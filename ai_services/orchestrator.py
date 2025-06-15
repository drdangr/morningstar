#!/usr/bin/env python3
"""
AI Orchestrator - Центральный координатор AI сервисов
Автоматически обрабатывает посты через CategorizationService и SummarizationService
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт сервисов
from ai_services.services.categorization import CategorizationService
from ai_services.services.summarization import SummarizationService

# Простые классы для данных
class Post:
    """Простой класс для поста"""
    def __init__(self, id, text, caption="", views=0, date=None, channel_id=None, message_id=None):
        self.id = id
        self.text = text
        self.caption = caption
        self.views = views
        self.date = date
        self.channel_id = channel_id
        self.message_id = message_id

class Bot:
    """Простой класс для бота"""
    def __init__(self, id, name, categorization_prompt="", summarization_prompt="", max_posts_per_digest=10, max_summary_length=150):
        self.id = id
        self.name = name
        self.categorization_prompt = categorization_prompt
        self.summarization_prompt = summarization_prompt
        self.max_posts_per_digest = max_posts_per_digest
        self.max_summary_length = max_summary_length

class AIOrchestrator:
    """
    AI Orchestrator - координатор автоматической обработки постов
    
    Функции:
    1. Мониторинг необработанных постов
    2. Получение настроек публичных ботов
    3. Вызов AI сервисов (категоризация + суммаризация)
    4. Сохранение результатов в Backend API
    5. Обновление статуса постов
    """
    
    def __init__(self, 
                 backend_url: str = "http://localhost:8000",
                 openai_api_key: Optional[str] = None,
                 processing_interval: int = 30,
                 batch_size: int = 10):
        
        self.backend_url = backend_url
        self.processing_interval = processing_interval
        self.batch_size = batch_size
        
        # Инициализация AI сервисов
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("⚠️ OPENAI_API_KEY не найден, будет использоваться mock режим")
        
        # Инициализация сервисов
        self.categorization_service = CategorizationService(
            openai_api_key=self.openai_api_key,
            backend_url=self.backend_url
        )
        
        self.summarization_service = SummarizationService(
            model_name="gpt-4o-mini",
            max_tokens=4000,
            temperature=0.3
        )
        
        # Статистика
        self.stats = {
            "total_processed": 0,
            "successful_processed": 0,
            "failed_processed": 0,
            "last_run": None,
            "processing_time": 0
        }
        
        logger.info("🤖 AI Orchestrator инициализирован")
        logger.info(f"📡 Backend URL: {self.backend_url}")
        logger.info(f"⏱️ Интервал обработки: {self.processing_interval}с")
        logger.info(f"📦 Размер батча: {self.batch_size}")
    
    async def get_unprocessed_posts(self, limit: int = None) -> List[Dict[str, Any]]:
        """Получить необработанные посты из Backend API"""
        limit = limit or self.batch_size
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/posts/unprocessed?limit={limit}"
                ) as response:
                    if response.status == 200:
                        posts = await response.json()
                        logger.info(f"📥 Получено {len(posts)} необработанных постов")
                        return posts
                    else:
                        logger.error(f"❌ Ошибка получения постов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении постов: {str(e)}")
            return []
    
    async def get_public_bots(self) -> List[Dict[str, Any]]:
        """Получить список активных публичных ботов (включая development)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/public-bots"  # Убираем фильтр, получаем всех
                ) as response:
                    if response.status == 200:
                        bots = await response.json()
                        # Фильтруем активных и development ботов
                        processing_bots = [bot for bot in bots if bot.get('status') in ['active', 'development']]
                        active_bots = [bot for bot in processing_bots if bot.get('status') == 'active']
                        dev_bots = [bot for bot in processing_bots if bot.get('status') == 'development']
                        
                        logger.info(f"🤖 Получено {len(active_bots)} активных ботов, {len(dev_bots)} в разработке")
                        return processing_bots
                    else:
                        logger.error(f"❌ Ошибка получения ботов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении ботов: {str(e)}")
            return []
    
    def convert_to_post_objects(self, posts_data: List[Dict[str, Any]]) -> List[Post]:
        """Конвертация данных постов в объекты Post"""
        posts = []
        for post_data in posts_data:
            try:
                # Парсинг даты
                post_date_str = post_data['post_date']
                if post_date_str.endswith('Z'):
                    post_date_str = post_date_str[:-1] + '+00:00'
                
                post = Post(
                    id=post_data['id'],
                    text=post_data.get('content', ''),
                    caption=post_data.get('title', ''),
                    views=post_data.get('views', 0),
                    date=datetime.fromisoformat(post_date_str),
                    channel_id=post_data['channel_telegram_id'],
                    message_id=post_data['telegram_message_id']
                )
                posts.append(post)
            except Exception as e:
                logger.error(f"⚠️ Ошибка конвертации поста {post_data.get('id', 'unknown')}: {str(e)}")
        
        logger.info(f"🔄 Конвертировано {len(posts)} постов в объекты Post")
        return posts
    
    def convert_to_bot_objects(self, bots_data: List[Dict[str, Any]]) -> List[Bot]:
        """Конвертация данных ботов в объекты Bot"""
        bots = []
        for bot_data in bots_data:
            try:
                bot = Bot(
                    id=bot_data['id'],
                    name=bot_data['name'],
                    categorization_prompt=bot_data.get('categorization_prompt'),
                    summarization_prompt=bot_data.get('summarization_prompt'),
                    max_posts_per_digest=bot_data.get('max_posts_per_digest', 10),
                    max_summary_length=bot_data.get('max_summary_length', 150)
                )
                bots.append(bot)
            except Exception as e:
                logger.error(f"⚠️ Ошибка конвертации бота {bot_data.get('id', 'unknown')}: {str(e)}")
        
        logger.info(f"🔄 Конвертировано {len(bots)} ботов в объекты Bot")
        return bots
    
    async def process_posts_for_bot(self, posts: List[Post], bot: Bot) -> List[Dict[str, Any]]:
        """Обработка постов для конкретного бота"""
        logger.info(f"🧠 Обработка {len(posts)} постов для бота '{bot.name}' (ID: {bot.id})")
        
        if not self.categorization_service:
            logger.error("❌ CategorizationService недоступен")
            return []
        
        # Используем существующий метод process_with_bot_config
        try:
            categorization_results = await self.categorization_service.process_with_bot_config(
                posts=posts,
                bot_id=bot.id
            )
        except Exception as e:
            logger.error(f"❌ Ошибка категоризации для бота {bot.id}: {str(e)}")
            return []
        
        results = []
        
        # Обрабатываем результаты категоризации
        for categorization_result in categorization_results:
            try:
                post_id = categorization_result.get('post_id')
                
                # Находим соответствующий пост
                post = next((p for p in posts if p.id == post_id), None)
                if not post:
                    logger.warning(f"⚠️ Пост {post_id} не найден для суммаризации")
                    continue
                
                # 2. Суммаризация поста (если есть OpenAI API)
                if self.openai_api_key and self.summarization_service:
                    summarization_result = await self.summarization_service.process(
                        text=post.text,
                        language="ru",
                        custom_prompt=bot.summarization_prompt
                    )
                else:
                    # Mock суммаризация
                    summarization_result = {
                        "summary": f"Краткое содержание: {post.text[:100]}..." if post.text else "Пост без текста",
                        "language": "ru",
                        "tokens_used": 150,
                        "status": "mock"
                    }
                
                # 3. Формирование результата
                ai_result = {
                    "post_id": post_id,
                    "public_bot_id": bot.id,
                    "summaries": {"ru": summarization_result.get("summary", "")},
                    "categories": {"ru": categorization_result.get("category_name", "NULL")},
                    "metrics": {
                        "importance": categorization_result.get("importance", 7),
                        "urgency": categorization_result.get("urgency", 6),
                        "significance": categorization_result.get("significance", 7),
                        "relevance_score": categorization_result.get("relevance_score", 0.0)
                    },
                    "processing_version": "v2.1",
                    "ai_metadata": {
                        "reasoning": categorization_result.get("reasoning", ""),
                        "tokens_used": categorization_result.get("tokens_used", 0) + summarization_result.get("tokens_used", 0)
                    }
                }
                
                results.append(ai_result)
                logger.info(f"  ✅ Пост {post_id}: {categorization_result.get('category_name', 'UNKNOWN')} (релевантность: {categorization_result.get('relevance_score', 0):.2f})")
                
            except Exception as e:
                logger.error(f"  ❌ Ошибка обработки результата для поста {categorization_result.get('post_id', 'N/A')}: {str(e)}")
                self.stats["failed_processed"] += 1
        
        logger.info(f"🎯 Обработано {len(results)} постов для бота '{bot.name}'")
        return results
    
    async def save_ai_results(self, ai_results: List[Dict[str, Any]]) -> bool:
        """Сохранение результатов AI обработки в Backend API"""
        if not ai_results:
            return True
        
        logger.info(f"💾 Сохранение {len(ai_results)} результатов AI обработки")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/ai/results/batch",
                    json=ai_results,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 201:
                        saved_results = await response.json()
                        logger.info(f"✅ Сохранено {len(saved_results)} результатов")
                        self.stats["successful_processed"] += len(saved_results)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка сохранения: HTTP {response.status}")
                        logger.error(f"   Детали: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Исключение при сохранении: {str(e)}")
            return False
    
    async def process_batch(self) -> bool:
        """Обработка одного батча постов"""
        start_time = datetime.now()
        
        # 1. Получение необработанных постов
        posts_data = await self.get_unprocessed_posts()
        if not posts_data:
            logger.info("📭 Нет необработанных постов")
            return True
        
        # 2. Получение активных ботов
        bots_data = await self.get_public_bots()
        if not bots_data:
            logger.warning("⚠️ Нет активных ботов для обработки")
            return False
        
        # 3. Конвертация в объекты
        posts = self.convert_to_post_objects(posts_data)
        bots = self.convert_to_bot_objects(bots_data)
        
        # 4. Обработка постов для каждого бота с разделением по статусам
        all_results = []
        dev_results = []  # Результаты для development ботов (только логирование)
        
        for bot_data in bots_data:
            bot = next((b for b in bots if b.id == bot_data['id']), None)
            if not bot:
                continue
                
            bot_results = await self.process_posts_for_bot(posts, bot)
            
            # Разделяем результаты по статусу бота
            if bot_data.get('status') == 'development':
                dev_results.extend(bot_results)
                logger.info(f"🧪 DEVELOPMENT MODE: Бот '{bot.name}' обработал {len(bot_results)} постов (результаты НЕ сохраняются)")
                # Детальное логирование для development ботов
                for result in bot_results:
                    logger.info(f"   📝 Пост {result['post_id']}: {result['categories']['ru']} (важность: {result['metrics']['importance']})")
            else:  # active статус
                all_results.extend(bot_results)
        
        # 5. Сохранение результатов (только для активных ботов)
        if all_results:
            success = await self.save_ai_results(all_results)
            if not success:
                return False
        
        # 6. Обновление статистики
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats["last_run"] = datetime.now()
        self.stats["processing_time"] = processing_time
        self.stats["total_processed"] += len(posts)
        
        logger.info(f"⏱️ Батч обработан за {processing_time:.2f}с")
        return True
    
    async def process_single_batch(self) -> Dict[str, Any]:
        """Обработка одного батча с возвратом статистики (для тестирования)"""
        logger.info("🧪 Запуск тестового батча AI Orchestrator")
        
        # Сброс статистики перед обработкой
        initial_stats = self.stats.copy()
        
        success = await self.process_batch()
        
        # Подготовка статистики
        stats = {
            "success": success,
            "posts_processed": self.stats['total_processed'] - initial_stats.get('total_processed', 0),
            "successful_processing": self.stats['successful_processed'] - initial_stats.get('successful_processed', 0),
            "errors": self.stats['failed_processed'] - initial_stats.get('failed_processed', 0),
            "processing_time": self.stats.get('processing_time', 0),
            "bots_processed": 1  # Примерное значение
        }
        
        if success:
            logger.info("🎉 Тестовый батч завершен успешно!")
        else:
            logger.error("💥 Тестовый батч завершен с ошибками")
        
        # Вывод финальной статистики
        logger.info("📊 Финальная статистика:")
        logger.info(f"  • Всего обработано: {stats['posts_processed']}")
        logger.info(f"  • Успешно: {stats['successful_processing']}")
        logger.info(f"  • Ошибок: {stats['errors']}")
        logger.info(f"  • Время обработки: {stats['processing_time']:.2f}с")
        
        return stats
    
    async def run_single_batch(self):
        """Запуск одного батча обработки (для тестирования)"""
        stats = await self.process_single_batch()
        return stats["success"]

async def main():
    """Главная функция для запуска AI Orchestrator"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Orchestrator для автоматической обработки постов")
    parser.add_argument("--mode", choices=["continuous", "single"], default="single",
                       help="Режим работы: continuous (непрерывно) или single (один батч)")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                       help="URL Backend API")
    parser.add_argument("--interval", type=int, default=30,
                       help="Интервал обработки в секундах")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Размер батча для обработки")
    
    args = parser.parse_args()
    
    # Создание AI Orchestrator
    orchestrator = AIOrchestrator(
        backend_url=args.backend_url,
        processing_interval=args.interval,
        batch_size=args.batch_size
    )
    
    # Запуск в выбранном режиме
    if args.mode == "continuous":
        await orchestrator.run_continuous()
    else:
        await orchestrator.run_single_batch()

if __name__ == "__main__":
    asyncio.run(main()) 