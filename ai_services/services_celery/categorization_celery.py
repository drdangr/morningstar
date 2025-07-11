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
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
import requests
from .base_celery import BaseAIServiceCelery

logger = logging.getLogger(__name__)

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
    
    def process_with_bot_config(self, posts: List[Dict], bot_id: int) -> List[Dict[str, Any]]:
        """
        🚀 БАТЧЕВАЯ категоризация постов с настройками конкретного PublicBot
        
        Args:
            posts: Список постов для категоризации (dict format)
            bot_id: ID публичного бота
            
        Returns:
            Список результатов категоризации
        """
        try:
            # Конвертируем dict в Post objects если нужно
            post_objects = self._convert_to_post_objects(posts)
            
            # Получаем конфигурацию бота
            bot_config = self._get_bot_config(bot_id)
            if not bot_config:
                logger.error(f"Не удалось получить конфигурацию бота {bot_id}")
                return []
            
            # Получаем категории бота с описаниями
            bot_categories = self._get_bot_categories(bot_id)
            if not bot_categories:
                logger.error(f"Не удалось получить категории бота {bot_id}")
                return []
            
            logger.info(f"🤖 БАТЧЕВАЯ обработка {len(post_objects)} постов для бота '{bot_config['name']}'")
            logger.info(f"📂 Доступно {len(bot_categories)} категорий")
            logger.info(f"📦 Размер батча: {self.batch_size}")
            
            # Разбиваем посты на батчи
            batches = self._split_posts_into_batches(post_objects)
            logger.info(f"📊 Создано {len(batches)} батчей")
            
            # Обрабатываем батчи последовательно (не параллельно как в async версии)
            all_results = []
            for i, batch in enumerate(batches, 1):
                try:
                    logger.info(f"📝 Обработка батча {i}/{len(batches)} ({len(batch)} постов)")
                    batch_results = self._process_batch(batch, bot_config, bot_categories, i, len(batches))
                    all_results.extend(batch_results)
                    logger.info(f"✅ Батч {i} обработан: {len(batch_results)} результатов")
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки батча {i}: {e}")
                    # Создаем fallback результаты для постов этого батча
                    for post in batch:
                        fallback_result = self._create_fallback_result(post)
                        all_results.append(fallback_result)
            
            logger.info(f"✅ БАТЧЕВАЯ обработка завершена: {len(all_results)} результатов")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка в process_with_bot_config: {str(e)}")
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
                self.text = data.get('text', '')
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
    
    def _process_batch(self, batch_posts: List[Any], bot_config: Dict[str, Any], 
                      bot_categories: List[Dict[str, Any]], batch_index: int, total_batches: int) -> List[Dict[str, Any]]:
        """
        Обрабатывает один батч постов
        
        Args:
            batch_posts: Посты в батче
            bot_config: Конфигурация бота
            bot_categories: Категории бота
            batch_index: Номер текущего батча
            total_batches: Общее количество батчей
        """
        try:
            logger.info(f"🔄 Обработка батча {batch_index}/{total_batches} ({len(batch_posts)} постов)")
            
            # Строим батчевый промпт (как в N8N)
            system_prompt, user_message = self._build_batch_prompt(bot_config, bot_categories, batch_posts, batch_index, total_batches)
            
            # Вызываем OpenAI API для всего батча
            response = self._call_openai_batch_api(system_prompt, user_message)
            if not response:
                logger.error(f"❌ Нет ответа от OpenAI для батча {batch_index}")
                return [self._create_fallback_result(post) for post in batch_posts]
            
            # Парсим батчевый ответ
            batch_results = self._parse_batch_response(response, batch_posts, bot_categories)
            
            logger.info(f"✅ Батч {batch_index} обработан: {len(batch_results)} результатов")
            return batch_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки батча {batch_index}: {str(e)}")
            return [self._create_fallback_result(post) for post in batch_posts]
    
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
            post_text = post.text[:1000] if post.text else "Пост без текста"
            posts_text.append(f"Пост {post.id}: {post_text}")
        
        user_message = f"Батч {batch_index}/{total_batches} ({len(batch_posts)} постов):\n\n" + "\n\n".join(posts_text)
        
        return system_prompt, user_message
    
    def _call_openai_batch_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """
        Вызывает OpenAI API для батчевой обработки (синхронно)
        
        Args:
            system_prompt: Системный промпт
            user_message: Пользовательское сообщение
            
        Returns:
            Ответ от OpenAI или None при ошибке
        """
        try:
            # Получаем настройки из SettingsManager или используем дефолтные
            model, max_tokens, temperature = self._get_model_settings()
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=60
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Ошибка OpenAI API: {str(e)}")
            return None
    
    def _parse_batch_response(self, response: str, batch_posts: List[Any], bot_categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Парсит батчевый ответ от OpenAI
        
        Args:
            response: Ответ от OpenAI
            batch_posts: Посты в батче
            bot_categories: Категории бота
            
        Returns:
            Список результатов категоризации
        """
        results = []
        
        try:
            # Пытаемся распарсить JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                
                # Извлекаем результаты
                ai_results = parsed.get('results', [])
                
                # Валидируем и нормализуем каждый результат
                for ai_result in ai_results:
                    validated_result = self._validate_and_normalize_batch_result(ai_result, None, bot_categories)
                    if validated_result:
                        results.append(validated_result)
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга batch ответа: {str(e)}")
        
        # Если результатов меньше чем постов, создаем fallback
        while len(results) < len(batch_posts):
            post_index = len(results)
            if post_index < len(batch_posts):
                fallback_result = self._create_fallback_result(batch_posts[post_index])
                results.append(fallback_result)
            else:
                break
        
        return results
    
    def _validate_and_normalize_batch_result(self, ai_result: Dict[str, Any], post: Any, bot_categories: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Валидирует и нормализует результат AI категоризации
        
        Args:
            ai_result: Результат от AI
            post: Пост (может быть None)
            bot_categories: Категории бота
            
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
                'category_number': category_number,
                'category_name': category_name,
                'relevance_score': relevance_score,
                'importance': importance,
                'urgency': urgency,
                'significance': significance,
                'processing_status': 'completed'
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
    
    def _create_fallback_result(self, post: Any) -> Dict[str, Any]:
        """Создает fallback результат при ошибке AI"""
        return {
            'post_id': post.id if hasattr(post, 'id') else None,
            'category_number': None,
            'category_name': 'Не определено',
            'relevance_score': 0.5,
            'importance': 5,
            'urgency': 5,
            'significance': 5,
            'processing_status': 'failed'
        }
    
    def _get_model_settings(self) -> Tuple[str, int, float]:
        """Получает настройки модели из SettingsManager или использует дефолтные"""
        if self.settings_manager:
            try:
                config = self.settings_manager.get_ai_service_config('categorization')
                return (
                    config.get('model', 'gpt-4o-mini'),
                    config.get('max_tokens', 1000),
                    config.get('temperature', 0.3)
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