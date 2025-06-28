#!/usr/bin/env python3
"""
AI Orchestrator v4.0 - Полная переработка с нуля
Батчевая обработка + Мультитенантность + Правильная архитектура
+
+Новая архитектура статусов (с 26 июня 2025):
+- Используются булевые флаги is_categorized, is_summarized в processed_data
+- Статус рассчитывается автоматически: 0 флагов → pending, 1 флаг → processing, все флаги → completed
+- Оркестратор только сообщает какой сервис завершил работу через sync-status endpoint
+- Backend сам управляет всей логикой статусов
"""

import sys
import os
# Добавляем путь к ai_services для корректных импортов
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

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AIOrchestrator_v4')

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
    processing_version: str = "v4.0_multitenant_batch"
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
        
        logger.info(f"🚀 AI Orchestrator v4.0 инициализирован")
        logger.info(f"   Backend URL: {backend_url}")
        logger.info(f"   Размер батча: {batch_size}")
    
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
            
            # AI сервисы готовы к использованию (инициализация не требуется)
            
            logger.info("✅ AI сервисы инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации AI сервисов: {e}")
            return False
    
    async def run_single_batch(self, skip_initialization: bool = False):
        """Запуск одного батча обработки"""
        logger.info("🔄 Запуск одного батча AI обработки")
        
        # Проверяем, инициализированы ли AI сервисы, если нет - инициализируем
        # В continuous режиме пропускаем повторную инициализацию
        if not skip_initialization and (self.categorization_service is None or self.summarization_service is None):
            if not await self.initialize_ai_services():
                return False
        
        active_bots = await self.get_active_bots()
        if not active_bots:
            logger.info("✅ Нет активных ботов для обработки")
            return True
        
        logger.info(f"🤖 Найдено {len(active_bots)} активных ботов")
        
        total_processed = 0
        for bot in active_bots:
            try:
                processed_count = await self.process_bot(bot)
                total_processed += processed_count
                logger.info(f"✅ Бот '{bot['name']}': обработано {processed_count} постов")
            except Exception as e:
                logger.error(f"❌ Ошибка обработки бота '{bot['name']}': {e}")
        
        logger.info(f"🎉 Общий результат: обработано {total_processed} постов")
        await self.report_statistics(total_processed, len(active_bots))
        
        return total_processed > 0
    
    async def process_bot(self, bot: Dict[str, Any]) -> int:
        """Обработка постов для одного бота"""
        bot_id = bot['id']
        bot_name = bot['name']
        
        logger.info(f"🔄 Обработка бота: {bot_name} (ID: {bot_id})")
        
        # Получаем каналы и категории
        channels = await self.get_bot_channels(bot_id)
        if not channels:
            logger.warning(f"⚠️ У бота {bot_name} нет настроенных каналов")
            return 0
        
        categories = await self.get_bot_categories(bot_id)
        if not categories:
            logger.warning(f"⚠️ У бота {bot_name} нет настроенных категорий")
            return 0
        
        channel_telegram_ids = [ch['telegram_id'] for ch in channels]
        logger.info(f"📺 Каналы: {[ch['username'] for ch in channels]}")
        logger.info(f"📂 Категории: {[cat['category_name'] for cat in categories]}")
        
        # Получаем необработанные посты
        posts = await self.get_unprocessed_posts_for_bot(channel_telegram_ids, bot_id)
        if not posts:
            logger.info(f"✅ Нет необработанных постов для бота {bot_name}")
            return 0
        
        logger.info(f"📋 Найдено {len(posts)} необработанных постов")
        
        # ИСПРАВЛЕНО: Сначала обрабатываем посты, потом сохраняем результаты
        # БАТЧЕВАЯ ОБРАБОТКА
        results = await self.process_posts_batch(posts, bot, categories)
        
        # Сохраняем результаты (это создаст записи в processed_data)
        if results:
            saved_count = await self.save_results(results)
            logger.info(f"✅ Сохранено {saved_count} результатов")
            return saved_count
        else:
            logger.warning(f"⚠️ Нет результатов для сохранения")
            # Новая логика: не трогаем статусы, Backend сам управляет через флаги
            # Посты остаются в текущем статусе для повторной обработки
            return 0
    
    async def _get_posts_status(self, post_ids: List[int], bot_id: int) -> Dict[int, Dict[str, Any]]:
        """Возвращает словарь post_id → {status, is_categorized, is_summarized} для указанного бота.
        В случае ошибки все статусы считаются not_found (то есть требуют обработки).
        
        Новая логика с флагами:
        - Если запись существует, возвращаем её processing_status и флаги
        - Backend сам управляет статусами через флаги is_categorized/is_summarized
        """
        if not post_ids:
            return {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/ai/results/batch-status",
                    params={
                        "post_ids": ",".join(map(str, post_ids)),
                        "bot_id": bot_id,
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        statuses = {}
                        for s in data.get("statuses", []):
                            statuses[s["post_id"]] = {
                                "status": s.get("status", "not_found"),
                                "is_categorized": s.get("is_categorized", False),
                                "is_summarized": s.get("is_summarized", False)
                            }
                        return statuses
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить статусы постов: {e}")

        # fallback
        return {
            pid: {"status": "not_found", "is_categorized": False, "is_summarized": False}
            for pid in post_ids
        }

    async def process_posts_batch(self, posts: List[Dict], bot: Dict, categories: List[Dict]) -> List[ProcessingResult]:
        """🚀 БАТЧЕВАЯ ОБРАБОТКА ПОСТОВ"""
        logger.info(f"🚀 БАТЧЕВАЯ обработка {len(posts)} постов")
        
        try:
            from models.post import Post
            
            # Подготавливаем данные
            post_objects = []
            post_texts = []
            valid_posts = []
            
            for post_data in posts:
                content = post_data.get('content', '') or post_data.get('text', '')
                if not content or len(content.strip()) < 10:
                    logger.warning(f"⚠️ Пост {post_data['id']} слишком короткий, пропускаем")
                    continue
                
                post_obj = Post(
                    id=post_data['id'],
                    content=content,
                    channel_telegram_id=post_data.get('channel_telegram_id'),
                    created_at=post_data.get('post_date'),
                    telegram_message_id=post_data.get('telegram_message_id', 0)
                )
                
                post_objects.append(post_obj)
                post_texts.append(content)
                valid_posts.append(post_data)
            
            if not post_objects:
                logger.warning("⚠️ Нет валидных постов для обработки")
                return []
            
            logger.info(f"📝 Подготовлено {len(post_objects)} валидных постов")
            
            # Получаем текущие статусы постов (мультитенантно)
            post_ids = [p["id"] for p in valid_posts]
            current_statuses = await self._get_posts_status(post_ids, bot["id"])

            # --- Категоризация ---
            posts_for_cat: List[Post] = []
            idx_map_cat: List[int] = []  # индекс valid_posts → позиция в cat result
            for idx, vp in enumerate(valid_posts):
                status_info = current_statuses.get(vp["id"], {"status": "not_found", "is_categorized": False, "is_summarized": False})
                
                # Категоризируем только посты которые еще НЕ категоризированы
                if not status_info.get("is_categorized", False):
                    posts_for_cat.append(post_objects[idx])
                    idx_map_cat.append(idx)
                else:
                    logger.debug(f"Пропускаем категоризацию поста {vp['id']} - уже категоризирован")

            categorization_raw_results: List[Dict[str, Any]] = [{}] * len(valid_posts)

            if posts_for_cat:
                logger.info(f"🔄 Категоризация {len(posts_for_cat)} постов (будет пропущено {len(valid_posts)-len(posts_for_cat)})")
                cat_res = await self.categorization_service.process_with_bot_config(posts_for_cat, bot["id"])
                for local_i, global_idx in enumerate(idx_map_cat):
                    categorization_raw_results[global_idx] = cat_res[local_i] if local_i < len(cat_res) else {}

                # Обновляем статусы ТОЛЬКО для успешно категоризированных постов
                successful_cat_post_ids = []
                for local_i, global_idx in enumerate(idx_map_cat):
                    if local_i < len(cat_res) and cat_res[local_i]:
                        # Проверяем что результат не пустой и содержит категорию
                        result = cat_res[local_i]
                        if result.get('category_name') and result.get('relevance_score', 0) > 0:
                            successful_cat_post_ids.append(valid_posts[global_idx]["id"])
                        else:
                            logger.warning(f"⚠️ Пост {valid_posts[global_idx]['id']} не получил категорию")
                
                if successful_cat_post_ids:
                    logger.info(f"✅ Успешно категоризировано {len(successful_cat_post_ids)} из {len(posts_for_cat)} постов")
                    await self.sync_service_status(successful_cat_post_ids, bot["id"], "categorizer")
                else:
                    logger.warning(f"⚠️ Ни один пост не был успешно категоризирован")
            else:
                logger.info("ℹ️ Все посты уже категоризированы, шаг пропущен")

            # --- Саммаризация ---
            # ОБНОВЛЯЕМ СТАТУСЫ после категоризации для корректной фильтрации
            updated_statuses = await self._get_posts_status(post_ids, bot["id"])
            
            texts_for_sum: List[str] = []
            idx_map_sum: List[int] = []
            for idx, vp in enumerate(valid_posts):
                status_info = updated_statuses.get(vp["id"], {"status": "not_found", "is_categorized": False, "is_summarized": False})
                
                # Саммаризируем только посты которые еще НЕ саммаризированы
                if not status_info.get("is_summarized", False):
                    texts_for_sum.append(post_texts[idx])
                    idx_map_sum.append(idx)
                else:
                    logger.debug(f"Пропускаем саммаризацию поста {vp['id']} - уже саммаризирован")

            summarization_raw_results: List[Dict[str, Any]] = [{}] * len(valid_posts)

            if texts_for_sum:
                logger.info(f"🔄 Саммаризация {len(texts_for_sum)} постов (будет пропущено {len(valid_posts)-len(texts_for_sum)})")
                sum_res = await self.summarization_service.process_batch(
                    texts=texts_for_sum,
                    language=bot.get("default_language", "ru"),
                    custom_prompt=bot.get("summarization_prompt"),
                )
                for local_i, global_idx in enumerate(idx_map_sum):
                    summarization_raw_results[global_idx] = sum_res[local_i] if local_i < len(sum_res) else {}

                # Обновляем статусы ТОЛЬКО для успешно саммаризированных постов
                successful_sum_post_ids = []
                for local_i, global_idx in enumerate(idx_map_sum):
                    if local_i < len(sum_res) and sum_res[local_i]:
                        # Проверяем что результат не пустой и содержит саммари
                        result = sum_res[local_i]
                        if result.get('summary') and len(result.get('summary', '').strip()) > 10:
                            successful_sum_post_ids.append(valid_posts[global_idx]["id"])
                        else:
                            logger.warning(f"⚠️ Пост {valid_posts[global_idx]['id']} не получил саммари")
                
                if successful_sum_post_ids:
                    logger.info(f"✅ Успешно саммаризировано {len(successful_sum_post_ids)} из {len(texts_for_sum)} постов")
                    await self.sync_service_status(successful_sum_post_ids, bot["id"], "summarizer")
                else:
                    logger.warning(f"⚠️ Ни один пост не был успешно саммаризирован")
            else:
                logger.info("ℹ️ Все посты уже саммаризированы, шаг пропущен")

            # ОБЪЕДИНЯЕМ РЕЗУЛЬТАТЫ
            results = []
            for i, post_data in enumerate(valid_posts):
                try:
                    categorization_result = categorization_raw_results[i]
                    summarization_result = summarization_raw_results[i]
                    
                    result = ProcessingResult(
                        post_id=post_data['id'],
                        bot_id=bot['id'],
                        success=True,
                        categories={
                            "primary": categorization_result.get('category_name', ''),
                            "secondary": [],
                            "relevance_scores": [categorization_result.get('relevance_score', 0.0)]
                        },
                        summaries={
                            "ru": summarization_result.get('summary', ''),
                            "en": ""
                        },
                        metrics={
                            "importance": categorization_result.get('importance', 5.0),
                            "urgency": categorization_result.get('urgency', 5.0),
                            "significance": categorization_result.get('significance', 5.0),
                            "tokens_used": summarization_result.get('tokens_used', 0),
                            "processing_time": 0.0
                        }
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка объединения результатов для поста {post_data['id']}: {e}")
                    
                    fallback_result = ProcessingResult(
                        post_id=post_data['id'],
                        bot_id=bot['id'],
                        success=False,
                        categories={"primary": "", "secondary": [], "relevance_scores": [0.0]},
                        summaries={"ru": "", "en": ""},
                        metrics={"importance": 5.0, "urgency": 5.0, "significance": 5.0, "tokens_used": 0, "processing_time": 0.0},
                        error_message=str(e)
                    )
                    results.append(fallback_result)
            
            logger.info(f"📊 Создано {len(results)} финальных результатов")
            return results
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка батчевой обработки: {e}")
            return []
    
    async def save_results(self, results: List[ProcessingResult]) -> int:
        """Сохранение результатов через Backend API"""
        if not results:
            return 0
        
        try:
            api_results = []
            successful_post_ids = []
            failed_post_ids = []
            
            for result in results:
                if result.success:
                    api_result = {
                        "post_id": result.post_id,
                        "public_bot_id": result.bot_id,
                        "summaries": result.summaries,
                        "categories": result.categories,
                        "metrics": result.metrics,
                        "processing_version": result.processing_version
                    }
                    api_results.append(api_result)
                    successful_post_ids.append(result.post_id)
                else:
                    failed_post_ids.append(result.post_id)
            
            saved_count = 0
            if api_results:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.backend_url}/api/ai/results/batch",
                        json=api_results,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 201:
                            saved_results = await response.json()
                            saved_count = len(saved_results)
                            logger.info(f"✅ Сохранено {saved_count} AI результатов")
                            
                            # Новая логика: Backend обновляет флаги через sync-status
                            # Статус completed устанавливается автоматически когда все флаги = true
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Ошибка сохранения: HTTP {response.status}")
                            logger.error(f"   Детали: {error_text}")
            
            # Помечаем неуспешные результаты как failed
            if failed_post_ids:
                # Новая логика: не трогаем статусы для failed постов
                # Backend сам управляет статусами через флаги
                logger.warning(f"⚠️ {len(failed_post_ids)} постов не удалось обработать")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения результатов: {e}")
            return 0
    
    async def update_multitenant_status(self, post_ids: List[int], bot_id: int, status: ProcessingStatus):
        """БАТЧЕВОЕ обновление мультитенантных статусов"""
        if not post_ids:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.backend_url}/api/ai/results/batch-status",
                    json={
                        "post_ids": post_ids,
                        "bot_id": bot_id,
                        "status": status.value
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ Статусы обновлены: {len(post_ids)} постов → {status.value}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка обновления статусов: HTTP {response.status}")
                        logger.error(f"   Детали: {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статусов: {e}")
    
    async def sync_service_status(self, post_ids: List[int], bot_id: int, service: str):
        """Синхронизация статуса сервиса через новый endpoint sync-status"""
        if not post_ids:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.backend_url}/api/ai/results/sync-status",
                    json={
                        "post_ids": post_ids,
                        "bot_id": bot_id,
                        "service": service
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Статус {service} синхронизирован для {len(post_ids)} постов")
                        logger.debug(f"   Результат: {data}")
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка синхронизации {service}: HTTP {response.status}")
                        logger.error(f"   Детали: {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка sync-status для {service}: {e}")
    
    async def get_active_bots(self) -> List[Dict[str, Any]]:
        """Получение активных ботов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots") as response:
                    if response.status == 200:
                        bots = await response.json()
                        active_bots = [bot for bot in bots if bot.get('status') == 'active']
                        return active_bots
                    else:
                        logger.error(f"❌ Ошибка получения ботов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса ботов: {e}")
            return []
    
    async def get_bot_channels(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получение каналов бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/channels") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ Ошибка получения каналов бота {bot_id}: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса каналов бота {bot_id}: {e}")
            return []
    
    async def get_bot_categories(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получение категорий бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/categories") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ Ошибка получения категорий бота {bot_id}: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка запроса категорий бота {bot_id}: {e}")
            return []
    
    async def get_unprocessed_posts_for_bot(self, channel_telegram_ids: List[int], bot_id: int) -> List[Dict[str, Any]]:
        """Получение необработанных постов для бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/posts/unprocessed",
                    params={"limit": self.batch_size * 3}
                ) as response:
                    if response.status == 200:
                        all_posts = await response.json()
                    else:
                        logger.error(f"❌ Ошибка получения постов: HTTP {response.status}")
                        return []
            
            # Фильтруем по каналам бота
            bot_posts = [
                post for post in all_posts 
                if post.get('channel_telegram_id') in channel_telegram_ids
            ]
            
            if not bot_posts:
                return []
            
            # Проверяем статусы обработки
            post_ids = [post['id'] for post in bot_posts]
            
            async with aiohttp.ClientSession() as session:
                post_ids_str = ','.join(map(str, post_ids))
                async with session.get(
                    f"{self.backend_url}/api/ai/results/batch-status",
                    params={"post_ids": post_ids_str, "bot_id": bot_id}
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        posts_to_process = []
                        
                        # Создаем словарь статусов для быстрого поиска
                        status_map = {
                            s["post_id"]: s.get("status", "not_found")
                            for s in status_data.get("statuses", [])
                        }
                        
                        # Обрабатываем только посты со статусами not_found, pending, processing
                        # НЕ обрабатываем посты со статусом completed
                        for post in bot_posts:
                            post_status = status_map.get(post['id'], 'not_found')
                            if post_status in ['not_found', 'pending', 'processing']:
                                posts_to_process.append(post)
                            else:
                                logger.debug(f"Пропускаем пост {post['id']} со статусом '{post_status}'")
                        
                        logger.info(f"📊 Найдено {len(posts_to_process)} постов для обработки из {len(bot_posts)} (статусы: not_found/pending/processing)")
                        return posts_to_process[:self.batch_size]
                    else:
                        logger.error(f"❌ Ошибка проверки статусов: HTTP {response.status}")
                        return bot_posts[:self.batch_size]
                        
        except Exception as e:
            logger.error(f"❌ Ошибка получения необработанных постов: {e}")
            return []
    
    async def report_statistics(self, total_processed: int, active_bots_count: int):
        """Отправка статистики в Backend"""
        try:
            stats = {
                "orchestrator_status": "completed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "stats": {
                    "posts_processed": total_processed,
                    "active_bots": active_bots_count,
                    "processing_version": "v4.0_multitenant_batch"
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/ai/orchestrator-status",
                    json=stats,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Статистика отправлена в Backend")
                    else:
                        logger.warning(f"⚠️ Ошибка отправки статистики: HTTP {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка отправки статистики: {e}")
    
    async def report_continuous_status(self, status: str, details: Dict[str, Any] = None):
        """Отправка статуса непрерывного режима в Backend"""
        try:
            status_data = {
                "orchestrator_status": status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "stats": {
                    "mode": "continuous",
                    "processing_version": "v4.0_multitenant_continuous",
                    "background_worker_running": True if status in ["STARTED", "PROCESSING", "IDLE"] else False
                },
                "details": details or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/ai/orchestrator-status",
                    json=status_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ Статус '{status}' отправлен в Backend")
                    else:
                        logger.warning(f"⚠️ Ошибка отправки статуса: HTTP {response.status}")
                        
        except Exception as e:
            logger.debug(f"⚠️ Ошибка отправки статуса: {e}")
            # Не критично, продолжаем работу

async def main():
    parser = argparse.ArgumentParser(description='AI Orchestrator v4.0')
    parser.add_argument('--mode', choices=['single', 'continuous'], default='single')
    parser.add_argument('--batch-size', type=int, default=30)
    parser.add_argument('--backend-url', default='http://localhost:8000')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Запуск AI Orchestrator v4.0")
    logger.info(f"   Режим: {args.mode}")
    logger.info(f"   Размер батча: {args.batch_size}")
    
    orchestrator = AIOrchestrator(
        backend_url=args.backend_url,
        batch_size=args.batch_size
    )
    
    if args.mode == 'single':
        success = await orchestrator.run_single_batch()
        if success:
            logger.info("🎉 Обработка завершена успешно")
        else:
            logger.warning("⚠️ Обработка завершена без результатов")
    
    elif args.mode == 'continuous':
        logger.info("🔄 Запуск непрерывного режима")
        
        try:
            # Инициализация AI сервисов
            if not await orchestrator.initialize_ai_services():
                logger.error("❌ Не удалось инициализировать AI сервисы")
                return
            
            # Отправляем статус о запуске
            await orchestrator.report_continuous_status("STARTED", {"mode": "continuous", "batch_size": args.batch_size})
            
            # Основной цикл непрерывной обработки
            cycle_count = 0
            while True:
                try:
                    cycle_count += 1
                    logger.info(f"🔄 Цикл обработки #{cycle_count}")
                    
                    # Отправляем статус о начале обработки
                    await orchestrator.report_continuous_status("PROCESSING", {
                        "cycle": cycle_count,
                        "status": "processing_started"
                    })
                    
                    # Запускаем один батч обработки (пропускаем инициализацию - уже выполнена)
                    success = await orchestrator.run_single_batch(skip_initialization=True)
                    
                    if success:
                        logger.info(f"✅ Цикл #{cycle_count} завершен успешно")
                        await orchestrator.report_continuous_status("IDLE", {
                            "cycle": cycle_count,
                            "status": "processing_completed",
                            "result": "success"
                        })
                    else:
                        logger.info(f"ℹ️ Цикл #{cycle_count} завершен без результатов")
                        await orchestrator.report_continuous_status("IDLE", {
                            "cycle": cycle_count,
                            "status": "processing_completed",
                            "result": "no_posts"
                        })
                    
                    # Пауза между циклами (30 секунд)
                    logger.info("😴 Пауза 30 секунд до следующего цикла...")
                    await asyncio.sleep(30)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Получен сигнал остановки")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка в цикле #{cycle_count}: {e}")
                    await orchestrator.report_continuous_status("ERROR", {
                        "cycle": cycle_count,
                        "error": str(e)
                    })
                    # Пауза при ошибке (60 секунд)
                    await asyncio.sleep(60)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Непрерывный режим остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка непрерывного режима: {e}")
        finally:
            # Отправляем статус об остановке
            await orchestrator.report_continuous_status("STOPPED", {"reason": "shutdown"})
            logger.info("🏁 Непрерывный режим завершен")

if __name__ == "__main__":
    asyncio.run(main()) 