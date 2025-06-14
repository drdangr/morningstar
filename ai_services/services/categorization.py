#!/usr/bin/env python3
"""
CategorizationService v2.1 - AI-powered post categorization with numbered categories and descriptions
Улучшенная версия с нумерованными категориями и описаниями для более точной категоризации
"""

import asyncio
import aiohttp
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
from ai_services.models.post import Post

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CategorizationService:
    """
    Сервис для AI-категоризации постов с поддержкой настроек PublicBot
    v2.1 - Нумерованные категории с описаниями
    """
    
    def __init__(self, openai_api_key: str, backend_url: str = "http://localhost:8000"):
        """
        Инициализация сервиса
        
        Args:
            openai_api_key: API ключ OpenAI
            backend_url: URL Backend API
        """
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.backend_url = backend_url
        
    async def process_with_bot_config(self, posts: List[Post], bot_id: int) -> List[Dict[str, Any]]:
        """
        Категоризация постов с настройками конкретного PublicBot
        
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
            
            logger.info(f"🤖 Обрабатываем {len(posts)} постов для бота '{bot_config['name']}'")
            logger.info(f"📂 Доступно {len(bot_categories)} категорий")
            
            # Обрабатываем каждый пост
            results = []
            for i, post in enumerate(posts, 1):
                logger.info(f"📝 Обрабатываем пост {i}/{len(posts)}")
                
                result = await self._categorize_single_post(post, bot_config, bot_categories)
                if result:
                    results.append(result)
                    
                # Небольшая задержка между запросами
                await asyncio.sleep(0.5)
            
            logger.info(f"✅ Обработано {len(results)} постов")
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка в process_with_bot_config: {str(e)}")
            return []
    
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
    
    async def _categorize_single_post(self, post: Post, bot_config: Dict[str, Any], bot_categories: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Категоризация одного поста"""
        try:
            # Строим составной промпт v2.1
            system_prompt = self._build_composite_prompt_v2_1(bot_config, bot_categories)
            
            # Подготавливаем текст поста
            post_text = self._prepare_post_text(post)
            
            # Вызываем OpenAI API
            response = await self._call_openai_api(system_prompt, post_text)
            if not response:
                return None
            
            # Валидируем и нормализуем результат
            result = self._validate_and_normalize_result_v2_1(response, post, bot_categories)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка категоризации поста: {str(e)}")
            return None
    
    def _build_composite_prompt_v2_1(self, bot_config: Dict[str, Any], bot_categories: List[Dict[str, Any]]) -> str:
        """
        Построение составного промпта v2.1 с нумерованными категориями и описаниями
        
        Структура промпта:
        1. Bot Prompt (из настроек бота)
        2. Нумерованный список категорий с описаниями
        3. Инструкции по анализу
        4. Формат JSON ответа
        """
        
        # 1. Bot Prompt из настроек
        bot_prompt = bot_config.get('categorization_prompt', 'Анализируй посты и определи релевантные категории.')
        
        # 2. Формируем нумерованный список категорий с описаниями
        categories_list = []
        for i, category in enumerate(bot_categories, 1):
            name = category.get('category_name', category.get('name', 'Unknown'))
            description = category.get('description', 'Без описания')
            categories_list.append(f"{i}. {name} ({description})")
        
        categories_text = "\n".join(categories_list)
        
        # 3. Инструкции по анализу
        analysis_instructions = """Для каждого сообщения определи:
1. Номер релевантной категории из списка выше, если ни одна не подходит поставь null
2. Оценку релевантности для выбранной категории (0.0-1.0)
3. Важность новости (1-10) - насколько это важно для аудитории
4. Срочность (1-10) - насколько быстро нужно об этом узнать
5. Значимость (1-10) - долгосрочное влияние события"""
        
        # 4. Формат JSON ответа
        json_format = """{
  "category_number": 1,
  "category_name": "название категории",
  "relevance_score": 0.95,
  "importance": 9,
  "urgency": 8,
  "significance": 9,
  "reasoning": "краткое обоснование выбора категории и оценок"
}

ВАЖНО: Если категория не подходит, используй null (строчными буквами), не NULL!
Пример для нерелевантного поста:
{
  "category_number": null,
  "category_name": null,
  "relevance_score": 0.0,
  "importance": 5,
  "urgency": 3,
  "significance": 4,
  "reasoning": "пост не относится ни к одной из доступных категорий"
}"""
        
        # Собираем полный промпт
        full_prompt = f"""{bot_prompt}

Доступные Категории для анализа:
{categories_text}

{analysis_instructions}

Отвечай ТОЛЬКО валидным JSON без дополнительного текста:
{json_format}"""
        
        return full_prompt
    
    def _prepare_post_text(self, post: Post) -> str:
        """Подготовка текста поста для анализа"""
        text_parts = []
        
        if post.text:
            text_parts.append(post.text)
        
        if post.caption:
            text_parts.append(f"Подпись: {post.caption}")
        
        # Добавляем метаданные канала если есть
        if hasattr(post, 'channel_title') and post.channel_title:
            text_parts.append(f"Канал: {post.channel_title}")
        
        return "\n".join(text_parts)
    
    async def _call_openai_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Вызов OpenAI API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Ошибка вызова OpenAI API: {str(e)}")
            return None
    
    def _validate_and_normalize_result_v2_1(self, response: str, post: Post, bot_categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Валидация и нормализация результата v2.1"""
        try:
            # Извлекаем JSON из ответа
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("JSON не найден в ответе AI")
                return self._create_fallback_result(post)
            
            # Исправляем проблему с NULL -> null для корректного JSON парсинга
            json_text = json_match.group()
            json_text = re.sub(r'\bNULL\b', 'null', json_text)  # Заменяем NULL на null
            
            # Парсим JSON
            try:
                result = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Ошибка парсинга JSON: {str(e)}")
                logger.warning(f"Проблемный JSON: {json_text[:200]}...")
                return self._create_fallback_result(post)
            
            # Валидируем и нормализуем поля
            normalized_result = {
                'post_id': post.id,
                'post_text': post.text[:200] + '...' if len(post.text or '') > 200 else post.text,
                'category_number': self._validate_category_number(result.get('category_number'), len(bot_categories)),
                'category_name': result.get('category_name', 'Unknown'),
                'relevance_score': self._validate_score(result.get('relevance_score'), 0.0, 1.0),
                'importance': self._validate_score(result.get('importance'), 1, 10),
                'urgency': self._validate_score(result.get('urgency'), 1, 10),
                'significance': self._validate_score(result.get('significance'), 1, 10),
                'reasoning': result.get('reasoning', 'Нет обоснования')[:500],  # Ограничиваем длину
                'tokens_used': len(response.split()),  # Примерная оценка
                'processing_time': 0.0  # Будет заполнено выше
            }
            
            # Если категория NULL, обнуляем релевантность
            if normalized_result['category_number'] is None:
                normalized_result['relevance_score'] = 0.0
                normalized_result['category_name'] = 'NULL'
            
            return normalized_result
            
        except Exception as e:
            logger.error(f"Ошибка валидации результата: {str(e)}")
            return self._create_fallback_result(post)
    
    def _validate_category_number(self, category_number: Any, max_categories: int) -> Optional[int]:
        """Валидация номера категории"""
        if category_number is None or str(category_number).upper() == 'NULL':
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
            val = float(score)
            return max(min_val, min(max_val, val))
        except (ValueError, TypeError):
            return min_val
    
    def _create_fallback_result(self, post: Post) -> Dict[str, Any]:
        """Создание fallback результата при ошибках"""
        return {
            'post_id': post.id,
            'post_text': post.text[:200] + '...' if len(post.text or '') > 200 else post.text,
            'category_number': None,
            'category_name': 'NULL',
            'relevance_score': 0.0,
            'importance': 5,
            'urgency': 5,
            'significance': 5,
            'reasoning': 'Ошибка обработки AI',
            'tokens_used': 0,
            'processing_time': 0.0
        } 