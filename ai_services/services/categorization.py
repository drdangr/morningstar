#!/usr/bin/env python3
"""
CategorizationService v3.0 - БАТЧЕВАЯ AI-категоризация постов
Революционная версия с батчевой обработкой как в N8N для максимальной производительности
"""

import asyncio
import aiohttp
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from openai import AsyncOpenAI
from models.post import Post
import math

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategorizationService:
    """
    Сервис для AI-категоризации постов с поддержкой настроек PublicBot
    v3.0 - БАТЧЕВАЯ обработка как в N8N для максимальной производительности
    """
    
    def __init__(self, openai_api_key: str, backend_url: str = "http://localhost:8000", batch_size: int = 30):
        """
        Инициализация сервиса
        
        Args:
            openai_api_key: API ключ OpenAI
            backend_url: URL Backend API
            batch_size: Размер батча для обработки (по умолчанию как в N8N)
        """
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.backend_url = backend_url
        self.batch_size = batch_size
        
    async def process_with_bot_config(self, posts: List[Post], bot_id: int) -> List[Dict[str, Any]]:
        """
        🚀 БАТЧЕВАЯ категоризация постов с настройками конкретного PublicBot
        
        Args:
            posts: Список постов для категоризации
            bot_id: ID публичного бота
            
        Returns:
            Список результатов категоризации
        """
        try:
            # Получаем конфигурацию бота
            bot_config = await self._get_bot_config(bot_id)
            if not bot_config:
                logger.error(f"Не удалось получить конфигурацию бота {bot_id}")
                return []
            
            # Получаем категории бота с описаниями
            bot_categories = await self._get_bot_categories(bot_id)
            if not bot_categories:
                logger.error(f"Не удалось получить категории бота {bot_id}")
                return []
            
            logger.info(f"🤖 БАТЧЕВАЯ обработка {len(posts)} постов для бота '{bot_config['name']}'")
            logger.info(f"📂 Доступно {len(bot_categories)} категорий")
            logger.info(f"📦 Размер батча: {self.batch_size}")
            
            # Разбиваем посты на батчи
            batches = self._split_posts_into_batches(posts)
            logger.info(f"📊 Создано {len(batches)} батчей")
            
            # 🚀 ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА БАТЧЕЙ
            batch_tasks = []
            for i, batch in enumerate(batches, 1):
                logger.info(f"📝 Создаем задачу для батча {i}/{len(batches)} ({len(batch)} постов)")
                task = self._process_batch(batch, bot_config, bot_categories, i, len(batches))
                batch_tasks.append(task)
            
            # Выполняем все батчи параллельно
            logger.info(f"🚀 Параллельная обработка {len(batch_tasks)} батчей")
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Собираем результаты всех батчей
            all_results = []
            for i, batch_result in enumerate(batch_results, 1):
                if isinstance(batch_result, Exception):
                    logger.error(f"❌ Ошибка обработки батча {i}: {batch_result}")
                    # Создаем fallback результаты для постов этого батча
                    batch_posts = batches[i-1]
                    for post in batch_posts:
                        fallback_result = self._create_fallback_result(post)
                        all_results.append(fallback_result)
                else:
                    all_results.extend(batch_result)
                    logger.info(f"✅ Батч {i} обработан: {len(batch_result)} результатов")
            
            logger.info(f"✅ БАТЧЕВАЯ обработка завершена: {len(all_results)} результатов")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка в process_with_bot_config: {str(e)}")
            return []
    
    def _split_posts_into_batches(self, posts: List[Post]) -> List[List[Post]]:
        """Разбивает посты на батчи заданного размера"""
        batches = []
        for i in range(0, len(posts), self.batch_size):
            batch = posts[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    async def _process_batch(self, batch_posts: List[Post], bot_config: Dict[str, Any], 
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
            response = await self._call_openai_batch_api(system_prompt, user_message)
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
                           batch_posts: List[Post], batch_index: int, total_batches: int) -> Tuple[str, str]:
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
      "importance": 9,
      "urgency": 8,
      "significance": 9,
      "reasoning": "краткое обоснование выбора категории и оценок"
    }}
  ]
}}

