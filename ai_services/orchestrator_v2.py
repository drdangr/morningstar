#!/usr/bin/env python3
"""
AI Orchestrator v2.0 - Event-Driven Architecture
Центральный координатор AI сервисов с приоритетной очередью и реактивной обработкой
"""

import asyncio
import aiohttp
import heapq
import os
import sys
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from loguru import logger

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт сервисов
from ai_services.services.categorization import CategorizationService
from ai_services.services.summarization import SummarizationService

# Система приоритетов согласно документации
class AITaskPriority(Enum):
    BACKGROUND = 1    # Фоновая обработка (когда все сделано)
    NORMAL = 2        # Плановая обработка
    HIGH = 3          # Активные боты, скорые дайджесты
    URGENT = 4        # Пользовательские запросы
    CRITICAL = 5      # Принудительные операции, новые данные

class AITaskType(Enum):
    # Системные операции
    STARTUP_PROCESSING = "startup_processing"
    BACKGROUND_PROCESSING = "background_processing"
    
    # Принудительные операции (CRITICAL приоритет)
    FORCE_REPROCESS_ALL = "force_reprocess_all"
    FORCE_REPROCESS_CHANNELS = "force_reprocess_channels"
    FORCE_REPROCESS_BOT = "force_reprocess_bot"
    CLEAR_AI_RESULTS = "clear_ai_results"
    
    # Реактивные операции (URGENT/CRITICAL приоритет)
    NEW_POSTS_PROCESSING = "new_posts_processing"
    BOT_SETTINGS_CHANGED = "bot_settings_changed"
    USER_URGENT_REQUEST = "user_urgent_request"
    
    # Плановые операции (NORMAL/HIGH приоритет)
    SCHEDULED_PROCESSING = "scheduled_processing"
    DIGEST_PREPARATION = "digest_preparation"

@dataclass
class AITask:
    task_type: AITaskType
    priority: AITaskPriority
    bot_id: Optional[int] = None
    channel_ids: Optional[List[int]] = None
    post_ids: Optional[List[int]] = None
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __lt__(self, other):
        """Сравнение для heapq (меньший приоритет = выше в очереди)"""
        return (-self.priority.value, self.created_at) < (-other.priority.value, other.created_at)

