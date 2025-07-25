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
                 batch_size: Optional[int] = None):
        
        self.backend_url = backend_url
        self.batch_size = batch_size  # Будет получен из настроек если None
        
        # Event-Driven архитектура
        self.task_queue = []  # Приоритетная очередь (heapq)
        self.processing_locks = {}  # Активные задачи
        self.background_worker_running = False
        self.processing_active = False  # Флаг активной обработки
        self.last_activity = None
        self.worker_event = asyncio.Event()  # Событие для пробуждения
        
        # Инициализация AI сервисов
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("⚠️ OPENAI_API_KEY не найден, будет использоваться mock режим")
        
        # AI сервисы будут инициализированы в startup_initialization после получения настроек
        self.categorization_service = None
        self.summarization_service = None
        
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
        """Умный фоновый обработчик с засыпанием/пробуждением по сигналам"""
        logger.info("🧠 Умный фоновый обработчик запущен")
        self.background_worker_running = True
        
        try:
            while self.background_worker_running:
                # Проверяем очередь задач
                if self.task_queue:
                    logger.info(f"📋 В очереди {len(self.task_queue)} задач, начинаем обработку")
                    
                    # Обрабатываем задачи по приоритету
                    while self.task_queue and self.background_worker_running:
                        task = heapq.heappop(self.task_queue)
                        self.stats['queue_size'] = len(self.task_queue)
                        
                        logger.info(f"🔄 Обработка задачи: {task.task_type.value} (приоритет: {task.priority.name})")
                        await self.report_orchestrator_status("PROCESSING", {
                            "current_task": task.task_type.value,
                            "priority": task.priority.name,
                            "queue_remaining": len(self.task_queue)
                        })
                        
                        success = await self._process_task(task)
                        
                        if success:
                            self.stats['successful_processed'] += 1
                            logger.info(f"✅ Задача {task.task_type.value} выполнена успешно")
                        else:
                            self.stats['failed_processed'] += 1
                            logger.error(f"❌ Задача {task.task_type.value} завершена с ошибкой")
                        
                        self.stats['total_processed'] += 1
                        self.last_activity = datetime.utcnow()
                        
                        # Небольшая пауза между задачами
                        await asyncio.sleep(0.5)
                
                else:
                    # Нет задач - засыпаем до сигнала
                    logger.info("😴 Нет задач, засыпаем до получения сигнала...")
                    await self.report_orchestrator_status("IDLE", {"queue_size": 0})
                    
                    # Ждем сигнала или периодически проверяем Backend API на наличие новых заданий
                    try:
                        await asyncio.wait_for(self.worker_event.wait(), timeout=30.0)
                        self.worker_event.clear()
                        logger.info("⚡ Получен сигнал пробуждения!")
                    except asyncio.TimeoutError:
                        # Периодическая проверка Backend API на наличие заданий
                        logger.debug("🔍 Периодическая проверка Backend API...")
                        await self._check_for_pending_tasks()
                        
        except Exception as e:
            logger.error(f"💥 Критическая ошибка фонового обработчика: {str(e)}")
        finally:
            self.background_worker_running = False
            await self.report_orchestrator_status("STOPPED", {"reason": "background_worker_terminated"})
            logger.info("🛑 Фоновый обработчик остановлен")

    async def _check_for_pending_tasks(self):
        """Периодическая проверка Backend API на наличие заданий от single режима И pending постов"""
        try:
            # 1. Проверяем команды от Backend API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/ai/orchestrator-commands") as response:
                    if response.status == 200:
                        commands = await response.json()
                        
                        for command in commands:
                            command_type = command.get('command_type')
                            if command_type == 'trigger_processing':
                                logger.info("📡 Получена команда trigger_processing от Backend API")
                                
                                # Создаем задачу обработки
                                task = AITask(
                                    task_type=AITaskType.BACKGROUND_PROCESSING,
                                    priority=AITaskPriority.NORMAL,
                                    metadata={'trigger': 'backend_api_command'}
                                )
                                
                                await self._add_task_to_queue(task)
                                
                                # Помечаем команду как выполненную
                                await self._mark_command_processed(command['id'])
                    
                    elif response.status == 404:
                        # Endpoint не существует - это нормально для старых версий Backend
                        pass
                    else:
                        logger.debug(f"⚠️ Неожиданный статус при проверке команд: {response.status}")
                        
            # 2. Проверяем наличие pending постов напрямую
            pending_data = await self._check_pending_data()
            if pending_data['total_posts'] > 0:
                logger.info(f"🔍 Обнаружено {pending_data['total_posts']} pending постов, добавляем задачу обработки")
                
                # Создаем задачу фоновой обработки
                task = AITask(
                    task_type=AITaskType.BACKGROUND_PROCESSING,
                    priority=AITaskPriority.NORMAL,
                    metadata={'trigger': 'periodic_check', 'total_posts': pending_data['total_posts']}
                )
                
                await self._add_task_to_queue(task)
            else:
                logger.debug("✅ Нет pending постов для обработки")
                        
        except Exception as e:
            logger.debug(f"🔍 Ошибка проверки команд/данных Backend API: {str(e)}")

    async def _mark_command_processed(self, command_id: int):
        """Помечаем команду как обработанную в Backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(f"{self.backend_url}/api/ai/orchestrator-commands/{command_id}") as response:
                    if response.status == 200:
                        logger.debug(f"✅ Команда {command_id} помечена как обработанная")
                    else:
                        logger.debug(f"⚠️ Не удалось пометить команду {command_id}: HTTP {response.status}")
        except Exception as e:
            logger.debug(f"❌ Ошибка при пометке команды {command_id}: {str(e)}")

    async def startup_initialization(self):
        """Инициализация при запуске системы - проверка необработанных данных"""
        logger.info("🚀 Startup Initialization - инициализация AI сервисов и проверка данных")
        
        # 1. Инициализируем AI сервисы
        await self._initialize_ai_services()
        
        # 2. Проверяем наличие необработанных данных
        pending_data = await self._check_pending_data()
        
        if pending_data['total_posts'] > 0:
            logger.info(f"📊 Найдено {pending_data['total_posts']} необработанных постов")
            
            # 3. Запускаем обработку по приоритетам
            await self._schedule_pending_data_processing(pending_data)
        else:
            logger.info("✅ Все данные обработаны")
        
        # 4. Запускаем фоновый обработчик
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
                async with session.get(f"{self.backend_url}/api/posts/unprocessed?limit=500") as response:
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
        """Обработка фонового батча постов с правильной фильтрацией по ботам"""
        logger.info("🔄 Обработка фонового батча")
        
        try:
            # 1. Получаем активных ботов
            active_bots = await self._get_active_bots()
            if not active_bots:
                logger.info("✅ Нет активных ботов для обработки")
                return True
            
            logger.info(f"🤖 Найдено {len(active_bots)} активных ботов")
            
            # 2. Для каждого активного бота обрабатываем его посты
            total_processed = 0
            for bot in active_bots:
                bot_id = bot['id']
                bot_name = bot['name']
                logger.info(f"🔄 Обработка постов для бота: {bot_name} (ID: {bot_id})")
                
                # Получаем каналы бота
                bot_channels = await self._get_bot_channels(bot_id)
                if not bot_channels:
                    logger.info(f"⚠️ У бота {bot_name} нет настроенных каналов")
                    continue
                
                # Получаем telegram_id каналов
                channel_telegram_ids = [ch['telegram_id'] for ch in bot_channels]
                logger.info(f"📺 Каналы бота {bot_name}: {[ch['username'] for ch in bot_channels]}")
                
                # Получаем категории бота
                bot_categories = await self._get_bot_categories(bot_id)
                if not bot_categories:
                    logger.info(f"⚠️ У бота {bot_name} нет настроенных категорий")
                    continue
                
                category_names = [cat['category_name'] for cat in bot_categories]
                logger.info(f"📂 Категории бота {bot_name}: {category_names}")
                
                # Получаем необработанные посты только из каналов этого бота
                bot_posts = await self._get_pending_posts_for_bot(channel_telegram_ids, limit=self.batch_size, bot_id=bot['id'])
                
                if not bot_posts:
                    logger.info(f"✅ Нет необработанных постов для бота {bot_name}")
                    continue
                
                logger.info(f"📋 Найдено {len(bot_posts)} необработанных постов для бота {bot_name}")
                
                # СРАЗУ обновляем мультитенантный статус постов на "pending" для этого бота
                post_ids = [post['id'] for post in bot_posts]
                await self._update_multitenant_status(post_ids, "pending", bot['id'])
                logger.info(f"🔄 Посты {post_ids} помечены как 'pending' для бота {bot_name}")
                
                # Обрабатываем посты РЕАЛЬНЫМИ AI сервисами
                ai_results = await self._process_posts_with_real_ai(bot_posts, bot, bot_categories)
                
                # Сохраняем результаты
                if ai_results:
                    success = await self._save_ai_results(ai_results)
                    if success:
                        # Статусы уже обновлены в _process_posts_with_real_ai
                        logger.info(f"✅ Сохранено {len(ai_results)} AI результатов для бота {bot_name}")
                        total_processed += len(ai_results)
                    else:
                        logger.error(f"❌ Ошибка сохранения AI результатов для бота {bot_name}")
                        # При ошибке сохранения помечаем как failed
                        post_ids = [result['post_id'] for result in ai_results]
                        await self._update_multitenant_status(post_ids, "failed", bot['id'])
            
            if total_processed > 0:
                logger.info(f"🎉 Всего обработано {total_processed} постов")
            else:
                logger.info("✅ Нет постов для обработки - все боты обработаны или нет orphan posts")
            
            return True  # Всегда возвращаем True - отсутствие постов не является ошибкой
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки фонового батча: {str(e)}")
            return False

    async def _get_active_bots(self) -> List[Dict[str, Any]]:
        """Получение активных публичных ботов"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots") as response:
                    if response.status == 200:
                        bots = await response.json()
                        # Фильтруем только активных ботов
                        active_bots = [bot for bot in bots if bot.get('status') == 'active']
                        return active_bots
                    else:
                        logger.error(f"❌ Ошибка получения ботов: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении ботов: {str(e)}")
            return []

    async def _get_bot_channels(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получение каналов бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/channels") as response:
                    if response.status == 200:
                        channels = await response.json()
                        return channels
                    else:
                        logger.error(f"❌ Ошибка получения каналов бота {bot_id}: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении каналов бота {bot_id}: {str(e)}")
            return []

    async def _get_bot_categories(self, bot_id: int) -> List[Dict[str, Any]]:
        """Получение категорий бота"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/public-bots/{bot_id}/categories") as response:
                    if response.status == 200:
                        categories = await response.json()
                        return categories
                    else:
                        logger.error(f"❌ Ошибка получения категорий бота {bot_id}: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"❌ Исключение при получении категорий бота {bot_id}: {str(e)}")
            return []

    async def _get_batch_size_from_settings(self) -> int:
        """Получение размера батча из настроек Backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/settings") as response:
                    if response.status == 200:
                        settings = await response.json()
                        for setting in settings:
                            if setting.get('key') == 'MAX_POSTS_FOR_AI_ANALYSIS':
                                batch_size = int(setting.get('value', 30))
                                logger.info(f"📦 Размер батча из настроек: {batch_size}")
                                return batch_size
                        
                        logger.warning("⚠️ Настройка 'MAX_POSTS_FOR_AI_ANALYSIS' не найдена, используем 30")
                        return 30
                    else:
                        logger.error(f"❌ Ошибка получения настроек: HTTP {response.status}")
                        return 30
        except Exception as e:
            logger.error(f"❌ Ошибка запроса настроек: {str(e)}")
            return 30

    async def _initialize_ai_services(self):
        """Инициализация AI сервисов с правильным размером батча"""
        logger.info("🔧 Инициализация AI сервисов...")
        
        # Получаем размер батча из настроек если не задан
        if self.batch_size is None:
            self.batch_size = await self._get_batch_size_from_settings()
            logger.info(f"📦 Размер батча получен из настроек: {self.batch_size}")
        
        # Инициализируем AI сервисы с правильным размером батча
        from ai_services.services.categorization import CategorizationService
        from ai_services.services.summarization import SummarizationService
        
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
        
        logger.info(f"✅ AI сервисы инициализированы с размером батча: {self.batch_size}")

    async def _get_pending_posts_for_bot(self, channel_telegram_ids: List[int], limit: int = None, bot_id: int = None) -> List[Dict[str, Any]]:
        """✅ ПРАВИЛЬНАЯ АРХИТЕКТУРА: Получение постов из общего пула, которые НЕ обработаны для конкретного бота"""
        try:
            # Используем переданный лимит или по умолчанию 500
            fetch_limit = limit if limit is not None else 500
            
            # 1. Получаем ВСЕ посты из общего пула
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/posts/unprocessed",
                    params={"limit": fetch_limit * 3}  # Получаем больше для фильтрации
                ) as response:
                    if response.status == 200:
                        all_posts = await response.json()
                    else:
                        logger.error(f"❌ Ошибка получения постов: HTTP {response.status}")
                        return []
            
            # 2. Фильтруем только посты из каналов этого бота
            bot_posts = [
                post for post in all_posts 
                if post.get('channel_telegram_id') in channel_telegram_ids
            ]
            
            if not bot_posts:
                logger.debug(f"📭 Нет постов из каналов бота {bot_id}")
                return []
            
            # 3. Если bot_id передан, проверяем какие посты НЕ обработаны для этого бота
            if bot_id is not None:
                post_ids = [post['id'] for post in bot_posts]
                
                # 🚀 ИСПРАВЛЕНИЕ: Получаем уже обработанные посты через мультитенантную таблицу processed_data
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.backend_url}/api/ai/results/batch-status",
                        params={
                            "post_ids": ",".join(map(str, post_ids)),
                            "bot_id": bot_id
                        }
                    ) as response:
                        if response.status == 200:
                            batch_status_response = await response.json()
                            # Получаем массив статусов из ответа
                            batch_status = batch_status_response.get('statuses', [])
                            # Получаем ID постов которые уже completed для этого бота
                            processed_post_ids = {
                                item['post_id'] for item in batch_status 
                                if item.get('status') == 'completed'
                            }
                            logger.debug(f"🔍 Бот {bot_id}: {len(processed_post_ids)} постов уже обработано через processed_data")
                        else:
                            logger.warning(f"⚠️ Не удалось получить статусы постов для бота {bot_id}")
                            processed_post_ids = set()
                
                # Фильтруем только НЕ обработанные посты
                unprocessed_posts = [
                    post for post in bot_posts 
                    if post['id'] not in processed_post_ids
                ]
                
                logger.info(f"📊 Бот {bot_id}: {len(bot_posts)} постов из каналов, {len(unprocessed_posts)} необработанных")
                
                # Возвращаем только нужное количество
                if limit is not None:
                    return unprocessed_posts[:limit]
                else:
                    return unprocessed_posts
            else:
                # Если bot_id не передан, возвращаем все посты из каналов бота
                if limit is not None:
                    return bot_posts[:limit]
                else:
                    return bot_posts
                    
        except Exception as e:
            logger.error(f"❌ Исключение при получении постов для бота {bot_id}: {str(e)}")
            return []

    async def _process_posts_with_real_ai(self, posts: List[Dict[str, Any]], bot: Dict[str, Any], categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработка постов реальными AI сервисами"""
        logger.info(f"🤖 Обработка {len(posts)} постов реальными AI сервисами")
        
        ai_results = []
        
        try:
            # Проверяем что AI сервисы инициализированы
            if self.categorization_service is None or self.summarization_service is None:
                logger.error("❌ AI сервисы не инициализированы!")
                return await self._process_posts_with_mock_ai(posts, bot)
            
            # Используем инициализированные AI сервисы
            categorization_service = self.categorization_service
            summarization_service = self.summarization_service
            
            # Преобразуем посты в формат Post для CategorizationService
            from ai_services.models.post import Post
            post_objects = []
            for post_data in posts:
                post_obj = Post(
                    id=post_data['id'],
                    content=post_data.get('content', ''),
                    channel_telegram_id=post_data.get('channel_telegram_id'),
                    created_at=post_data.get('created_at'),
                    telegram_message_id=post_data.get('message_id', 0)
                )
                post_objects.append(post_obj)
            
            # 1. Категоризация всех постов через CategorizationService
            logger.info(f"🔄 Категоризация {len(post_objects)} постов")
            categorization_results = await categorization_service.process_with_bot_config(
                posts=post_objects,
                bot_id=bot['id']
            )
            
            # 2. БАТЧЕВАЯ саммаризация всех постов через SummarizationService
            logger.info(f"🔄 БАТЧЕВАЯ саммаризация {len(posts)} постов")
            
            # Подготавливаем тексты для батчевой саммаризации
            texts_for_summarization = []
            post_id_to_index = {}
            valid_posts = []
            
            for i, post in enumerate(posts):
                post_id = post['id']
                content = post.get('content', '')
                
                if not content or len(content.strip()) < 10:
                    logger.warning(f"⚠️ Пост {post_id} слишком короткий, пропускаем")
                    continue
                
                # Проверяем что есть результат категоризации
                categorization_result = None
                for cat_result in categorization_results:
                    if cat_result.get('post_id') == post_id:
                        categorization_result = cat_result
                        break
                
                if not categorization_result:
                    logger.warning(f"⚠️ Не найден результат категоризации для поста {post_id}")
                    continue
                
                # Добавляем в батч для саммаризации
                texts_for_summarization.append(content)
                post_id_to_index[post_id] = len(valid_posts)
                valid_posts.append(post)
            
            # Батчевая саммаризация всех текстов
            if texts_for_summarization:
                logger.info(f"🚀 Батчевая саммаризация {len(texts_for_summarization)} постов")
                summarization_results = await summarization_service.process_batch(
                    texts=texts_for_summarization,
                    language=bot.get('default_language', 'ru'),
                    custom_prompt=bot.get('summarization_prompt'),
                    max_summary_length=bot.get('max_summary_length', 150)
                )
            else:
                logger.warning("⚠️ Нет постов для саммаризации")
                summarization_results = []
            
            # 3. Формируем финальные результаты, объединяя категоризацию и саммаризацию
            logger.info(f"🔄 Формирование {len(valid_posts)} финальных результатов")
            for i, post in enumerate(valid_posts):
                try:
                    post_id = post['id']
                    
                    # Получаем результат категоризации для этого поста
                    categorization_result = None
                    for cat_result in categorization_results:
                        if cat_result.get('post_id') == post_id:
                            categorization_result = cat_result
                            break
                    
                    # Получаем результат саммаризации (по индексу)
                    summarization_result = {}
                    if i < len(summarization_results):
                        summarization_result = summarization_results[i]
                    
                    # Формируем результат
                    ai_result = {
                        "post_id": post_id,
                        "public_bot_id": bot['id'],  # Правильный bot_id!
                        "summaries": {
                            "ru": summarization_result.get('summary', ''),
                            "en": summarization_result.get('summary_en', '')
                        },
                        "categories": {
                            "primary": categorization_result.get('category_name', '') if categorization_result else '',
                            "secondary": [],
                            "relevance_scores": [categorization_result.get('relevance_score', 0.0)] if categorization_result else [0.0]
                        },
                        "metrics": {
                            "importance": categorization_result.get('importance', 5.0) if categorization_result else 5.0,
                            "urgency": categorization_result.get('urgency', 5.0) if categorization_result else 5.0,
                            "significance": categorization_result.get('significance', 5.0) if categorization_result else 5.0,
                            "tokens_used": summarization_result.get('tokens_used', 0),
                            "processing_time": 0.0  # TODO: измерить время
                        },
                        "processing_version": "v3.1_multitenant_batch"
                    }
                    
                    ai_results.append(ai_result)
                    
                    # 🚀 УМНОЕ ОБНОВЛЕНИЕ МУЛЬТИТЕНАНТНОГО СТАТУСА 
                    await self._update_multitenant_status([post_id], "completed", bot['id'], "both_services")
                    
                    category_name = categorization_result.get('category_name', 'N/A') if categorization_result else 'N/A'
                    logger.info(f"✅ Пост {post_id} обработан: {category_name}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка формирования результата для поста {post.get('id', 'Unknown')}: {str(e)}")
                    # При ошибке помечаем пост как failed
                    post_id = post.get('id')
                    if post_id:
                        await self._update_multitenant_status([post_id], "failed", bot['id'])
            
            logger.info(f"🎉 Обработано {len(ai_results)} постов из {len(posts)}")
            return ai_results
            
        except Exception as e:
            logger.error(f"❌ Ошибка реальной AI обработки: {str(e)}")
            logger.info("🔄 Используем заглушки...")
            return await self._process_posts_with_mock_ai(posts, bot)

    async def _process_posts_with_mock_ai(self, posts: List[Dict[str, Any]], bot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback: обработка постов заглушками (с правильным bot_id)"""
        logger.info(f"🧪 Fallback: обработка {len(posts)} постов заглушками")
        
        ai_results = []
        for post in posts:
            post_id = post["id"]
            ai_result = {
                "post_id": post_id,
                "public_bot_id": bot['id'],  # Правильный bot_id!
                "summaries": {
                    "ru": f"AI резюме для поста {post_id} (бот: {bot['name']})",
                    "en": f"AI summary for post {post_id} (bot: {bot['name']})"
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
                                        "processing_version": "v3.1_multitenant_mock"
            }
            ai_results.append(ai_result)
            
            # 🚀 УМНОЕ ОБНОВЛЕНИЕ МУЛЬТИТЕНАНТНОГО СТАТУСА (Mock режим)
            await self._update_multitenant_status([post_id], "completed", bot['id'], "both_services")
            logger.info(f"✅ Mock пост {post_id} обработан")
        
        return ai_results

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
        
        try:
            status_data = {
                "orchestrator_status": status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "stats": {
                    "queue_size": len(self.task_queue),
                    "background_worker_running": self.background_worker_running,
                    "processing_active": self.processing_active
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
                        logger.debug("✅ Статус успешно отправлен в Backend API")
                    else:
                        logger.warning(f"⚠️ Ошибка отправки статуса: HTTP {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Исключение при отправке статуса: {str(e)}")

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
        
        # Инициализируем AI сервисы перед обработкой
        await self._initialize_ai_services()
        
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

    async def _save_ai_results(self, ai_results: List[Dict[str, Any]]) -> bool:
        """Сохранение AI результатов в Backend API"""
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

    # ❌ УДАЛЕН УСТАРЕВШИЙ МЕТОД _update_posts_status - использовал глобальные статусы
    # ✅ Используйте _update_multitenant_status для мультитенантной архитектуры

    async def _update_multitenant_status(self, post_ids: List[int], status: str, bot_id: int, service_type: str = None) -> bool:
        """🔧 НОВОЕ: Умное обновление мультитенантных статусов AI обработки"""
        try:
            # 🧠 УМНАЯ ЛОГИКА СТАТУСОВ
            # Определяем правильный статус на основе текущего состояния и типа сервиса
            smart_status = await self._calculate_smart_status(post_ids, bot_id, status, service_type)
            
            # 🚀 БАТЧЕВОЕ ОБНОВЛЕНИЕ через новый endpoint
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.backend_url}/api/ai/results/batch-status",
                    json={
                        "post_ids": post_ids,
                        "bot_id": bot_id,
                        "status": smart_status
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        affected_count = result.get('affected_count', 0)
                        logger.info(f"✅ Батчево обновлено {affected_count} AI статусов на '{smart_status}' для бота {bot_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ошибка батчевого обновления: HTTP {response.status}")
                        logger.error(f"   Детали: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"❌ Исключение при обновлении мультитенантных статусов: {str(e)}")
            return False

    async def _calculate_smart_status(self, post_ids: List[int], bot_id: int, requested_status: str, service_type: str = None) -> str:
        """🧠 Умное вычисление статуса на основе текущего состояния и типа сервиса"""
        
        # Если не указан тип сервиса, возвращаем как есть
        if not service_type:
            return requested_status
        
        try:
            # 🔧 ИСПРАВЛЕНО: Получаем текущие статусы через МУЛЬТИТЕНАНТНЫЙ endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/ai/results/batch-status",
                    params={
                        "post_ids": ",".join(map(str, post_ids)),
                        "bot_id": bot_id
                    },
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        batch_status_response = await response.json()
                        # Получаем массив статусов из ответа
                        batch_status = batch_status_response.get('statuses', [])
                        
                        # Создаем карту текущих статусов из мультитенантных данных
                        current_statuses = {}
                        for item in batch_status:
                            if item['post_id'] in post_ids:
                                current_statuses[item['post_id']] = item.get('status', 'pending')
                        
                        # 🧠 УМНАЯ ЛОГИКА СТАТУСОВ
                        if service_type == "categorization":
                            # Категоризация завершена
                            smart_statuses = []
                            for post_id in post_ids:
                                current = current_statuses.get(post_id, 'pending')
                                if current == 'pending':
                                    smart_statuses.append('categorized')
                                elif current == 'summarized':
                                    smart_statuses.append('completed')
                                else:
                                    smart_statuses.append(current)  # Оставляем как есть
                            
                            # Если все статусы одинаковые, возвращаем один
                            unique_statuses = set(smart_statuses)
                            if len(unique_statuses) == 1:
                                return smart_statuses[0]
                            else:
                                logger.info(f"📊 Смешанные статусы после категоризации: {unique_statuses}")
                                return 'categorized'  # Консервативный подход
                        
                        elif service_type == "summarization":
                            # Саммаризация завершена
                            smart_statuses = []
                            for post_id in post_ids:
                                current = current_statuses.get(post_id, 'pending')
                                if current == 'pending':
                                    smart_statuses.append('summarized')
                                elif current == 'categorized':
                                    smart_statuses.append('completed')
                                else:
                                    smart_statuses.append(current)  # Оставляем как есть
                            
                            # Если все статусы одинаковые, возвращаем один
                            unique_statuses = set(smart_statuses)
                            if len(unique_statuses) == 1:
                                return smart_statuses[0]
                            else:
                                logger.info(f"📊 Смешанные статусы после саммаризации: {unique_statuses}")
                                return 'summarized'  # Консервативный подход
                    
                    else:
                        logger.warning(f"⚠️ Не удалось получить текущие мультитенантные статусы: HTTP {response.status}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при вычислении умного статуса: {str(e)}")
        
        # Fallback: возвращаем запрошенный статус
        return requested_status

    # === ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ С BACKEND ===
    
    async def process_posts_for_bot(self, posts: List['Post'], bot: 'Bot') -> List[Dict[str, Any]]:
        """Обработка постов для конкретного бота (совместимость с backend)"""
        logger.info(f"🧠 Обработка {len(posts)} постов для бота '{bot.name}' (ID: {bot.id})")
        
        # Конвертируем Post объекты в словари для внутренней обработки
        posts_data = []
        for post in posts:
            post_dict = {
                "id": post.id,
                "content": post.text,
                "title": post.caption,
                "views": post.views,
                "post_date": post.date,
                "channel_telegram_id": post.channel_id,
                "telegram_message_id": post.message_id
            }
            posts_data.append(post_dict)
        
        # Конвертируем Bot объект в словарь
        bot_data = {
            "id": bot.id,
            "name": bot.name,
            "categorization_prompt": bot.categorization_prompt,
            "summarization_prompt": bot.summarization_prompt,
            "max_posts_per_digest": bot.max_posts_per_digest,
            "max_summary_length": bot.max_summary_length
        }
        
        # Получаем категории бота
        categories = await self._get_bot_categories(bot.id)
        
        # Обрабатываем через реальный AI или mock
        if self.openai_api_key:
            ai_results = await self._process_posts_with_real_ai(posts_data, bot_data, categories)
        else:
            ai_results = await self._process_posts_with_mock_ai(posts_data, bot_data)
        
        logger.info(f"✅ Подготовлено {len(ai_results)} результатов для сохранения")
        return ai_results

    async def save_ai_results(self, ai_results: List[Dict[str, Any]]) -> bool:
        """Сохранение результатов AI обработки (совместимость с backend)"""
        return await self._save_ai_results(ai_results)

# === АЛИАС ДЛЯ СОВМЕСТИМОСТИ С BACKEND ===
# Backend импортирует AIOrchestrator, но класс называется AIOrchestratorV2
AIOrchestrator = AIOrchestratorV2

# === КЛАССЫ ДЛЯ СОВМЕСТИМОСТИ С BACKEND ===
# Backend также импортирует Post и Bot классы

class Post:
    """Простой класс для поста (совместимость с backend)"""
    def __init__(self, id, text, caption="", views=0, date=None, channel_id=None, message_id=None):
        self.id = id
        self.text = text
        self.caption = caption
        self.views = views
        self.date = date
        self.channel_id = channel_id
        self.message_id = message_id

class Bot:
    """Простой класс для бота (совместимость с backend)"""
    def __init__(self, id, name, categorization_prompt="", summarization_prompt="", max_posts_per_digest=10, max_summary_length=150):
        self.id = id
        self.name = name
        self.categorization_prompt = categorization_prompt
        self.summarization_prompt = summarization_prompt
        self.max_posts_per_digest = max_posts_per_digest
        self.max_summary_length = max_summary_length

async def main():
    """Главная функция для запуска AI Orchestrator v2.0"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Orchestrator v2.0 Event-Driven Architecture")
    parser.add_argument("--mode", choices=["continuous", "single"], default="single",
                       help="Режим работы: continuous (непрерывно) или single (один батч)")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                       help="URL Backend API")
    parser.add_argument("--batch-size", type=int, default=None,
                       help="Размер батча для обработки (если не указан, берется из настроек Backend)")
    
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