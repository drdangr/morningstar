#!/usr/bin/env python3
"""
SummarizationServiceCelery - Celery-адаптированная версия AI саммаризации
Скопировано из services/summarization.py и адаптировано для синхронной работы в Celery
Учитывает проблемы с батчевой саммаризацией - поддерживает одиночный и батчевый режимы
"""

import json
import re
import time
import logging
import os
import asyncio
from typing import Dict, List, Optional, Any
from openai import OpenAI
from .base_celery import BaseAIServiceCelery

# ✨ НОВОЕ: Импорт единой схемы данных
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from schemas import PostForSummarization, ProcessingStatus, ServiceResult

logger = logging.getLogger(__name__)

# 🔧 КОНТРОЛЬ CONCURRENCY: Ограничиваем одновременные запросы к OpenAI  
OPENAI_SEMAPHORE = asyncio.Semaphore(2)  # Максимум 2 одновременных запроса


class SummarizationServiceCelery(BaseAIServiceCelery):
    """
    Сервис для AI-саммаризации постов в Celery
    Поддерживает одиночный режим (рекомендуется) и батчевый режим
    """
    
    def __init__(self, settings_manager=None):
        """
        Инициализация сервиса
        
        Args:
            settings_manager: Менеджер настроек для динамических LLM
        """
        super().__init__(settings_manager)
        
        # OpenAI ключ и клиент инициализируются лениво
        self.openai_api_key = None
        self.async_client = None
        
        # 🔧 ИСПРАВЛЕНИЕ: Добавляем отсутствующий атрибут max_summary_length
        self.max_summary_length = 150  # Дефолтное значение для длины саммари
        
        logger.info(f"📝 SummarizationServiceCelery инициализирован")
        if settings_manager:
            logger.info(f"   Настройки будут получены динамически через SettingsManager")
        else:
            logger.warning(f"   ⚠️ SettingsManager не подключен. Будут использованы стандартные настройки.")
    
    async def process_async(self, text: str, language: str = "ru", custom_prompt: Optional[str] = None, 
                max_summary_length: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Асинхронно создает краткое содержание одного текста
        """
        try:
            if not text or not text.strip():
                return { "summary": "", "status": "skipped", "reason": "empty_text" }
            
            model, max_tokens, temperature, top_p, settings_max_length = await self._get_model_settings_async()
            summary_length = max_summary_length or settings_max_length or self.max_summary_length
            prompt = self._build_single_prompt(custom_prompt, language, summary_length)

            # Обеспечиваем наличие ключа OpenAI
            await self._ensure_openai_key()
            if not self.openai_api_key:
                return { "summary": "ошибка саммаризации", "status": "error", "error": "missing_openai_api_key" }

            # Реальный вызов OpenAI
            response_text = await self._call_openai_api_async(system_prompt=prompt, user_message=text)
            if not response_text:
                return { "summary": "ошибка саммаризации", "status": "error", "error": "openai_api_failed" }

            return {
                "summary": response_text,
                "language": language,
                "tokens_used": 0,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка в process_async: {e}")
            return { "summary": f"Ошибка обработки: {str(e)}", "status": "error", "error": str(e) }

    async def process_posts_individually_async(self, posts: List[Dict], bot_id: int, language: str = "ru", 
                                  custom_prompt: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        ✨ ОБНОВЛЕНО: Асинхронно обрабатывает посты по одному используя unified схему
        """
        logger.info(f"📝 Асинхронная индивидуальная саммаризация {len(posts)} постов")
        
        # 🔧 ИСПРАВЛЕНИЕ: Получаем настройки бота включая кастомный промпт и длину саммари
        bot_custom_prompt, bot_max_length = await self._get_bot_summarization_settings(bot_id)
        # Получаем системные настройки для определения системной длины
        _, _, _, _, settings_max_length = await self._get_model_settings_async()
        if bot_custom_prompt:
            logger.info(f"🎯 Используем кастомный промпт бота {bot_id} (длина: {len(bot_custom_prompt)})")
            custom_prompt = bot_custom_prompt
        else:
            logger.info(f"📄 Кастомный промпт для бота {bot_id} не найден, используем дефолтный")
        
        # Определяем максимальную длину саммари (приоритет: настройки бота → системные настройки → fallback)
        final_max_length = bot_max_length or settings_max_length or self.max_summary_length
        if bot_max_length:
            logger.info(f"📏 Используем кастомную длину саммари бота {bot_id}: {final_max_length}")
        else:
            logger.info(f"📏 Используем дефолтную длину саммари: {final_max_length}")
        
        # Конвертируем посты в PostForSummarization objects
        post_objects = self._convert_to_post_objects(posts, bot_id)
        
        results = []
        for i, post in enumerate(post_objects, 1):
            try:
                # Используем unified schema - PostForSummarization
                text = post.content or ''
                if not text or not text.strip():
                    results.append({
                        "post_id": post.id,  # Используем атрибут объекта
                        "public_bot_id": bot_id,
                        "service_name": "summarization",
                        "status": ProcessingStatus.COMPLETED.value,  # Используем enum
                        "payload": {"summary": "", "reason": "empty_text"},
                        "metrics": {}
                    })
                    continue
                
                # Передаем post_id, bot_id и кастомную длину саммари для реальной обработки
                result = await self.process_async(text, language, custom_prompt, 
                                                max_summary_length=final_max_length,
                                                post_id=post.id, bot_id=bot_id, **kwargs)
                
                result['post_id'] = post.id  # Используем атрибут объекта
                result['public_bot_id'] = bot_id
                result['service_name'] = 'summarization'

                # ✨ ОБНОВЛЕНО: Используем enum статусы
                status = ProcessingStatus.COMPLETED.value if result.get('status') == 'success' else ProcessingStatus.FAILED.value
                
                final_result = {
                    'post_id': result.get('post_id'),
                    'public_bot_id': result.get('public_bot_id'),
                    'service_name': 'summarization',
                    'status': status,  # Используем enum статус
                    'payload': { 'summary': result.get('summary'), 'language': result.get('language') },
                    'metrics': { 'tokens_used': result.get('tokens_used', 0) }
                }
                if result.get('status') == 'error':
                    final_result['payload']['error'] = result.get('error')

                results.append(final_result)
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки поста {i}: {e}")
                results.append({
                    "post_id": post.id,  # Используем атрибут объекта
                    "public_bot_id": bot_id,
                    "service_name": "summarization",
                    'status': ProcessingStatus.FAILED.value,  # Используем enum для ошибки
                    'payload': {'error': str(e)},
                    'metrics': {}
                })
        
        logger.info(f"✅ Асинхронная индивидуальная саммаризация завершена: {len(results)} результатов")
        return results
    
    def _convert_to_post_objects(self, posts: List[Dict], bot_id: int) -> List[PostForSummarization]:
        """
        ✨ НОВОЕ: Конвертирует dict в PostForSummarization objects используя unified схему
        """
        # Если уже PostForSummarization objects, возвращаем как есть
        if posts and isinstance(posts[0], PostForSummarization):
            return posts
        
        # Создаем PostForSummarization объекты через unified схему
        result_posts = []
        for post_data in posts:
            try:
                # Создаем PostForSummarization согласно schemas.py
                post_obj = PostForSummarization(
                    id=post_data.get('id'),
                    public_bot_id=bot_id,
                    channel_telegram_id=post_data.get('channel_telegram_id', 0),
                    telegram_message_id=post_data.get('telegram_message_id', 0),
                    title=post_data.get('title'),
                    content=post_data.get('content') or post_data.get('text', ''),  # Поддержка legacy поля 'text'
                    media_urls=post_data.get('media_urls', []),
                    views=post_data.get('views', 0),
                    post_date=post_data.get('post_date'),
                    userbot_metadata=post_data.get('userbot_metadata', {}),
                    categories=post_data.get('categories', [])  # Результат категоризации если есть
                )
                result_posts.append(post_obj)
                
            except Exception as e:
                logger.error(f"❌ Ошибка создания PostForSummarization для поста {post_data.get('id', 'unknown')}: {e}")
                # Пропускаем проблематичные посты
                continue
        
        logger.info(f"✅ Конвертировано {len(result_posts)} постов в PostForSummarization")
        return result_posts

    async def _ensure_openai_key(self) -> None:
        """Гарантирует наличие OpenAI API ключа в self.openai_api_key."""
        if self.openai_api_key:
            return
        try:
            if self.settings_manager is not None:
                key = await self.settings_manager.get_openai_key()
                self.openai_api_key = key
                return
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить OpenAI ключ через SettingsManager: {e}")
        # Fallback: переменная окружения
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
    
    async def _call_openai_api_async(self, system_prompt: str, user_message: str) -> Optional[str]:
        """
        Асинхронно вызывает OpenAI API для индивидуальной обработки
        """
        try:
            model, max_tokens, temperature, top_p, settings_max_length = await self._get_model_settings_async()

            # 🐞 ИСПРАВЛЕНО: Создаем клиент и явно закрываем его
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p
                )
            finally:
                # Явно закрываем HTTP клиент чтобы избежать RuntimeError
                await client.close()
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"❌ Ошибка Async OpenAI API: {str(e)}")
            return None
        
    async def _get_model_settings_async(self) -> tuple:
        """Асинхронно получает настройки модели из SettingsManager"""
        # 🐞 FIX: Определяем безопасные значения по умолчанию прямо здесь
        defaults = {
            'model': 'gpt-4o-mini',
            'max_tokens': 2000,
            'temperature': 0.7,
            'top_p': 1.0,
            'max_summary_length': 150
        }

        if self.settings_manager:
            try:
                config = await self.settings_manager.get_ai_service_config('summarization')
                
                # 🔍 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ НАСТРОЕК
                model = config.get('model', defaults['model'])
                max_tokens = int(config.get('max_tokens', defaults['max_tokens']))
                temperature = float(config.get('temperature', defaults['temperature']))
                top_p = float(config.get('top_p', defaults['top_p']))
                max_summary_length = int(config.get('max_summary_length', defaults['max_summary_length']))
                
                logger.info(f"📋 СИСТЕМНЫЕ настройки саммаризации из SettingsManager (могут быть переопределены настройками бота):")
                logger.info(f"   🤖 Модель: {model} (ожидалось: gpt-4o)")
                logger.info(f"   🎯 Max tokens: {max_tokens} (ожидалось: 2000)")
                logger.info(f"   🌡️ Temperature: {temperature} (ожидалось: 0.7)")
                logger.info(f"   🎲 Top_p: {top_p} (ожидалось: 1.0)")
                logger.info(f"   📏 Max summary length: {max_summary_length} (СИСТЕМНАЯ, fallback: 150)")
                
                return (model, max_tokens, temperature, top_p, max_summary_length)
                
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки настроек: {e}")
                logger.info(f"📋 Используются дефолтные настройки саммаризации:")
                logger.info(f"   🤖 Модель: {defaults['model']}")
                logger.info(f"   🎯 Max tokens: {defaults['max_tokens']}")
                logger.info(f"   🌡️ Temperature: {defaults['temperature']}")
                logger.info(f"   🎲 Top_p: {defaults['top_p']}")
                logger.info(f"   📏 Max summary length: {defaults['max_summary_length']}")
        else:
            logger.info(f"📋 SettingsManager отсутствует, используются дефолтные настройки:")
            logger.info(f"   🤖 Модель: {defaults['model']}")
            logger.info(f"   🎯 Max tokens: {defaults['max_tokens']}")
            logger.info(f"   🌡️ Temperature: {defaults['temperature']}")
            logger.info(f"   🎲 Top_p: {defaults['top_p']}")
            logger.info(f"   📏 Max summary length: {defaults['max_summary_length']}")
        
        return (defaults['model'], defaults['max_tokens'], defaults['temperature'], defaults['top_p'], defaults['max_summary_length'])
    
    def _build_single_prompt(self, custom_prompt: Optional[str], language: str, max_length: int) -> str:
        """Строит промпт для одиночной саммаризации"""
        # Базовый промпт или кастомный
        base_prompt = custom_prompt or self._get_default_prompt(language)
        
        # Добавляем ограничение по длине
        if max_length:
            length_instruction = f"\n\nЛимит длины: постарайся уложиться примерно в {max_length} символов, но не жертвуй важными частями ради этого. Лучше слегка превысить лимит, чем потерять суть или вкус текста."
            return f"{base_prompt}{length_instruction}"
        
        return base_prompt
    
    def _build_batch_prompt(self, texts: List[str], custom_prompt: Optional[str], language: str, max_length: int) -> str:
        """Строит промпт для батчевой обработки"""
        # Начинаем с инструкции о формате
        prompt = f"""Обработай следующие {len(texts)} текстов СТРОГО ПРИДЕРЖИВАЯСЬ ДЛЯ КАЖДОГО ИЗ ТЕКСТОВ ИНСТРУКЦИИ НИЖЕ и верни результат в формате JSON массива.
Каждый элемент должен содержать поле "summary".

Формат ответа:
[
  {{"summary": "результат обработки текста 1"}},
  {{"summary": "результат обработки текста 2"}},
  ...
]

ИНСТРУКЦИЯ ДЛЯ КАЖДОГО ТЕКСТА:
{custom_prompt or self._get_default_prompt(language)}

Лимит длины summary: примерно {max_length} символов для каждого.

ТЕКСТЫ ДЛЯ ОБРАБОТКИ:
"""
        
        # Добавляем тексты с номерами
        for i, text in enumerate(texts, 1):
            prompt += f"\n\n=== ТЕКСТ {i} ===\n{text}"
        
        return prompt
    
    def _parse_batch_response(self, response_text: str, expected_count: int) -> List[str]:
        """Парсит батчевый ответ от OpenAI"""
        summaries = []
        
        try:
            # Пытаемся найти JSON в ответе
            json_text = self._extract_json(response_text)
            if json_text:
                # Парсим JSON
                parsed = json.loads(json_text)
                
                # Извлекаем summary из каждого элемента
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict) and 'summary' in item:
                            summaries.append(item['summary'])
                        elif isinstance(item, str):
                            summaries.append(item)
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга батчевого ответа: {e}")
        
        # Дополняем недостающие summary
        while len(summaries) < expected_count:
            summaries.append(f"Не удалось обработать текст {len(summaries) + 1}")
        
        # Обрезаем лишние
        return summaries[:expected_count]
    
    def _extract_json(self, text: str) -> str:
        """Извлекает JSON из текста"""
        try:
            # Ищем массив JSON
            start = text.find('[')
            if start == -1:
                return ""
            
            # Находим соответствующую закрывающую скобку
            bracket_count = 0
            for i in range(start, len(text)):
                if text[i] == '[':
                    bracket_count += 1
                elif text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        return text[start:i+1]
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения JSON: {e}")
            return ""
    
    def _get_default_prompt(self, language: str) -> str:
        """Возвращает дефолтный промпт для саммаризации"""
        if language == "ru":
            return """Создай краткое содержание текста, сохранив основную идею и ключевые детали.
Требования:
- Пиши кратко, но информативно
- Сохраняй главную мысль и важные факты
- Используй простой и понятный язык
- Не добавляй собственные комментарии или оценки
- Если в тексте есть конкретные цифры, даты или имена - обязательно включай их"""
        else:
            return """Create a concise summary of the text, preserving the main idea and key details.
Requirements:
- Write concisely but informatively
- Preserve the main idea and important facts
- Use simple and clear language
- Don't add your own comments or evaluations
- If the text contains specific numbers, dates, or names - be sure to include them"""
    
    def _get_openai_key(self) -> str:
        """Получает OpenAI API ключ из переменных окружения"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required") 
        return api_key

    async def _get_bot_summarization_settings(self, bot_id: int) -> tuple[Optional[str], Optional[int]]:
        """
        Получает кастомные настройки саммаризации для конкретного бота
        
        Args:
            bot_id: ID публичного бота
            
        Returns:
            Кортеж (кастомный_промпт, макс_длина_саммари) или (None, None) если не найдены
        """
        try:
            import httpx
            
            # Получаем настройки бота через Backend API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"http://morningstar_backend:8000/api/public-bots/{bot_id}")
                if response.status_code == 200:
                    bot_data = response.json()
                    
                    # Получаем кастомный промпт
                    summarization_prompt = bot_data.get("summarization_prompt")
                    custom_prompt = summarization_prompt.strip() if summarization_prompt and summarization_prompt.strip() else None
                    
                    # Получаем максимальную длину саммари
                    max_summary_length = bot_data.get("max_summary_length")
                    custom_max_length = int(max_summary_length) if max_summary_length and str(max_summary_length).isdigit() else None
                    
                    if custom_prompt:
                        logger.info(f"✅ Получен кастомный промпт саммаризации для бота {bot_id}")
                    else:
                        logger.info(f"📄 У бота {bot_id} нет кастомного промпта саммаризации")
                    
                    if custom_max_length:
                        logger.info(f"✅ Получена кастомная длина саммари для бота {bot_id}: {custom_max_length}")
                    else:
                        logger.info(f"📏 У бота {bot_id} нет кастомной длины саммари")
                    
                    return (custom_prompt, custom_max_length)
                else:
                    logger.warning(f"❌ Не удалось получить настройки бота {bot_id}: HTTP {response.status_code}")
                    return (None, None)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения настроек бота {bot_id}: {e}")
            return (None, None) 