class AIOrchestratorV2:
    """
    AI Orchestrator v2.0 - Event-Driven Architecture
    
    Функции:
    1. Приоритетная очередь задач (heapq)
    2. Реактивная обработка новых данных от Userbot
    3. Умная остановка/пробуждение фонового обработчика
    4. Система прерываний для критических задач
    5. Startup initialization с проверкой необработанных данных
    """
    
    def __init__(self, 
                 backend_url: str = "http://localhost:8000",
                 openai_api_key: Optional[str] = None,
                 batch_size: int = 10):
        
        self.backend_url = backend_url
        self.batch_size = batch_size
        
        # Event-Driven архитектура
        self.task_queue = []  # Приоритетная очередь (heapq)
        self.processing_locks = {}  # Активные задачи
        self.background_worker_running = False
        self.last_activity = None
        self.worker_event = asyncio.Event()  # Событие для пробуждения
        
        # Инициализация AI сервисов
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("⚠️ OPENAI_API_KEY не найден, будет использоваться mock режим")
        
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
            "processing_time": 0,
            "queue_size": 0,
            "active_tasks": 0
        }
        
        logger.info("🤖 AI Orchestrator v2.0 (Event-Driven) инициализирован")
        logger.info(f"📡 Backend URL: {self.backend_url}")
        logger.info(f"📦 Размер батча: {self.batch_size}")

    # === СИСТЕМА СОБЫТИЙ И ПРИОРИТЕТОВ ===
    
    async def handle_new_posts_from_userbot(self, post_ids: List[int], channel_id: int):
        """Обработка сигнала о новых данных от Userbot"""
        logger.info(f"📡 Получен сигнал о {len(post_ids)} новых постах из канала {channel_id}")
        
        # Определяем затронутых ботов
        affected_bots = await self._get_bots_using_channel(channel_id)
        
        if not affected_bots:
            logger.warning(f"⚠️ Канал {channel_id} не используется активными ботами")
            return
        
        # Создаем задачи для каждого затронутого бота
        for bot_id in affected_bots:
            task = AITask(
                task_type=AITaskType.NEW_POSTS_PROCESSING,
                priority=AITaskPriority.CRITICAL,  # Новые данные = критический приоритет
                bot_id=bot_id,
                post_ids=post_ids,
                metadata={
                    'channel_id': channel_id,
                    'trigger': 'userbot_new_posts',
                    'posts_count': len(post_ids)
                }
            )
            
            await self._add_task_to_queue(task)
        
        # Если фоновый обработчик остановился - запускаем
        if not self.background_worker_running:
            logger.info("🔄 Фоновый обработчик остановлен, запускаем...")
            await self._start_background_worker()

    async def _add_task_to_queue(self, task: AITask):
        """Добавление задачи в приоритетную очередь"""
        # Проверяем дублирование
        if await self._is_duplicate_task(task):
            logger.warning(f"⚠️ Задача {task.task_type.value} уже выполняется, пропускаем")
            return
        
        # Если это критическая задача - прерываем текущую обработку
        if task.priority == AITaskPriority.CRITICAL:
            await self._interrupt_current_processing(task)
        
        # Добавляем в приоритетную очередь
        heapq.heappush(self.task_queue, task)
        self.stats['queue_size'] = len(self.task_queue)
        
        logger.info(f"➕ Задача добавлена: {task.task_type.value} (приоритет: {task.priority.name})")
        
        # Будим фоновый обработчик
        self.worker_event.set()

    async def _is_duplicate_task(self, task: AITask) -> bool:
        """Проверка дублирования задач"""
        # Простая проверка по типу задачи и bot_id
        for existing_task in self.task_queue:
            if (existing_task.task_type == task.task_type and 
                existing_task.bot_id == task.bot_id):
                return True
        return False

    async def _interrupt_current_processing(self, urgent_task: AITask):
        """Прерывание текущей обработки для критических задач"""
        if urgent_task.priority == AITaskPriority.CRITICAL:
            logger.warning(f"🚨 ПРЕРЫВАНИЕ: Критическая задача {urgent_task.task_type.value}")
            
            # Помечаем текущие задачи для прерывания
            for lock_key in list(self.processing_locks.keys()):
                current_task = self.processing_locks[lock_key]
                if current_task.priority.value < urgent_task.priority.value:
                    logger.info(f"⏸️ Прерываем задачу {current_task.task_type.value}")

    # === УМНЫЙ ФОНОВЫЙ ОБРАБОТЧИК ===
    
    async def _start_background_worker(self):
        """Запуск умного фонового обработчика"""
        if self.background_worker_running:
            return
        
        self.background_worker_running = True
        logger.info("🚀 Запуск умного фонового обработчика")
        
        # Запускаем в отдельной задаче
        asyncio.create_task(self._smart_background_worker())

    async def _smart_background_worker(self):
        """Умный фоновый обработчик согласно документации"""
        logger.info("🧠 Умный фоновый обработчик запущен")
        
        try:
            while self.background_worker_running:
                if not self.task_queue:
                    # НЕТ ЗАДАЧ - ЗАСЫПАЕМ до получения сигнала
                    logger.info("😴 Нет задач, засыпаем до получения сигнала...")
                    await self.report_orchestrator_status("IDLE", {"queue_size": 0})
                    
                    # Ждем сигнала о новых задачах
                    await self.worker_event.wait()
                    self.worker_event.clear()
                    
                    logger.info("⏰ Получен сигнал, просыпаемся...")
                else:
                    # ЕСТЬ ЗАДАЧИ - обрабатываем по приоритетам
                    task = heapq.heappop(self.task_queue)
                    self.stats['queue_size'] = len(self.task_queue)
                    
                    logger.info(f"🔄 Обрабатываем задачу: {task.task_type.value} (приоритет: {task.priority.name})")
                    
                    await self.report_orchestrator_status("PROCESSING", {
                        "current_task": task.task_type.value,
                        "priority": task.priority.name,
                        "queue_size": len(self.task_queue)
                    })
                    
                    # Обрабатываем задачу
                    success = await self._process_task(task)
                    
                    if success:
                        logger.info(f"✅ Задача {task.task_type.value} выполнена успешно")
                    else:
                        logger.error(f"❌ Ошибка выполнения задачи {task.task_type.value}")
                    
                    # Обновляем активность
                    self.last_activity = datetime.utcnow()
                    
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в фоновом обработчике: {str(e)}")
        finally:
            self.background_worker_running = False
            logger.info("🛑 Умный фоновый обработчик остановлен")

    async def startup_initialization(self):
        """Инициализация при запуске системы - проверка необработанных данных"""
        logger.info("🚀 Startup Initialization - проверка необработанных данных")
        
        # 1. Проверяем наличие необработанных данных
        pending_data = await self._check_pending_data()
        
        if pending_data['total_posts'] > 0:
            logger.info(f"📊 Найдено {pending_data['total_posts']} необработанных постов")
            
            # 2. Запускаем обработку по приоритетам
            await self._schedule_pending_data_processing(pending_data)
        else:
            logger.info("✅ Все данные обработаны")
        
        # 3. Запускаем фоновый обработчик
        await self._start_background_worker()
        
        logger.info("✅ AI Orchestrator готов к работе")

    async def run_continuous(self):
        """Непрерывная обработка в Event-Driven режиме"""
        logger.info("🔄 Запуск непрерывной Event-Driven обработки")
        
        # Startup initialization
        await self.startup_initialization()
        
        # Основной цикл - просто ждем прерывания
        try:
            while True:
                await asyncio.sleep(60)  # Проверяем каждую минуту что система работает
                
                # Логируем статистику
                if self.background_worker_running:
                    logger.debug(f"📊 Статистика: очередь={len(self.task_queue)}, активных={len(self.processing_locks)}")
                
        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал остановки, завершение работы")
            await self.stop_background_worker()

    async def stop_background_worker(self):
        """Остановка фонового обработчика"""
        logger.info("🛑 Остановка фонового обработчика")
        self.background_worker_running = False
        self.worker_event.set()  # Будим чтобы он завершился

    # === ЗАГЛУШКИ ДЛЯ МЕТОДОВ (БУДУТ РЕАЛИЗОВАНЫ) ===
    
    async def _get_bots_using_channel(self, channel_id: int) -> List[int]:
        """Получить список ботов, использующих данный канал"""
        # Заглушка - возвращаем тестовый бот
        return [1] if channel_id else []

    async def _check_pending_data(self) -> Dict[str, Any]:
        """Проверка необработанных данных при запуске"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/posts/unprocessed?limit=1000") as response:
                    if response.status == 200:
                        posts = await response.json()
                        return {
                            'total_posts': len(posts),
                            'bots_affected': 1,  # Заглушка
                            'pending_by_bot': {1: len(posts)}
                        }
                    else:
                        logger.error(f"❌ Ошибка проверки данных: HTTP {response.status}")
                        return {'total_posts': 0, 'bots_affected': 0, 'pending_by_bot': {}}
        except Exception as e:
            logger.error(f"❌ Исключение при проверке данных: {str(e)}")
            return {'total_posts': 0, 'bots_affected': 0, 'pending_by_bot': {}}

    async def _schedule_pending_data_processing(self, pending_data: Dict[str, Any]):
        """Планирование обработки необработанных данных по приоритетам"""
        logger.info(f"📋 Планирование обработки {pending_data['total_posts']} постов")
        
        # Создаем задачу фоновой обработки
        task = AITask(
            task_type=AITaskType.BACKGROUND_PROCESSING,
            priority=AITaskPriority.NORMAL,
            metadata={'startup_processing': True, 'total_posts': pending_data['total_posts']}
        )
        
        await self._add_task_to_queue(task)
        logger.info("✅ Задача обработки добавлена в очередь")

    async def _process_task(self, task: AITask) -> bool:
        """Обработка конкретной задачи"""
        logger.info(f"🔄 Обработка задачи {task.task_type.value}")
        
        try:
            if task.task_type == AITaskType.BACKGROUND_PROCESSING:
                return await self._process_background_batch()
            elif task.task_type == AITaskType.NEW_POSTS_PROCESSING:
                return await self._process_new_posts(task.post_ids, task.channel_ids)
            elif task.task_type == AITaskType.FORCE_REPROCESS_CHANNELS:
                return await self._reprocess_channels(task.channel_ids)
            else:
                logger.warning(f"⚠️ Неизвестный тип задачи: {task.task_type.value}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки задачи {task.task_type.value}: {str(e)}")
            return False

    async def _process_background_batch(self) -> bool:
        """Обработка фонового батча постов"""
        logger.info("🔄 Обработка фонового батча")
        
        try:
            # Получаем необработанные посты
            pending_posts = await self._get_pending_posts(limit=self.batch_size)
            
            if not pending_posts:
                logger.info("✅ Нет необработанных постов")
                return True
            
            logger.info(f"📋 Найдено {len(pending_posts)} необработанных постов")
            
            # Обрабатываем AI сервисами (заглушка)
            ai_results = []
            for post in pending_posts:
                # Имитация AI обработки
                ai_result = {
                    "post_id": post["id"],
                    "public_bot_id": 1,  # Тестовый бот
                    "summaries": {
                        "ru": f"AI резюме для поста {post['id']}",
                        "en": f"AI summary for post {post['id']}"
                    },
                    "categories": {
                        "primary": "Тестовая категория",
                        "secondary": ["AI", "Тест"],
                        "relevance_scores": [0.95, 0.85]
                    },
                    "metrics": {
                        "importance": 8.0,
                        "urgency": 7.0, 
                        "significance": 8.5,
                        "tokens_used": 150,
                        "processing_time": 1.5
                    },
                    "processing_version": "v2.0"
                }
                ai_results.append(ai_result)
            
            # Сохраняем результаты
            if ai_results:
                success = await self._save_ai_results(ai_results)
                if success:
                    logger.info(f"✅ Сохранено {len(ai_results)} AI результатов")
                    return True
                else:
                    logger.error("❌ Ошибка сохранения AI результатов")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки фонового батча: {str(e)}")
            return False

    async def _get_pending_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение необработанных постов из Backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/posts/unprocessed",
                    params={"limit": limit}
                ) as response:
                    if response.status == 200:
                        posts = await response.json()
                        return posts
                    else:
                        logger.error(f"❌ Ошибка получения постов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении постов: {str(e)}")
            return []

    async def _save_ai_results(self, ai_results: List[Dict[str, Any]]) -> bool:
        """Сохранение AI результатов в Backend API (ИСПРАВЛЕННЫЙ ФОРМАТ)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/ai/results/batch",
                    json=ai_results,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 201:
                        saved_results = await response.json()
                        logger.info(f"✅ Сохранено {len(saved_results)} AI результатов")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка сохранения: HTTP {response.status}")
                        logger.error(f"   Детали: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Исключение при сохранении: {str(e)}")
            return False

    async def _process_new_posts(self, post_ids: List[int], channel_ids: List[int]) -> bool:
        """Обработка новых постов"""
        logger.info(f"🔄 Обработка новых постов: {len(post_ids)} постов из каналов {channel_ids}")
        # Заглушка
        return True

    async def _reprocess_channels(self, channel_ids: List[int]) -> bool:
        """Переобработка каналов"""
        logger.info(f"🔄 Переобработка каналов: {channel_ids}")
        # Заглушка
        return True

    async def report_orchestrator_status(self, status: str, details: Dict[str, Any] = None):
        """Отчет о статусе AI Orchestrator в Backend API"""
        logger.debug(f"📡 Статус: {status}, детали: {details}")

    async def trigger_processing(self):
        """Реактивный запуск обработки (для вызова из Backend API)"""
        logger.info("⚡ Trigger Processing - реактивный запуск обработки")
        
        # Создаем фоновую задачу
        task = AITask(
            task_type=AITaskType.BACKGROUND_PROCESSING,
            priority=AITaskPriority.NORMAL,
            metadata={'trigger': 'api_request'}
        )
        
        await self._add_task_to_queue(task)
        
        # Если фоновый обработчик не запущен - запускаем
        if not self.background_worker_running:
            await self._start_background_worker()
        
        return {"success": True, "message": "AI обработка запущена успешно"}

    async def run_single_batch(self):
        """Запуск одного батча обработки (для тестирования)"""
        logger.info("🧪 Запуск тестового батча AI Orchestrator v2.0")
        
        # Создаем фоновую задачу
        task = AITask(
            task_type=AITaskType.BACKGROUND_PROCESSING,
            priority=AITaskPriority.NORMAL,
            metadata={'trigger': 'single_batch_test'}
        )
        
        # Обрабатываем напрямую
        success = await self._process_task(task)
        
        if success:
            logger.info("🎉 Тестовый батч завершен успешно!")
        else:
            logger.error("💥 Тестовый батч завершен с ошибками")
        
        return success


async def main():
    """Главная функция для запуска AI Orchestrator v2.0"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Orchestrator v2.0 Event-Driven Architecture")
    parser.add_argument("--mode", choices=["continuous", "single"], default="single",
                       help="Режим работы: continuous (непрерывно) или single (один батч)")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                       help="URL Backend API")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Размер батча для обработки")
    
    args = parser.parse_args()
    
    # Создание AI Orchestrator v2.0
    orchestrator = AIOrchestratorV2(
        backend_url=args.backend_url,
        batch_size=args.batch_size
    )
    
    # Запуск в выбранном режиме
    if args.mode == "continuous":
        await orchestrator.run_continuous()
    else:
        await orchestrator.run_single_batch()

if __name__ == "__main__":
    asyncio.run(main()) 