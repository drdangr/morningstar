#!/usr/bin/env python3
"""
AI Orchestrator v2.0 - Event-Driven Architecture
Центральный координатор AI сервисов с приоритетной очередью и реактивной обработкой
"""

import asyncio
import aiohttp
import json
import logging
import os
import sys
import heapq
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

class AIOrchestrator:
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
            logger.warning(f"⚠️ Задача {task.task_type} уже выполняется, пропускаем")
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
                    # Здесь можно добавить логику graceful прерывания

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

    async def _process_task(self, task: AITask) -> bool:
        """Обработка конкретной задачи"""
        try:
            # Добавляем в активные задачи
            lock_key = f"{task.task_type.value}_{task.bot_id}_{task.created_at.timestamp()}"
            self.processing_locks[lock_key] = task
            self.stats['active_tasks'] = len(self.processing_locks)
            
            # Выбираем метод обработки в зависимости от типа задачи
            if task.task_type == AITaskType.STARTUP_PROCESSING:
                success = await self._process_startup_task(task)
            elif task.task_type == AITaskType.NEW_POSTS_PROCESSING:
                success = await self._process_new_posts_task(task)
            elif task.task_type == AITaskType.BACKGROUND_PROCESSING:
                success = await self._process_background_task(task)
            else:
                logger.warning(f"⚠️ Неизвестный тип задачи: {task.task_type.value}")
                success = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки задачи {task.task_type.value}: {str(e)}")
            return False
        finally:
            # Убираем из активных задач
            if lock_key in self.processing_locks:
                del self.processing_locks[lock_key]
            self.stats['active_tasks'] = len(self.processing_locks)

    # === STARTUP INITIALIZATION ===
    
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

    async def _check_pending_data(self) -> Dict[str, Any]:
        """Проверка необработанных данных при запуске"""
        # Получаем все посты без AI обработки
        unprocessed_posts = await self.get_unprocessed_posts(limit=1000)  # Больший лимит для startup
        
        if not unprocessed_posts:
            return {'total_posts': 0, 'bots_affected': 0, 'pending_by_bot': {}}
        
        # Группируем по ботам
        pending_by_bot = {}
        
        # Получаем всех активных ботов
        bots_data = await self.get_public_bots()
        
        for bot_data in bots_data:
            bot_id = bot_data['id']
            bot_channels = await self.get_bot_channels(bot_id)
            
            # Фильтруем посты для этого бота
            bot_posts = [post for post in unprocessed_posts 
                        if post['channel_telegram_id'] in bot_channels]
            
            if bot_posts:
                pending_by_bot[bot_id] = {
                    'bot_id': bot_id,
                    'bot_name': bot_data['name'],
                    'posts': bot_posts,
                    'channels': set(post['channel_telegram_id'] for post in bot_posts),
                    'next_digest_time': await self._get_next_digest_time(bot_id)
                }
        
        return {
            'total_posts': len(unprocessed_posts),
            'bots_affected': len(pending_by_bot),
            'pending_by_bot': pending_by_bot
        }

    async def _schedule_pending_data_processing(self, pending_data: Dict[str, Any]):
        """Планирование обработки необработанных данных по приоритетам"""
        bots_data = pending_data['pending_by_bot']
        
        # Сортируем ботов по приоритету
        sorted_bots = sorted(
            bots_data.values(),
            key=lambda bot: (
                not await self._is_bot_active(bot['bot_id']),  # Активные боты первыми
                bot['next_digest_time'] or datetime.max,       # Ближайшее время дайджеста
                -len(bot['posts'])                             # Больше постов = выше приоритет
            )
        )
        
        for i, bot_data in enumerate(sorted_bots):
            # Определяем приоритет задачи
            if i < 3:  # Первые 3 бота - высокий приоритет
                priority = AITaskPriority.HIGH
            elif bot_data['next_digest_time'] and bot_data['next_digest_time'] < datetime.utcnow() + timedelta(hours=2):
                priority = AITaskPriority.HIGH  # Скоро дайджест
            else:
                priority = AITaskPriority.NORMAL
            
            # Создаем задачу обработки
            task = AITask(
                task_type=AITaskType.STARTUP_PROCESSING,
                priority=priority,
                bot_id=bot_data['bot_id'],
                post_ids=[post['id'] for post in bot_data['posts']],
                metadata={
                    'reason': 'startup_pending_data',
                    'posts_count': len(bot_data['posts']),
                    'channels_count': len(bot_data['channels']),
                    'bot_name': bot_data['bot_name'],
                    'next_digest': bot_data['next_digest_time'].isoformat() if bot_data['next_digest_time'] else None
                }
            )
            
            await self._add_task_to_queue(task)

    # === ОБРАБОТЧИКИ ЗАДАЧ ===
    
    async def _process_startup_task(self, task: AITask) -> bool:
        """Обработка startup задачи"""
        logger.info(f"🚀 Обработка startup задачи для бота {task.bot_id}")
        
        if not task.post_ids:
            return True
        
        # Используем существующую логику batch обработки
        return await self._process_posts_batch_for_bot(task.bot_id, task.post_ids)

    async def _process_new_posts_task(self, task: AITask) -> bool:
        """Обработка новых постов от Userbot"""
        logger.info(f"📡 Обработка новых постов для бота {task.bot_id}")
        
        if not task.post_ids:
            return True
        
        # Новые посты обрабатываем с высоким приоритетом
        return await self._process_posts_batch_for_bot(task.bot_id, task.post_ids)

    async def _process_background_task(self, task: AITask) -> bool:
        """Обработка фоновой задачи"""
        logger.info(f"🔄 Обработка фоновой задачи для бота {task.bot_id}")
        
        # Проверяем есть ли еще необработанные посты для этого бота
        bot_channels = await self.get_bot_channels(task.bot_id)
        if not bot_channels:
            return True
        
        unprocessed_posts = await self.get_unprocessed_posts_for_channels(bot_channels, self.batch_size)
        
        if not unprocessed_posts:
            logger.info(f"✅ Нет необработанных постов для бота {task.bot_id}")
            return True
        
        post_ids = [post['id'] for post in unprocessed_posts]
        return await self._process_posts_batch_for_bot(task.bot_id, post_ids)

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    async def _get_bots_using_channel(self, channel_id: int) -> List[int]:
        """Получить список ботов, использующих данный канал"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/channels/{channel_id}/bots") as response:
                    if response.status == 200:
                        bots = await response.json()
                        return [bot['id'] for bot in bots]
                    else:
                        logger.warning(f"⚠️ Не удалось получить ботов для канала {channel_id}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка получения ботов для канала {channel_id}: {str(e)}")
            return []

    async def _get_next_digest_time(self, bot_id: int) -> Optional[datetime]:
        """Получить время следующего дайджеста для бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}") as response:
                    if response.status == 200:
                        bot_data = await response.json()
                        # Простая логика - берем время из настроек
                        digest_time = bot_data.get('digest_generation_time', '09:00')
                        
                        # Вычисляем следующее время дайджеста
                        now = datetime.utcnow()
                        hour, minute = map(int, digest_time.split(':'))
                        next_digest = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        if next_digest <= now:
                            next_digest += timedelta(days=1)
                        
                        return next_digest
                    else:
                        return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения времени дайджеста для бота {bot_id}: {str(e)}")
            return None

    async def _is_bot_active(self, bot_id: int) -> bool:
        """Проверить активен ли бот"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}") as response:
                    if response.status == 200:
                        bot_data = await response.json()
                        return bot_data.get('status') == 'active'
                    else:
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки статуса бота {bot_id}: {str(e)}")
            return False

    async def _process_posts_batch_for_bot(self, bot_id: int, post_ids: List[int]) -> bool:
        """Обработка батча постов для конкретного бота"""
        try:
            start_time = datetime.utcnow()
            
            # Получаем данные постов
            posts_data = await self._get_posts_data(post_ids)
            if not posts_data:
                logger.warning(f"⚠️ Не удалось получить данные постов: {post_ids}")
                return False
            
            # Конвертируем в объекты
            posts = self.convert_to_post_objects(posts_data)
            
            # Получаем настройки бота
            bot_data = await self._get_bot_data(bot_id)
            if not bot_data:
                logger.error(f"❌ Не удалось получить данные бота {bot_id}")
                return False
            
            bot = self.convert_to_bot_objects([bot_data])[0]
            
            # Обрабатываем через AI сервисы
            ai_results = await self.process_posts_for_bot(posts, bot)
            
            if ai_results:
                # Сохраняем результаты
                success = await self.save_ai_results(ai_results)
                
                if success:
                    processing_time = (datetime.utcnow() - start_time).total_seconds()
                    self.stats['total_processed'] += len(posts)
                    self.stats['processing_time'] = processing_time
                    
                    logger.info(f"✅ Обработано {len(posts)} постов для бота {bot_id} за {processing_time:.2f}с")
                    return True
                else:
                    logger.error(f"❌ Ошибка сохранения результатов для бота {bot_id}")
                    return False
            else:
                logger.warning(f"⚠️ Нет результатов AI обработки для бота {bot_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки батча для бота {bot_id}: {str(e)}")
            return False

    async def _get_posts_data(self, post_ids: List[int]) -> List[Dict[str, Any]]:
        """Получить данные постов по ID"""
        try:
            # Формируем запрос с фильтрацией по ID
            ids_filter = "&".join([f"id={pid}" for pid in post_ids])
            url = f"{self.backend_url}/api/posts/cache?{ids_filter}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        posts = await response.json()
                        return posts
                    else:
                        logger.error(f"❌ Ошибка получения данных постов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении данных постов: {str(e)}")
            return []

    async def _get_bot_data(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные бота по ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ Ошибка получения данных бота {bot_id}: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Исключение при получении данных бота {bot_id}: {str(e)}")
            return None

    # === МЕТОДЫ ИЗ ОРИГИНАЛЬНОГО ORCHESTRATOR ===
    
    async def get_unprocessed_posts_for_channels(self, channel_ids: List[int], limit: int) -> List[Dict[str, Any]]:
        """Получить необработанные посты для конкретных каналов с лимитом"""
        if not channel_ids:
            return []
            
        try:
            # Формируем запрос с фильтрацией по каналам
            channel_filter = "&".join([f"channel_telegram_id={cid}" for cid in channel_ids])
            url = f"{self.backend_url}/api/posts/cache?processing_status=pending&{channel_filter}&limit={limit}&sort_by=post_date&sort_order=desc"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        posts = await response.json()
                        logger.info(f"📥 Получено {len(posts)} необработанных постов для каналов {channel_ids}")
                        return posts
                    else:
                        logger.error(f"❌ Ошибка получения постов для каналов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении постов для каналов: {str(e)}")
            return []

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

    async def get_bot_channels(self, bot_id: int) -> List[int]:
        """Получить список каналов для бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/channels") as response:
                    if response.status == 200:
                        channels = await response.json()
                        channel_ids = [channel['telegram_id'] for channel in channels]
                        logger.debug(f"📺 Бот {bot_id} использует каналы: {channel_ids}")
                        return channel_ids
                    else:
                        logger.warning(f"⚠️ Не удалось получить каналы для бота {bot_id}: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Ошибка получения каналов для бота {bot_id}: {str(e)}")
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
        
        for i, post in enumerate(posts):
            try:
                if i < len(categorization_results):
                    result = categorization_results[i]
                    
                    # Формируем результат для сохранения
                    ai_result = {
                        "post_id": post.id,
                        "public_bot_id": bot.id,
                        "summaries": result.get("summaries", {}),
                        "categories": result.get("categories", {}),
                        "metrics": result.get("metrics", {}),
                        "processing_version": "v2.0"
                    }
                    
                    results.append(ai_result)
                else:
                    logger.warning(f"⚠️ Нет результата категоризации для поста {post.id}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки результата для поста {post.id}: {str(e)}")
        
        logger.info(f"✅ Подготовлено {len(results)} результатов для сохранения")
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
    
    async def report_orchestrator_status(self, status: str, details: Dict[str, Any] = None):
        """Отчет о статусе AI Orchestrator в Backend API"""
        try:
            status_data = {
                "orchestrator_status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "stats": self.stats.copy(),
                "details": details or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/ai/orchestrator-status",
                    json=status_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 201]:
                        logger.debug(f"📡 Статус '{status}' отправлен в Backend API")
                    else:
                        logger.warning(f"⚠️ Не удалось отправить статус: HTTP {response.status}")
                        
        except Exception as e:
            logger.debug(f"🔇 Не удалось отправить статус в Backend API: {str(e)}")
            # Не критично, продолжаем работу

    # === ПУБЛИЧНЫЕ API МЕТОДЫ ===
    
    async def trigger_processing(self):
        """Реактивный запуск обработки (для вызова из Backend API)"""
        logger.info("⚡ Trigger Processing - реактивный запуск обработки")
        
        try:
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
            
        except Exception as e:
            logger.error(f"❌ Исключение при реактивной обработке: {str(e)}")
            return {"success": False, "message": f"Исключение: {str(e)}"}

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Получение статистики для мониторинга"""
        return {
            'orchestrator_status': 'running' if self.background_worker_running else 'stopped',
            'queue_size': len(self.task_queue),
            'active_tasks': len(self.processing_locks),
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'stats': self.stats,
            'current_tasks': [
                {
                    'task_type': task.task_type.value,
                    'priority': task.priority.name,
                    'bot_id': task.bot_id,
                    'created_at': task.created_at.isoformat()
                }
                for task in list(self.task_queue)[:10]  # Первые 10 задач
            ],
            'processing_locks': list(self.processing_locks.keys())
        }

    async def stop_background_worker(self):
        """Остановка фонового обработчика"""
        logger.info("🛑 Остановка фонового обработчика")
        self.background_worker_running = False
        self.worker_event.set()  # Будим чтобы он завершился

    # === РЕЖИМЫ ЗАПУСКА ===
    
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
    orchestrator = AIOrchestrator(
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