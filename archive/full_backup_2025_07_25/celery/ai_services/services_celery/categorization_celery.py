#!/usr/bin/env python3
"""
CategorizationServiceCelery - Celery-адаптированная версия AI категоризации
Скопировано из services/categorization.py и адаптировано для синхронной работы в Celery
"""

import json
import re
import time
import logging
import math
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
import requests
from .base_celery import BaseAIServiceCelery

logger = logging.getLogger(__name__)

# 🔧 КОНТРОЛЬ CONCURRENCY: Ограничиваем одновременные запросы к OpenAI
OPENAI_SEMAPHORE = asyncio.Semaphore(2)  # Максимум 2 одновременных запроса

class CategorizationServiceCelery(BaseAIServiceCelery):
    """
    Сервис для AI-категоризации постов в Celery
    Батчевая обработка с настройками из админ-панели
    """
    
    def __init__(self, openai_api_key: str = None, backend_url: str = "http://localhost:8000", 
                 batch_size: int = 30, settings_manager=None):
        """
        Инициализация сервиса
        
        Args:
            openai_api_key: API ключ OpenAI
            backend_url: URL Backend API
            batch_size: Размер батча для обработки
            settings_manager: Менеджер настроек для динамических LLM
        """
        super().__init__(settings_manager)
        
        self.openai_api_key = openai_api_key or self._get_openai_key()
        self.backend_url = backend_url
        self.batch_size = batch_size
        
        # Инициализируем OpenAI клиент (синхронный)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        logger.info(f"🏷️ CategorizationServiceCelery инициализирован")
        logger.info(f"   Backend URL: {backend_url}")
        logger.info(f"   Размер батча: {batch_size}")
        if settings_manager:
            logger.info(f"   SettingsManager: подключен")
        else:
            logger.warning(f"   ⚠️ SettingsManager не подключен")
    
    async def process_with_bot_config_async(self, posts: List[Dict], bot_id: int) -> List[Dict[str, Any]]:
        """
        🚀 АСИНХРОННАЯ БАТЧЕВАЯ категоризация постов с настройками конкретного PublicBot
        """
        try:
            post_objects = self._convert_to_post_objects(posts)
            
            bot_config = self._get_bot_config(bot_id)
            if not bot_config:
                logger.error(f"Не удалось получить конфигурацию бота {bot_id}")
                return []
            
            bot_categories = self._get_bot_categories(bot_id)
            if not bot_categories:
                logger.error(f"Не удалось получить категории бота {bot_id}")
                return []
            
            logger.info(f"🤖 АСИНХРОННАЯ БАТЧЕВАЯ обработка {len(post_objects)} постов для бота '{bot_config['name']}'")
            logger.info(f"📦 Размер батча: {self.batch_size}")
            
            batches = self._split_posts_into_batches(post_objects)
            logger.info(f"📊 Создано {len(batches)} батчей")
            
            all_results = []
            for i, batch in enumerate(batches, 1):
                try:
                    logger.info(f"📝 Асинхронная обработка батча {i}/{len(batches)} ({len(batch)} постов)")
                    batch_results = await self._process_batch_async(batch, bot_config, bot_categories, i, len(batches))
                    all_results.extend(batch_results)
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки async батча {i}: {e}")
                    for post in batch:
                        fallback_result = self._create_fallback_result(post, bot_id)
                        all_results.append(fallback_result)
            
            logger.info(f"✅ АСИНХРОННАЯ БАТЧЕВАЯ обработка завершена: {len(all_results)} результатов")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка в process_with_bot_config_async: {str(e)}")
            return []
    
    def _convert_to_post_objects(self, posts: List[Dict]) -> List[Any]:
        """Конвертирует dict в Post objects если нужно"""
        # Если уже Post objects, возвращаем как есть
        if posts and hasattr(posts[0], 'id'):
            return posts
        
        # Создаем простые объекты с нужными атрибутами
        class SimplePost:
            def __init__(self, data):
                self.id = data.get('id')
                # 🔧 ИСПРАВЛЕНИЕ: Backend API возвращает 'content', а не 'text'
                self.text = data.get('content', '') or data.get('text', '')  # Fallback на 'text' для совместимости
                self.media_path = data.get('media_path', '')
                self.views = data.get('views', 0)
                self.channel_telegram_id = data.get('channel_telegram_id', '')
                self.post_telegram_id = data.get('post_telegram_id', '')
                self.post_date = data.get('post_date', '')
                self.post_url = data.get('post_url', '')
        
        return [SimplePost(post) for post in posts]
    
    def _split_posts_into_batches(self, posts: List[Any]) -> List[List[Any]]:
        """Разбивает посты на батчи заданного размера"""
        batches = []
        for i in range(0, len(posts), self.batch_size):
            batch = posts[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    async def _process_batch_async(self, batch_posts: List[Any], bot_config: Dict[str, Any], 
                      bot_categories: List[Dict[str, Any]], batch_index: int, total_batches: int) -> List[Dict[str, Any]]:
        """
        Асинхронно обрабатывает один батч постов
        """
        try:
            logger.info(f"🔄 Асинхронная обработка батча {batch_index}/{total_batches} ({len(batch_posts)} постов)")
            
            system_prompt, user_message = self._build_batch_prompt(bot_config, bot_categories, batch_posts, batch_index, total_batches)
            
            response = await self._call_openai_batch_api_async(system_prompt, user_message)
            if not response:
                logger.error(f"❌ Нет ответа от OpenAI для батча {batch_index}")
                return [self._create_fallback_result(post, bot_config.get('id')) for post in batch_posts]
            
            batch_results = self._parse_batch_response(response, batch_posts, bot_categories, bot_config)
            
            logger.info(f"✅ Асинхронный батч {batch_index} обработан: {len(batch_results)} результатов")
            return batch_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка асинхронной обработки батча {batch_index}: {str(e)}")
            return [self._create_fallback_result(post, bot_config.get('id')) for post in batch_posts]
    
    def _build_batch_prompt(self, bot_config: Dict[str, Any], bot_categories: List[Dict[str, Any]], 
                           batch_posts: List[Any], batch_index: int, total_batches: int) -> Tuple[str, str]:
        """
        Строит батчевый промпт как в N8N workflows
        
        Returns:
            Tuple[system_prompt, user_message]
        """
        
        # 1. Bot Prompt из настроек
        bot_prompt = bot_config.get('categorization_prompt', 'Анализируй посты и определи релевантные категории.')
        
        # 2. Формируем список категорий с описаниями
        categories_list = []
        for i, category in enumerate(bot_categories, 1):
            name = category.get('category_name', category.get('name', 'Unknown'))
            description = category.get('description', 'Без описания')
            categories_list.append(f"{i}. {name} ({description})")
        
        categories_text = "\n".join(categories_list)
        
        # 3. Системный промпт (как в N8N)
        system_prompt = f"""{bot_prompt}

Доступные Категории для анализа:
{categories_text}

Проанализируй каждый пост и определи:
1. Номер релевантной категории из списка выше, если ни одна не подходит поставь null
2. Оценку релевантности для выбранной категории (0.0-1.0)
3. Важность новости (1-10) - насколько это важно для аудитории
4. Срочность (1-10) - насколько быстро нужно об этом узнать
5. Значимость (1-10) - долгосрочное влияние события

Отвечай ТОЛЬКО валидным JSON массивом:
{{
  "results": [
    {{
      "id": post_id,
      "category_number": 1,
      "category_name": "название категории",
      "relevance_score": 0.95,
      "importance": 8,
      "urgency": 7,
      "significance": 9
    }}
  ]
}}"""
        
        # 4. Пользовательское сообщение с постами
        posts_text = []
        for i, post in enumerate(batch_posts, 1):
            post_text_raw = post.text[:1000] if post.text else "Пост без текста"
            # 🐞 FIX: Экранируем спецсимволы, которые могут сломать JSON в ответе OpenAI
            post_text_safe = post_text_raw.replace('\\', '\\\\').replace('"', "'")
            posts_text.append(f"Пост {post.id}: {post_text_safe}")
        
        user_message = f"Батч {batch_index}/{total_batches} ({len(batch_posts)} постов):\n\n" + "\n\n".join(posts_text)
        
        return system_prompt, user_message
    
    async def _call_openai_batch_api_async(self, system_prompt: str, user_message: str) -> Optional[str]:
        """
        Асинхронно вызывает OpenAI API для батчевой обработки с контролем concurrency
        """
        async with OPENAI_SEMAPHORE:  # 🔧 ОГРАНИЧИВАЕМ CONCURRENCY
            try:
                logger.info(f"🔒 Получили слот для OpenAI запроса (активных запросов: {2 - OPENAI_SEMAPHORE._value})")
                
                model, max_tokens, temperature = await self._get_model_settings_async()
                
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
                        timeout=60
                    )
                finally:
                    # Явно закрываем HTTP клиент чтобы избежать RuntimeError
                    await client.close()
                
                logger.info(f"✅ OpenAI запрос завершен, освобождаем слот")
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                logger.error(f"❌ Ошибка Async OpenAI API: {str(e)}")
                return None
    
    def _extract_json_objects(self, text: str) -> List[str]:
        """
        Корректно извлекает JSON объекты из текста, учитывая вложенные скобки
        Исправляет проблему с регулярным выражением \{.*?\} которое обрезало JSON
        """
        json_objects = []
        brace_count = 0
        start_pos = None
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_pos = i  # Начало JSON объекта
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_pos is not None:
                    # Конец JSON объекта - извлекаем полный объект
                    json_str = text[start_pos:i+1]
                    json_objects.append(json_str)
                    start_pos = None
        
        logger.info(f"📋 DEBUG: Извлечено {len(json_objects)} JSON объектов правильным парсером")
        return json_objects
    
    def _parse_batch_response(self, response: str, batch_posts: List[Any], 
                             bot_categories: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсит батчевый ответ от OpenAI
        
        Args:
            response: Ответ от OpenAI
            batch_posts: Посты в батче
            bot_categories: Категории бота
            bot_config: Конфигурация бота
            
        Returns:
            Список результатов категоризации
        """
        results = []
        
        try:
            # 🔍 ОТЛАДКА: Логируем сырой ответ OpenAI
            logger.info(f"🤖 DEBUG: OpenAI ответ (первые 500 символов): {response[:500]}")
            logger.info(f"🤖 DEBUG: Длина ответа: {len(response)} символов")
            
            # 🔧 ИСПРАВЛЕНИЕ: Убираем markdown обертки ```json и ```
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Убираем ```json
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]  # Убираем ```
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Убираем завершающие ```
            clean_response = clean_response.strip()
            
            logger.info(f"🧹 DEBUG: Очищенный ответ (первые 300 символов): {clean_response[:300]}")
            
            # 🔧 ИСПРАВЛЕННЫЙ ПАРСЕР: корректно парсим вложенные JSON
            # Старая регулярка \{.*?\} неправильно обрезала вложенные объекты
            json_objects = self._extract_json_objects(clean_response)
            logger.info(f"🔍 DEBUG: Найдено JSON объектов: {len(json_objects)}")
            
            # Сопоставляем посты по ID для удобства
            post_map = {post.id: post for post in batch_posts}
            
            for json_str in json_objects:
                try:
                    parsed = json.loads(json_str)
                    
                    # Проверяем, есть ли это результат для одного поста
                    if 'id' in parsed and 'category_name' in parsed:
                        validated_result = self._validate_and_normalize_batch_result(parsed, post_map.get(parsed['id']), bot_categories, bot_config)
                        if validated_result:
                            results.append(validated_result)
                            # Удаляем пост из карты, чтобы избежать дублирования
                            if parsed['id'] in post_map:
                                del post_map[parsed['id']]
                    
                    # Проверяем, есть ли это обертка с ключом 'results'
                    elif 'results' in parsed and isinstance(parsed['results'], list):
                        for ai_result in parsed['results']:
                            if 'id' in ai_result:
                                validated_result = self._validate_and_normalize_batch_result(ai_result, post_map.get(ai_result['id']), bot_categories, bot_config)
                                if validated_result:
                                    results.append(validated_result)
                                    # Удаляем пост из карты
                                    if ai_result['id'] in post_map:
                                        del post_map[ai_result['id']]

                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Не удалось распарсить JSON-фрагмент: {json_str[:100]}...")
                    continue # Переходим к следующему фрагменту

        except Exception as e:
            logger.error(f"❌ Критическая ошибка парсинга batch ответа: {str(e)}")
        
        # Для всех постов, которые НЕ получили результат, создаем fallback
        if post_map: # Если в карте остались посты
            logger.warning(f"⚠️ Для {len(post_map)} постов не найдено результатов в ответе AI, создаем fallback.")
            for post_id, post in post_map.items():
                bot_id = bot_config.get('id')
                fallback_result = self._create_fallback_result(post, bot_id)
                results.append(fallback_result)
        
        return results
    
    def _validate_and_normalize_batch_result(self, ai_result: Dict[str, Any], post: Any, 
                                            bot_categories: List[Dict[str, Any]], bot_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Валидирует и нормализует результат AI категоризации
        
        Args:
            ai_result: Результат от AI
            post: Пост (может быть None)
            bot_categories: Категории бота
            bot_config: Конфигурация бота
            
        Returns:
            Нормализованный результат или None при ошибке
        """
        try:
            # Извлекаем данные с fallback значениями
            post_id = ai_result.get('id')
            category_number = ai_result.get('category_number')
            category_name = ai_result.get('category_name', '')
            relevance_score = self._validate_score(ai_result.get('relevance_score', 0.5), 0.0, 1.0)
            importance = self._validate_score(ai_result.get('importance', 5), 1, 10)
            urgency = self._validate_score(ai_result.get('urgency', 5), 1, 10)
            significance = self._validate_score(ai_result.get('significance', 5), 1, 10)
            
            # Валидируем номер категории
            if category_number is not None:
                category_number = self._validate_category_number(category_number, len(bot_categories))
                if category_number is not None:
                    # Получаем имя категории из списка
                    category_index = category_number - 1
                    if 0 <= category_index < len(bot_categories):
                        category_name = bot_categories[category_index].get('category_name', 
                                                                        bot_categories[category_index].get('name', 'Unknown'))
            
            # Формируем результат
            result = {
                'post_id': post_id,
                'public_bot_id': bot_config.get('id') if bot_config else None,
                'service_name': 'categorization',
                'status': 'success',
                'payload': {
                    'primary': category_name,
                    'secondary': [],
                    'relevance_scores': [relevance_score]
                },
                'metrics': {
                    'importance': importance,
                    'urgency': urgency,
                    'significance': significance
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации результата: {str(e)}")
            return None
    
    def _get_bot_config(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Получает конфигурацию бота из Backend API"""
        try:
            response = requests.get(f"{self.backend_url}/api/public-bots/{bot_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка получения конфигурации бота {bot_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса конфигурации бота {bot_id}: {str(e)}")
            return None
    
    def _get_bot_categories(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получает категории бота из Backend API"""
        try:
            response = requests.get(f"{self.backend_url}/api/public-bots/{bot_id}/categories")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка получения категорий бота {bot_id}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса категорий бота {bot_id}: {str(e)}")
            return []
    
    def _validate_category_number(self, category_number: Any, max_categories: int) -> Optional[int]:
        """Валидирует номер категории"""
        try:
            if category_number is None:
                return None
            
            num = int(category_number)
            if 1 <= num <= max_categories:
                return num
            else:
                logger.warning(f"⚠️ Номер категории {num} вне диапазона 1-{max_categories}")
                return None
        except (ValueError, TypeError):
            logger.warning(f"⚠️ Неверный формат номера категории: {category_number}")
            return None
    
    def _validate_score(self, score: Any, min_val: float, max_val: float) -> float:
        """Валидирует оценку в заданном диапазоне"""
        try:
            val = float(score)
            return max(min_val, min(val, max_val))
        except (ValueError, TypeError):
            return (min_val + max_val) / 2  # Средняя оценка по умолчанию
    
    def _create_fallback_result(self, post: Any, bot_id: int) -> Dict[str, Any]:
        """Создает fallback результат при ошибке AI"""
        return {
            'post_id': post.id if hasattr(post, 'id') else None,
            'public_bot_id': bot_id,
            'service_name': 'categorization',
            'status': 'success',
            'payload': {'error': 'AI processing failed'},
            'metrics': {}
        }
    
    async def _get_model_settings_async(self) -> Tuple[str, int, float]:
        """Асинхронно получает настройки модели из SettingsManager"""
        if self.settings_manager:
            try:
                config = await self.settings_manager.get_ai_service_config('categorization')
                return (
                    config.get('model', 'gpt-4o-mini'),
                    int(config.get('max_tokens', 1000)),
                    float(config.get('temperature', 0.3))
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка загрузки настроек: {e}")
        
        # Дефолтные значения
        return ('gpt-4o-mini', 1000, 0.3)
    
    def _get_openai_key(self) -> str:
        """Получает OpenAI API ключ из переменных окружения"""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required") 