ВАЖНО: Если категория не подходит, используй null (строчными буквами), не NULL!"""
        
        # 4. Подготавливаем посты для анализа (как в N8N)
        posts_for_ai = []
        for post in batch_posts:
            posts_for_ai.append({
                "id": post.id,
                "text": post.content,
                "channel": getattr(post, 'channel_title', 'Unknown'),
                "views": getattr(post, 'views', 0),
                "date": post.date.isoformat() if hasattr(post, 'date') and post.date else None
            })
        
        # 5. Пользовательское сообщение (как в N8N)
        user_message = f"Проанализируй эти {len(batch_posts)} постов (батч {batch_index}/{total_batches}):\n\n{json.dumps(posts_for_ai, ensure_ascii=False, indent=2)}"
        
        return system_prompt, user_message
    
    async def _call_openai_batch_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Вызов OpenAI API для батча постов"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=6000,  # Увеличенный лимит для батча как в N8N
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка вызова OpenAI API для батча: {str(e)}")
            return None
    
    def _parse_batch_response(self, response: str, batch_posts: List[Post], bot_categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Парсит батчевый ответ от OpenAI"""
        try:
            # Извлекаем JSON из ответа
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("JSON не найден в батчевом ответе AI")
                return [self._create_fallback_result(post) for post in batch_posts]
            
            # Исправляем проблему с NULL -> null
            json_text = json_match.group()
            json_text = re.sub(r'\bNULL\b', 'null', json_text)
            
            # Парсим JSON
            try:
                parsed_response = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Ошибка парсинга батчевого JSON: {str(e)}")
                return [self._create_fallback_result(post) for post in batch_posts]
            
            # Извлекаем массив результатов
            ai_results = parsed_response.get('results', [])
            if not isinstance(ai_results, list):
                logger.warning("Результаты AI не являются массивом")
                return [self._create_fallback_result(post) for post in batch_posts]
            
            # Сопоставляем результаты с постами
            results = []
            post_id_to_post = {post.id: post for post in batch_posts}
            
            for ai_result in ai_results:
                post_id = ai_result.get('id')
                if post_id in post_id_to_post:
                    post = post_id_to_post[post_id]
                    
                    # Валидируем и нормализуем результат (включая нерелевантные)
                    normalized_result = self._validate_and_normalize_batch_result(ai_result, post, bot_categories)
                    if normalized_result:
                        results.append(normalized_result)
                else:
                    logger.warning(f"Пост с ID {post_id} не найден в батче")
            
            # НЕ создаем fallback результаты для нерелевантных постов
            # Если пост не получил категорию - значит он нерелевантен, это нормально
            logger.info(f"✅ Батчевая обработка: {len(results)} релевантных постов из {len(batch_posts)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка парсинга батчевого ответа: {str(e)}")
            return [self._create_fallback_result(post) for post in batch_posts]
    
    def _validate_and_normalize_batch_result(self, ai_result: Dict[str, Any], post: Post, bot_categories: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Валидация и нормализация одного результата из батча"""
        try:
            # Проверяем категорию - null означает нерелевантный пост
            category_number = ai_result.get('category_number')
            
            if category_number is None or category_number == 'null':
                # Создаем результат для НЕРЕЛЕВАНТНОГО поста
                logger.info(f"📝 Пост {post.id} нерелевантен - создаем результат 'Нерелевантно'")
                return {
                    'post_id': post.id,
                    'post_text': post.content[:200] + '...' if len(post.content or '') > 200 else post.content,
                    'category_number': None,
                    'category_name': 'Нерелевантно',
                    'relevance_score': 0.0,
                    'importance': self._validate_score(ai_result.get('importance'), 1, 10),
                    'urgency': self._validate_score(ai_result.get('urgency'), 1, 10),
                    'significance': self._validate_score(ai_result.get('significance'), 1, 10),
                    'reasoning': str(ai_result.get('reasoning', 'Пост не относится ни к одной из категорий бота'))[:500],
                    'processing_method': 'batch_categorization_v3.0_irrelevant'
                }
            
            # Валидируем номер категории для релевантных постов
            validated_category_number = self._validate_category_number(category_number, len(bot_categories))
            if validated_category_number is None:
                logger.warning(f"📝 Пост {post.id} имеет невалидный номер категории {category_number}")
                # Создаем fallback результат
                return self._create_fallback_result(post)
            
            # Валидируем и нормализуем поля для релевантных постов
            normalized_result = {
                'post_id': post.id,
                'post_text': post.content[:200] + '...' if len(post.content or '') > 200 else post.content,
                'category_number': validated_category_number,
                'category_name': ai_result.get('category_name', 'Unknown'),
                'relevance_score': self._validate_score(ai_result.get('relevance_score'), 0.0, 1.0),
                'importance': self._validate_score(ai_result.get('importance'), 1, 10),
                'urgency': self._validate_score(ai_result.get('urgency'), 1, 10),
                'significance': self._validate_score(ai_result.get('significance'), 1, 10),
                'reasoning': str(ai_result.get('reasoning', 'Автоматическая категоризация'))[:500],
                'processing_method': 'batch_categorization_v3.0'
            }
            
            return normalized_result
            
        except Exception as e:
            logger.error(f"Ошибка валидации батчевого результата: {str(e)}")
            return self._create_fallback_result(post)
    
    async def _get_bot_config(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Получение конфигурации бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Ошибка получения конфигурации бота: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка запроса конфигурации бота: {str(e)}")
            return None
    
    async def _get_bot_categories(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получение категорий бота с описаниями"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/categories") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Ошибка получения категорий бота: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Ошибка запроса категорий бота: {str(e)}")
            return []
    
    def _validate_category_number(self, category_number: Any, max_categories: int) -> Optional[int]:
        """Валидация номера категории"""
        if category_number is None or category_number == 'null':
            return None
        
        try:
            num = int(category_number)
            if 1 <= num <= max_categories:
                return num
            else:
                logger.warning(f"Номер категории {num} вне диапазона 1-{max_categories}")
                return None
        except (ValueError, TypeError):
            logger.warning(f"Некорректный номер категории: {category_number}")
            return None
    
    def _validate_score(self, score: Any, min_val: float, max_val: float) -> float:
        """Валидация числовых оценок"""
        try:
            num = float(score)
            return max(min_val, min(max_val, num))
        except (ValueError, TypeError):
            return (min_val + max_val) / 2  # Возвращаем среднее значение при ошибке
    
    def _create_fallback_result(self, post: Post) -> Dict[str, Any]:
        """Создание fallback результата при ошибке AI"""
        return {
            'post_id': post.id,
            'post_text': post.content[:200] + '...' if len(post.content or '') > 200 else post.content,
            'category_number': None,
            'category_name': None,
            'relevance_score': 0.0,
            'importance': 5,
            'urgency': 5,
            'significance': 5,
            'reasoning': 'Fallback результат - ошибка AI категоризации',
            'processing_method': 'fallback_batch_v3.0'
        } 