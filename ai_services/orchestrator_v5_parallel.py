#!/usr/bin/env python3
"""
AI Orchestrator v5.0 - Параллельная архитектура
Революционное решение проблемы зависания через независимые worker циклы

КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ:
1. Два полностью независимых цикла - categorization_worker() и summarization_worker()
2. Флаги активности для предотвращения дублирования
3. Непрерывная обработка ВСЕ доступных постов до завершения
4. Умные циклы с проверкой флагов каждые 30 секунд

АРХИТЕКТУРА:
- Categorization Worker: обрабатывает посты с is_categorized=false
- Summarization Worker: обрабатывает посты с is_categorized=true, is_summarized=false
- Каждый worker работает независимо, не блокируя другой
- Backend автоматически управляет статусами через boolean флаги
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import asyncio
import aiohttp
import json
import logging
import argparse
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from models.post import Post

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AIOrchestrator_v5_Parallel')

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingResult:
    post_id: int
    bot_id: int
    success: bool
    categories: Dict[str, Any]
    summaries: Dict[str, Any]
    metrics: Dict[str, Any]
    processing_version: str = "v5.0_parallel_workers"
    error_message: Optional[str] = None

class AIOrchestrator:
    def __init__(self, backend_url: str = "http://localhost:8000", batch_size: int = 30):
        self.backend_url = backend_url
        self.batch_size = batch_size
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.categorization_service = None
        self.summarization_service = None
        
        # НОВЫЕ ФЛАГИ ДЛЯ ПАРАЛЛЕЛЬНОЙ АРХИТЕКТУРЫ
        self.categorization_is_running = False
        self.summarization_is_running = False
        self.workers_lock = asyncio.Lock()
        
        # Лимиты для предотвращения слишком долгой обработки
        self.max_batches_per_cycle = 10
        self.batch_timeout_minutes = 5
        
        logger.info(f"🚀 AI Orchestrator v5.0 инициализирован (Параллельная архитектура)")
        logger.info(f"   Backend URL: {backend_url}")
        logger.info(f"   Размер батча: {batch_size}")
        logger.info(f"   Макс батчей за цикл: {self.max_batches_per_cycle}")
    
    async def initialize_ai_services(self):
        """Инициализация AI сервисов"""
        try:
            from services.categorization import CategorizationService
            from services.summarization import SummarizationService
            
            self.categorization_service = CategorizationService(
                openai_api_key=self.openai_api_key,
                backend_url=self.backend_url,
                batch_size=self.batch_size
            )
            
            self.summarization_service = SummarizationService(
                model_name="gpt-4o-mini",
                max_tokens=4000,
                temperature=0.3
            )
            
            logger.info("✅ AI сервисы инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации AI сервисов: {e}")
            return False

    async def run_parallel_workers(self):
        """Новый метод: запуск параллельных worker циклов"""
        logger.info("🔄 Запуск параллельных AI worker циклов")
        
        # Инициализируем AI сервисы один раз
        if not await self.initialize_ai_services():
            logger.error("❌ Не удалось инициализировать AI сервисы")
            return False
        
        # Запускаем оба worker цикла параллельно
        try:
            await asyncio.gather(
                self.categorization_worker(),
                self.summarization_worker(),
                return_exceptions=True
            )
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Ошибка в параллельных worker циклах: {e}")

    async def categorization_worker(self):
        """Worker цикл для категоризации"""
        logger.info("🏷️ Запуск Categorization Worker")
        
        while True:
            try:
                # Проверяем флаг активности
                async with self.workers_lock:
                    if self.categorization_is_running:
                        logger.debug("🏷️ Categorization уже работает, пропускаем цикл")
                        await asyncio.sleep(30)
                        continue
                
                # Быстрая проверка наличия работы
                if not await self.has_uncategorized_posts():
                    logger.debug("🏷️ Нет некатегоризированных постов")
                    await asyncio.sleep(30)
                    continue
                
                # Выставляем флаг активности
                async with self.workers_lock:
                    self.categorization_is_running = True
                
                logger.info("🏷️ Categorization Worker: начинаем обработку")
                
                try:
                    # Обрабатываем ВСЕ доступные посты до завершения
                    await self.process_all_categorization()
                finally:
                    # Сбрасываем флаг активности
                    async with self.workers_lock:
                        self.categorization_is_running = False
                    logger.info("🏷️ Categorization Worker: цикл завершен")
                
                # Небольшая пауза перед следующей проверкой
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в Categorization Worker: {e}")
                # Сбрасываем флаг при ошибке
                async with self.workers_lock:
                    self.categorization_is_running = False
                await asyncio.sleep(60)  # Большая пауза при ошибке

    async def summarization_worker(self):
        """Worker цикл для саммаризации"""
        logger.info("📝 Запуск Summarization Worker")
        
        while True:
            try:
                # Проверяем флаг активности
                async with self.workers_lock:
                    if self.summarization_is_running:
                        logger.debug("📝 Summarization уже работает, пропускаем цикл")
                        await asyncio.sleep(30)
                        continue
                
                # Быстрая проверка наличия работы
                if not await self.has_unsummarized_posts():
                    logger.debug("📝 Нет несаммаризированных постов")
                    await asyncio.sleep(30)
                    continue
                
                # Выставляем флаг активности
                async with self.workers_lock:
                    self.summarization_is_running = True
                
                logger.info("📝 Summarization Worker: начинаем обработку")
                
                try:
                    # Обрабатываем ВСЕ доступные посты до завершения
                    await self.process_all_summarization()
                finally:
                    # Сбрасываем флаг активности
                    async with self.workers_lock:
                        self.summarization_is_running = False
                    logger.info("📝 Summarization Worker: цикл завершен")
                
                # Небольшая пауза перед следующей проверкой
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в Summarization Worker: {e}")
                # Сбрасываем флаг при ошибке
                async with self.workers_lock:
                    self.summarization_is_running = False
                await asyncio.sleep(60)  # Большая пауза при ошибке

    async def has_uncategorized_posts(self) -> bool:
        """Быстрая проверка наличия некатегоризированных постов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/ai/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Проверяем есть ли посты со статусом not_found или pending
                        # или посты с is_categorized=false
                        flags_stats = data.get("flags_stats", {})
                        uncategorized = flags_stats.get("uncategorized", 0)
                        return uncategorized > 0
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки некатегоризированных постов: {e}")
            # При ошибке считаем что работа есть (fail-safe)
            return True
        return False

    async def has_unsummarized_posts(self) -> bool:
        """Быстрая проверка наличия несаммаризированных постов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/ai/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Проверяем есть ли посты с is_summarized=false
                        flags_stats = data.get("flags_stats", {})
                        unsummarized = flags_stats.get("unsummarized", 0)
                        return unsummarized > 0
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки несаммаризированных постов: {e}")
            # При ошибке считаем что работа есть (fail-safe)
            return True
        return False

    async def process_all_categorization(self):
        """Обрабатывает ВСЕ некатегоризированные посты до завершения"""
        batches_processed = 0
        
        while batches_processed < self.max_batches_per_cycle:
            # Получаем активных ботов
            active_bots = await self.get_active_bots()
            if not active_bots:
                logger.info("✅ Нет активных ботов для категоризации")
                break
            
            work_found = False
            
            for bot in active_bots:
                try:
                    # Получаем посты для категоризации
                    posts = await self.get_posts_for_categorization(bot)
                    
                    if posts:
                        work_found = True
                        logger.info(f"🏷️ Категоризация: {len(posts)} постов для бота '{bot['name']}'")
                        
                        # Обрабатываем категоризацию
                        await self.process_categorization_batch(posts, bot)
                        
                        # Обновляем флаг категоризации
                        post_ids = [p['id'] for p in posts]
                        await self.sync_service_status(post_ids, bot['id'], 'categorization')
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка категоризации для бота '{bot['name']}': {e}")
            
            if not work_found:
                logger.info("✅ Все посты категоризированы")
                break
            
            batches_processed += 1
            
            # Небольшая пауза между батчами
            await asyncio.sleep(1)
        
        if batches_processed >= self.max_batches_per_cycle:
            logger.warning(f"⚠️ Достигнут лимит батчей категоризации: {self.max_batches_per_cycle}")

    async def process_all_summarization(self):
        """Обрабатывает ВСЕ несаммаризированные посты до завершения"""
        batches_processed = 0
        
        while batches_processed < self.max_batches_per_cycle:
            # Получаем активных ботов
            active_bots = await self.get_active_bots()
            if not active_bots:
                logger.info("✅ Нет активных ботов для саммаризации")
                break
            
            work_found = False
            
            for bot in active_bots:
                try:
                    # Получаем посты для саммаризации
                    posts = await self.get_posts_for_summarization(bot)
                    
                    if posts:
                        work_found = True
                        logger.info(f"📝 Саммаризация: {len(posts)} постов для бота '{bot['name']}'")
                        
                        # Обрабатываем саммаризацию
                        await self.process_summarization_batch(posts, bot)
                        
                        # Обновляем флаг саммаризации
                        post_ids = [p['id'] for p in posts]
                        await self.sync_service_status(post_ids, bot['id'], 'summarization')
                        
                except Exception as e:
                    logger.error(f"❌ Ошибка саммаризации для бота '{bot['name']}': {e}")
            
            if not work_found:
                logger.info("✅ Все посты саммаризированы")
                break
            
            batches_processed += 1
            
            # Небольшая пауза между батчами
            await asyncio.sleep(1)
        
        if batches_processed >= self.max_batches_per_cycle:
            logger.warning(f"⚠️ Достигнут лимит батчей саммаризации: {self.max_batches_per_cycle}")

    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====
    
    async def get_posts_for_categorization(self, bot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получить посты для категоризации (is_categorized=false)"""
        bot_id = bot['id']
        
        # Получаем каналы бота
        channels = await self.get_bot_channels(bot_id)
        if not channels:
            return []
        
        channel_telegram_ids = [ch['telegram_id'] for ch in channels]
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "channel_telegram_ids": ",".join(map(str, channel_telegram_ids)),
                    "bot_id": bot_id,
                    "limit": self.batch_size,
                    "require_categorization": "true"  # Только некатегоризированные
                }
                
                async with session.get(
                    f"{self.backend_url}/api/posts/unprocessed",
                    params=params
                ) as response:
                    if response.status == 200:
                        posts = await response.json()
                        return posts  # Endpoint возвращает список напрямую
                    else:
                        logger.warning(f"⚠️ Ошибка получения постов для категоризации: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса постов для категоризации: {e}")
            return []

    async def get_posts_for_summarization(self, bot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Получить посты для саммаризации (is_categorized=true, is_summarized=false)"""
        bot_id = bot['id']
        
        # Получаем каналы бота
        channels = await self.get_bot_channels(bot_id)
        if not channels:
            return []
        
        channel_telegram_ids = [ch['telegram_id'] for ch in channels]
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "channel_telegram_ids": ",".join(map(str, channel_telegram_ids)),
                    "bot_id": bot_id,
                    "limit": self.batch_size,
                    "require_summarization": "true"  # Только несаммаризированные
                }
                
                async with session.get(
                    f"{self.backend_url}/api/posts/unprocessed",
                    params=params
                ) as response:
                    if response.status == 200:
                        posts = await response.json()
                        return posts  # Endpoint возвращает список напрямую
                    else:
                        logger.warning(f"⚠️ Ошибка получения постов для саммаризации: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса постов для саммаризации: {e}")
            return []

    async def process_categorization_batch(self, posts: List[Dict], bot: Dict):
        """Обработка батча категоризации"""
        categories = await self.get_bot_categories(bot['id'])
        if not categories:
            logger.warning(f"⚠️ У бота {bot['name']} нет категорий для категоризации")
            return
        
        # Используем существующий CategorizationService
        if self.categorization_service:
            try:
                # Конвертируем посты в объекты Post для CategorizationService
                post_objects = []
                for post_dict in posts:
                    post_obj = Post(
                        id=post_dict['id'],
                        channel_telegram_id=post_dict['channel_telegram_id'],
                        telegram_message_id=post_dict['telegram_message_id'],
                        title=post_dict.get('title', ''),
                        content=post_dict.get('content', ''),
                        post_date=post_dict['post_date'],
                        views=post_dict.get('views', 0),
                        media_urls=post_dict.get('media_urls', [])
                    )
                    post_objects.append(post_obj)
                
                # Вызываем правильный метод CategorizationService
                results = await self.categorization_service.process_with_bot_config(
                    post_objects, bot['id']
                )
                
                if results:
                    # Конвертируем результаты в ProcessingResult
                    processing_results = []
                    for result in results:
                        processing_result = ProcessingResult(
                            post_id=result.get('post_id', 0),
                            bot_id=bot['id'],
                            success=True,
                            categories=result,
                            summaries={},
                            metrics=result.get('metrics', {})
                        )
                        processing_results.append(processing_result)
                    
                    # Сохраняем результаты категоризации
                    saved_count = await self.save_results(processing_results)
                    logger.info(f"✅ Категоризация: сохранено {saved_count} результатов")
                    
                    # Обновляем флаги категоризации
                    post_ids = [result.get('post_id', 0) for result in results]
                    await self.sync_service_status(post_ids, bot['id'], 'categorization')
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки категоризации: {e}")

    async def process_summarization_batch(self, posts: List[Dict], bot: Dict):
        """Обработка батча саммаризации"""
        # Используем существующий SummarizationService
        if self.summarization_service:
            try:
                # Для саммаризации нужны категоризированные данные
                processed_posts = []
                for post in posts:
                    # Получаем данные из processed_data для этого поста и бота
                    processed_data = await self.get_processed_data(post['id'], bot['id'])
                    if processed_data and processed_data.get('categorization_result'):
                        processed_posts.append({
                            **post,
                            'categories': processed_data['categorization_result']
                        })
                
                if processed_posts:
                    # Извлекаем тексты для батчевой обработки
                    texts = []
                    for post in processed_posts:
                        text = f"{post.get('title', '')} {post.get('content', '')}".strip()
                        texts.append(text)
                    
                    # Вызываем правильный метод SummarizationService
                    results = await self.summarization_service.process_batch(texts)
                    
                    if results:
                        # Конвертируем результаты в ProcessingResult
                        processing_results = []
                        for i, result in enumerate(results):
                            if i < len(processed_posts):
                                processing_result = ProcessingResult(
                                    post_id=processed_posts[i]['id'],
                                    bot_id=bot['id'],
                                    success=True,
                                    categories=processed_posts[i].get('categories', {}),
                                    summaries=result,
                                    metrics={}
                                )
                                processing_results.append(processing_result)
                        
                        # Сохраняем результаты саммаризации
                        saved_count = await self.save_results(processing_results)
                        logger.info(f"✅ Саммаризация: сохранено {saved_count} результатов")
                        
                        # Обновляем флаги саммаризации
                        post_ids = [post['id'] for post in processed_posts]
                        await self.sync_service_status(post_ids, bot['id'], 'summarization')
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки саммаризации: {e}")

    async def get_processed_data(self, post_id: int, bot_id: int) -> Optional[Dict]:
        """Получить обработанные данные для поста и бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/ai/results",
                    params={"post_id": post_id, "bot_id": bot_id}
                ) as response:
                    if response.status == 200:
                        results = await response.json()  # Endpoint возвращает список
                        return results[0] if results else None
                    return None
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения processed_data для поста {post_id}: {e}")
            return None

    # ===== МЕТОДЫ ИЗ V4 (НЕИЗМЕНЕННЫЕ) =====
    
    async def sync_service_status(self, post_ids: List[int], bot_id: int, service: str):
        """Синхронизация статуса сервиса через boolean флаги"""
        if not post_ids:
            return
        
        try:
            # Определяем какой флаг обновлять
            update_data = {}
            if service == 'categorization':
                update_data['is_categorized'] = True
            elif service == 'summarization':
                update_data['is_summarized'] = True
            else:
                logger.warning(f"⚠️ Неизвестный сервис: {service}")
                return
            
            # Маппинг сервисов для API
            service_mapping = {
                'categorization': 'categorizer',
                'summarization': 'summarizer'
            }
            
            payload = {
                "post_ids": post_ids,
                "bot_id": bot_id,
                "service": service_mapping.get(service, service),
                **update_data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.backend_url}/api/ai/results/sync-status",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Обновлен флаг {service}: {len(post_ids)} постов, статус: {data.get('message', 'OK')}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка обновления флага {service}: {response.status} - {error_text}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации статуса {service}: {e}")

    async def save_results(self, results: List[ProcessingResult]) -> int:
        """Сохранение результатов AI обработки"""
        if not results:
            return 0
        
        try:
            # Преобразуем результаты в формат для API
            results_data = []
            for result in results:
                result_dict = {
                    "post_id": result.post_id,
                    "public_bot_id": result.bot_id,
                    "categorization_result": result.categories,
                    "summarization_result": result.summaries,
                    "metrics": result.metrics,
                    "processing_version": result.processing_version,
                    "success": result.success
                }
                
                if result.error_message:
                    result_dict["error_message"] = result.error_message
                
                results_data.append(result_dict)
            
            # Отправляем батчевый запрос (API ожидает список, не объект)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/ai/results/batch",
                    json=results_data  # Передаем список напрямую
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        saved_count = data.get("saved_count", 0)
                        logger.info(f"✅ Сохранено {saved_count} результатов в processed_data")
                        return saved_count
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка сохранения результатов: {response.status} - {error_text}")
                        return 0
        
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {e}")
            return 0

    async def get_active_bots(self) -> List[Dict[str, Any]]:
        """Получить список активных ботов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots") as response:
                    if response.status == 200:
                        bots = await response.json()  # Endpoint возвращает список напрямую
                        active_bots = [bot for bot in bots if bot.get("status") == "active"]
                        return active_bots
                    else:
                        logger.error(f"❌ Ошибка получения ботов: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса ботов: {e}")
            return []

    async def get_bot_channels(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получить каналы для бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/channels") as response:
                    if response.status == 200:
                        channels = await response.json()  # Endpoint возвращает список напрямую
                        return channels
                    else:
                        logger.warning(f"⚠️ Ошибка получения каналов для бота {bot_id}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса каналов для бота {bot_id}: {e}")
            return []

    async def get_bot_categories(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получить категории для бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/categories") as response:
                    if response.status == 200:
                        categories = await response.json()  # Endpoint возвращает список напрямую
                        return categories
                    else:
                        logger.warning(f"⚠️ Ошибка получения категорий для бота {bot_id}: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса категорий для бота {bot_id}: {e}")
            return []

    # ===== LEGACY МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ =====
    
    async def run_single_batch(self, skip_initialization: bool = False):
        """Legacy метод для совместимости с существующими тестами"""
        logger.info("🔄 Запуск одного батча AI обработки (Legacy mode)")
        
        if not skip_initialization and (self.categorization_service is None or self.summarization_service is None):
            if not await self.initialize_ai_services():
                return False
        
        # Запускаем один цикл каждого worker'а
        await self.process_all_categorization()
        await self.process_all_summarization()
        
        return True

async def main():
    """Главная функция для запуска AI Orchestrator"""
    parser = argparse.ArgumentParser(description='AI Orchestrator v5.0 - Параллельная архитектура')
    parser.add_argument('mode', choices=['single', 'parallel'], 
                       help='Режим работы: single - один батч, parallel - параллельные workers')
    parser.add_argument('--backend-url', default='http://localhost:8000',
                       help='URL Backend API (по умолчанию: http://localhost:8000)')
    parser.add_argument('--batch-size', type=int, default=30,
                       help='Размер батча для обработки (по умолчанию: 30)')
    
    args = parser.parse_args()
    
    orchestrator = AIOrchestrator(
        backend_url=args.backend_url,
        batch_size=args.batch_size
    )
    
    try:
        if args.mode == 'single':
            logger.info("🎯 Режим: Одиночный батч")
            success = await orchestrator.run_single_batch()
            if success:
                logger.info("✅ Одиночный батч завершен успешно")
            else:
                logger.error("❌ Ошибка выполнения одиночного батча")
        
        elif args.mode == 'parallel':
            logger.info("🔄 Режим: Параллельные workers")
            await orchestrator.run_parallel_workers()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 