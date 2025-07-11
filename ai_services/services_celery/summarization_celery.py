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
from typing import Dict, List, Optional, Any
from openai import OpenAI
from .base_celery import BaseAIServiceCelery

logger = logging.getLogger(__name__)

class SummarizationServiceCelery(BaseAIServiceCelery):
    """
    Сервис для AI-саммаризации постов в Celery
    Поддерживает одиночный режим (рекомендуется) и батчевый режим
    """
    
    def __init__(self, model_name: str = "gpt-4", max_tokens: int = 4000, temperature: float = 0.3,
                 max_summary_length: int = 150, settings_manager=None):
        """
        Инициализация сервиса
        
        Args:
            model_name: Модель OpenAI для саммаризации
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            max_summary_length: Максимальная длина summary
            settings_manager: Менеджер настроек для динамических LLM
        """
        super().__init__(settings_manager)
        
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_summary_length = max_summary_length
        
        # Инициализируем OpenAI клиент (синхронный)
        api_key = self._get_openai_key()
        self.client = OpenAI(api_key=api_key)
        
        logger.info(f"📝 SummarizationServiceCelery инициализирован")
        logger.info(f"   Модель: {model_name}")
        logger.info(f"   Max tokens: {max_tokens}")
        logger.info(f"   Temperature: {temperature}")
        logger.info(f"   Max summary length: {max_summary_length}")
        if settings_manager:
            logger.info(f"   SettingsManager: подключен")
        else:
            logger.warning(f"   ⚠️ SettingsManager не подключен")
    
    def process(self, text: str, language: str = "ru", custom_prompt: Optional[str] = None, 
                max_summary_length: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """
        Создание краткого содержания одного текста
        
        Args:
            text: Текст для саммаризации
            language: Язык текста
            custom_prompt: Кастомный промпт
            max_summary_length: Максимальная длина summary
            **kwargs: Дополнительные параметры
            
        Returns:
            Результат саммаризации
        """
        try:
            # Проверяем валидность входных данных
            if not text or not text.strip():
                return {
                    "summary": "",
                    "status": "skipped",
                    "reason": "empty_text"
                }
            
            # Получаем настройки из SettingsManager или используем дефолтные
            model, max_tokens, temperature, top_p = self._get_model_settings()
            
            # Формируем промпт
            summary_length = max_summary_length or self.max_summary_length
            prompt = self._build_single_prompt(custom_prompt, language, summary_length)
            
            # Вызываем OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            # Извлекаем результат
            summary = response.choices[0].message.content.strip()
            
            return {
                "summary": summary,
                "language": language,
                "tokens_used": response.usage.total_tokens,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка в process: {e}")
            return {
                "summary": f"Ошибка обработки: {str(e)}",
                "status": "error",
                "error": str(e)
            }
    
    def process_batch(self, texts: List[str], language: str = "ru", custom_prompt: Optional[str] = None,
                     max_summary_length: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Батчевая обработка текстов одним запросом
        
        ВНИМАНИЕ: Батчевая саммаризация может давать некачественные результаты!
        Рекомендуется использовать одиночный режим или OpenAI Batch API
        
        Args:
            texts: Список текстов для саммаризации
            language: Язык текстов
            custom_prompt: Кастомный промпт
            max_summary_length: Максимальная длина summary
            **kwargs: Дополнительные параметры
            
        Returns:
            Список результатов саммаризации
        """
        
        if not texts:
            return []
        
        logger.info(f"🚀 Батчевая саммаризация {len(texts)} текстов")
        logger.warning(f"⚠️ Батчевая саммаризация может давать некачественные результаты!")
        
        try:
            # Получаем настройки
            model, max_tokens, temperature, top_p = self._get_model_settings()
            
            # Формируем батчевый промпт
            summary_length = max_summary_length or self.max_summary_length
            batch_prompt = self._build_batch_prompt(texts, custom_prompt, language, summary_length)
            
            # Отправляем запрос к OpenAI
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": batch_prompt}
                ],
                max_tokens=max_tokens * 2,  # Увеличиваем для батча
                temperature=temperature,
                top_p=top_p
            )
            
            # Парсим результат
            response_text = response.choices[0].message.content.strip()
            summaries = self._parse_batch_response(response_text, len(texts))
            
            # Формируем результаты
            total_tokens = response.usage.total_tokens
            tokens_per_text = total_tokens // len(texts) if texts else 0
            
            results = []
            for i, summary in enumerate(summaries):
                results.append({
                    "summary": summary,
                    "language": language,
                    "tokens_used": tokens_per_text,
                    "status": "success"
                })
            
            logger.info(f"✅ Батчевая саммаризация завершена: {len(results)} результатов")
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка батчевой саммаризации: {e}")
            
            # Возвращаем ошибки для всех текстов
            return [{
                "summary": f"Ошибка обработки текста {i+1}",
                "language": language,
                "tokens_used": 0,
                "status": "error",
                "error": str(e)
            } for i in range(len(texts))]
    
    def process_posts_individually(self, posts: List[Dict], language: str = "ru", 
                                  custom_prompt: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Обрабатывает посты по одному (рекомендуемый режим)
        
        Args:
            posts: Список постов для саммаризации
            language: Язык текстов
            custom_prompt: Кастомный промпт
            **kwargs: Дополнительные параметры
            
        Returns:
            Список результатов саммаризации
        """
        logger.info(f"📝 Индивидуальная саммаризация {len(posts)} постов")
        
        results = []
        for i, post in enumerate(posts, 1):
            try:
                # Извлекаем текст поста
                text = post.get('text', '')
                if not text or not text.strip():
                    results.append({
                        "post_id": post.get('id'),
                        "summary": "",
                        "status": "skipped",
                        "reason": "empty_text"
                    })
                    continue
                
                # Саммаризуем пост
                result = self.process(text, language, custom_prompt, **kwargs)
                
                # Добавляем ID поста к результату
                result['post_id'] = post.get('id')
                results.append(result)
                
                logger.info(f"✅ Пост {i}/{len(posts)} обработан")
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки поста {i}: {e}")
                results.append({
                    "post_id": post.get('id'),
                    "summary": f"Ошибка обработки: {str(e)}",
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"✅ Индивидуальная саммаризация завершена: {len(results)} результатов")
        return results
    
    def _get_model_settings(self) -> tuple:
        """Получает настройки модели из SettingsManager или использует дефолтные"""
        if self.settings_manager:
            try:
                config = self.settings_manager.get_ai_service_config('summarization')
                return (
                    config.get('model', self.model_name),
                    config.get('max_tokens', self.max_tokens),
                    config.get('temperature', self.temperature),
                    config.get('top_p', 1.0)
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки настроек: {e}")
        
        # Дефолтные значения
        return (
            self.model_name,
            self.max_tokens,
            self.temperature,
            1.0
        )
    
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