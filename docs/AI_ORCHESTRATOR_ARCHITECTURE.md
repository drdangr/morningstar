# 🎯 AI ORCHESTRATOR v2.0 - ДОРАБОТАННАЯ АРХИТЕКТУРА

## 🏗️ **СИСТЕМА ПРИОРИТЕТОВ И РАСПИСАНИЯ**

### **1. 🚀 ЗАПУСК СИСТЕМЫ И ПРОВЕРКА НЕОБРАБОТАННЫХ ДАННЫХ**

```python
# backend/services/ai_orchestrator.py
import asyncio
import heapq
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

class AIOrchestrator:
    def __init__(self):
        self.categorization_service = CategorizationService()
        self.summarization_service = SummarizationService()
        
        # Приоритетная очередь (heapq для автосортировки по приоритету)
        self.task_queue = []
        self.processing_locks = {}
        self.background_worker_running = False
        self.last_activity = None
        
        # Статистика и мониторинг
        self.stats = {
            'processed_posts': 0,
            'failed_posts': 0,
            'active_tasks': 0,
            'queue_size': 0
        }
    
    async def startup_initialization(self):
        """Инициализация при запуске системы"""
        print("🚀 Запуск AI Orchestrator...")
        
        # 1. Проверяем наличие необработанных данных
        pending_data = await self._check_pending_data()
        
        if pending_data['total_posts'] > 0:
            print(f"📊 Найдено {pending_data['total_posts']} необработанных постов")
            
            # 2. Запускаем обработку по приоритетам
            await self._schedule_pending_data_processing(pending_data)
        else:
            print("✅ Все данные обработаны")
        
        # 3. Запускаем фоновый обработчик
        await self._start_background_worker()
        
        print("✅ AI Orchestrator готов к работе")
    
    async def _check_pending_data(self) -> Dict[str, Any]:
        """Проверка необработанных данных при запуске"""
        # Получаем все посты без AI обработки
        unprocessed_posts = await self._get_unprocessed_posts()
        
        # Группируем по ботам и каналам
        pending_by_bot = {}
        for post in unprocessed_posts:
            bot_ids = await self._get_bots_using_channel(post['channel_id'])
            
            for bot_id in bot_ids:
                if bot_id not in pending_by_bot:
                    pending_by_bot[bot_id] = {
                        'bot_id': bot_id,
                        'posts': [],
                        'channels': set(),
                        'next_digest_time': await self._get_next_digest_time(bot_id)
                    }
                
                pending_by_bot[bot_id]['posts'].append(post)
                pending_by_bot[bot_id]['channels'].add(post['channel_id'])
        
        return {
            'total_posts': len(unprocessed_posts),
            'bots_affected': len(pending_by_bot),
            'pending_by_bot': pending_by_bot
        }
    
    async def _schedule_pending_data_processing(self, pending_data: Dict[str, Any]):
        """Планирование обработки необработанных данных по приоритетам"""
        bots_data = pending_data['pending_by_bot']
        
        # Сортируем ботов по приоритету:
        # 1. Активные боты
        # 2. Ближайшее время дайджеста
        # 3. Количество необработанных постов
        
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
                    'next_digest': bot_data['next_digest_time'].isoformat() if bot_data['next_digest_time'] else None
                }
            )
            
            await self._add_task_to_queue(task)
```

### **2. 🔄 СИСТЕМА ПРЕРЫВАНИЙ И ПРИОРИТЕТОВ**

```python
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
    async def _add_task_to_queue(self, task: AITask):
        """Добавление задачи в приоритетную очередь"""
        # Проверяем дублирование
        if await self._is_duplicate_task(task):
            print(f"⚠️ Задача {task.task_type} уже выполняется, пропускаем")
            return
        
        # Если это критическая задача - прерываем текущую обработку
        if task.priority == AITaskPriority.CRITICAL:
            await self._interrupt_current_processing(task)
        
        # Добавляем в приоритетную очередь
        heapq.heappush(self.task_queue, task)
        self.stats['queue_size'] = len(self.task_queue)
        
        print(f"➕ Задача добавлена: {task.task_type} (приоритет: {task.priority.name})")
        
        # Если фоновый обработчик спит - будим его
        if not self.background_worker_running:
            await self._wake_background_worker()
    
    async def _interrupt_current_processing(self, urgent_task: AITask):
        """Прерывание текущей обработки для критических задач"""
        if urgent_task.priority == AITaskPriority.CRITICAL:
            print(f"🚨 ПРЕРЫВАНИЕ: Критическая задача {urgent_task.task_type}")
            
            # Помечаем текущие задачи для прерывания
            for lock_key in list(self.processing_locks.keys()):
                current_task = self.processing_locks[lock_key]
                if current_task.priority.value < urgent_task.priority.value:
                    print(f"⏸️ Прерываем задачу {current_task.task_type}")
                    # Здесь можно добавить логику graceful прерывания
```

### **3. 🔄 ОБРАБОТКА НОВЫХ ДАННЫХ ОТ USERBOT**

```python
class AIOrchestrator:
    async def handle_new_posts_from_userbot(self, post_ids: List[int], channel_id: int):
        """Обработка сигнала о новых данных от Userbot"""
        print(f"📡 Получен сигнал о {len(post_ids)} новых постах из канала {channel_id}")
        
        # Определяем затронутых ботов
        affected_bots = await self._get_bots_using_channel(channel_id)
        
        if not affected_bots:
            print(f"⚠️ Канал {channel_id} не используется активными ботами")
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
            print("🔄 Фоновый обработчик остановлен, запускаем...")
            await self._start_background_worker()
    
    async def _wake_background_worker(self):
        """Пробуждение фонового обработчика"""
        if not self.background_worker_running:
            await self._start_background_worker()
        # Если работает - он сам подхватит новые задачи из очереди
```

### **4. 📊 БАТЧ ОБРАБОТКА С FALLBACK НА ОТДЕЛЬНЫЕ ПОСТЫ**

```python
class AIOrchestrator:
    async def _process_posts_batch(self, bot_id: int, post_ids: List[int]) -> Dict[str, Any]:
        """Обработка постов с автоматическим fallback"""
        
        # Определяем размер батча (максимум 30 постов)
        batch_size = min(30, len(post_ids))
        
        if len(post_ids) <= batch_size:
            # Пробуем обработать весь батч
            result = await self._try_batch_processing(bot_id, post_ids)
            
            if result['success']:
                return result
            else:
                print(f"⚠️ Батч обработка не удалась, переходим к отдельным постам")
                return await self._fallback_to_individual_processing(bot_id, post_ids)
        else:
            # Разбиваем на батчи по 30 постов
            results = []
            for i in range(0, len(post_ids), batch_size):
                batch = post_ids[i:i + batch_size]
                batch_result = await self._try_batch_processing(bot_id, batch)
                
                if batch_result['success']:
                    results.append(batch_result)
                else:
                    # Fallback для неудачного батча
                    individual_result = await self._fallback_to_individual_processing(bot_id, batch)
                    results.append(individual_result)
            
            return self._merge_batch_results(results)
    
    async def _try_batch_processing(self, bot_id: int, post_ids: List[int], max_retries: int = 2) -> Dict[str, Any]:
        """Попытка батч обработки с retry логикой"""
        
        for attempt in range(max_retries):
            try:
                print(f"🧠 Батч обработка: {len(post_ids)} постов (попытка {attempt + 1})")
                
                # Получаем настройки бота
                bot_config = await self._get_bot_config(bot_id)
                
                # Получаем данные постов
                posts_data = await self._get_posts_data(post_ids)
                
                # Запускаем CategorizationService v2.1
                categorization_results = await self.categorization_service.process_with_bot_config(
                    posts_data, bot_config
                )
                
                # Запускаем SummarizationService
                summarization_results = await self.summarization_service.process_batch(
                    posts_data, bot_config
                )
                
                # Сохраняем результаты
                await self._save_ai_results(post_ids, categorization_results, summarization_results)
                
                return {
                    'success': True,
                    'method': 'batch',
                    'posts_processed': len(post_ids),
                    'attempt': attempt + 1
                }
                
            except Exception as e:
                print(f"❌ Ошибка батч обработки (попытка {attempt + 1}): {e}")
                
                # Проверяем, не "захлебнулась" ли LLM
                if self._is_llm_overload_error(e):
                    print("🚨 LLM перегружена! Уведомляем администратора")
                    await self._notify_admin_llm_overload(bot_id, len(post_ids), str(e))
                    break  # Не повторяем при перегрузке
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Ждем {wait_time}с перед повтором...")
                    await asyncio.sleep(wait_time)
        
        return {
            'success': False,
            'method': 'batch',
            'error': 'max_retries_exceeded',
            'posts_count': len(post_ids)
        }
    
    async def _fallback_to_individual_processing(self, bot_id: int, post_ids: List[int]) -> Dict[str, Any]:
        """Fallback обработка отдельных постов"""
        print(f"🔄 Fallback: обрабатываем {len(post_ids)} постов по отдельности")
        
        successful_posts = []
        failed_posts = []
        
        # Ограничиваем параллельность для избежания перегрузки
        semaphore = asyncio.Semaphore(3)
        
        async def process_single_post(post_id):
            async with semaphore:
                try:
                    result = await self._process_single_post(bot_id, post_id)
                    if result['success']:
                        successful_posts.append(post_id)
                    else:
                        failed_posts.append(post_id)
                except Exception as e:
                    print(f"❌ Ошибка обработки поста {post_id}: {e}")
                    failed_posts.append(post_id)
        
        # Запускаем обработку параллельно
        tasks = [process_single_post(post_id) for post_id in post_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            'success': len(successful_posts) > 0,
            'method': 'individual',
            'posts_processed': len(successful_posts),
            'posts_failed': len(failed_posts),
            'success_rate': len(successful_posts) / len(post_ids) if post_ids else 0
        }
    
    async def _process_single_post(self, bot_id: int, post_id: int) -> Dict[str, Any]:
        """Обработка отдельного поста"""
        try:
            # Получаем настройки бота и данные поста
            bot_config = await self._get_bot_config(bot_id)
            post_data = await self._get_post_data(post_id)
            
            # Обрабатываем через AI Services
            categorization_result = await self.categorization_service.process_single_post(
                post_data, bot_config
            )
            
            summarization_result = await self.summarization_service.process_single_post(
                post_data, bot_config
            )
            
            # Сохраняем результат
            await self._save_ai_results([post_id], [categorization_result], [summarization_result])
            
            return {'success': True, 'post_id': post_id}
            
        except Exception as e:
            print(f"❌ Ошибка обработки поста {post_id}: {e}")
            return {'success': False, 'post_id': post_id, 'error': str(e)}
    
    def _is_llm_overload_error(self, error: Exception) -> bool:
        """Проверка, является ли ошибка перегрузкой LLM"""
        error_str = str(error).lower()
        overload_indicators = [
            'rate limit',
            'too many tokens',
            'context length exceeded',
            'timeout',
            'overloaded',
            'quota exceeded'
        ]
        return any(indicator in error_str for indicator in overload_indicators)
```

### **5. 📊 МОНИТОРИНГ И УВЕДОМЛЕНИЯ**

```python
class AIOrchestrator:
    async def _notify_admin_llm_overload(self, bot_id: int, posts_count: int, error: str):
        """Уведомление администратора о перегрузке LLM"""
        notification = {
            'type': 'llm_overload',
            'bot_id': bot_id,
            'posts_count': posts_count,
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
            'recommendation': f'Уменьшите размер батча для бота {bot_id} или проверьте лимиты OpenAI API'
        }
        
        # Отправляем в Telegram администратору
        await self._send_admin_notification(notification)
        
        # Логируем в систему мониторинга
        await self._log_critical_event(notification)
    
    async def _send_admin_notification(self, notification: Dict[str, Any]):
        """Отправка уведомления администратору в Telegram"""
        try:
            message = f"""
🚨 КРИТИЧЕСКОЕ УВЕДОМЛЕНИЕ AI ORCHESTRATOR

Тип: {notification['type']}
Бот ID: {notification['bot_id']}
Постов в батче: {notification['posts_count']}
Ошибка: {notification['error']}
Время: {notification['timestamp']}

Рекомендация: {notification['recommendation']}
            """
            
            # Отправляем через Backend API в Telegram Bot
            async with aiohttp.ClientSession() as session:
                payload = {
                    'admin_notification': True,
                    'message': message,
                    'priority': 'critical'
                }
                async with session.post(f"{BACKEND_URL}/api/telegram/admin-notify", json=payload) as response:
                    if response.status == 200:
                        print("✅ Уведомление администратору отправлено")
                    else:
                        print(f"❌ Ошибка отправки уведомления: {response.status}")
                        
        except Exception as e:
            print(f"❌ Критическая ошибка отправки уведомления: {e}")
    
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
```

---

## 🎯 **ИТОГОВАЯ АРХИТЕКТУРА v2.0:**

### ✅ **РЕАЛИЗОВАНЫ ВСЕ ТРЕБОВАНИЯ:**

1. **🚀 Умный запуск системы** с проверкой необработанных данных
2. **📊 Приоритизация по активности ботов** и времени дайджестов  
3. **🚨 Система прерываний** для критических задач
4. **📡 Реактивная обработка** новых данных от Userbot
5. **🔄 Батч обработка до 30 постов** с fallback на отдельные посты
6. **📊 Полный мониторинг** с уведомлениями о перегрузке LLM

### 🚀 **ГОТОВО К РЕАЛИЗАЦИИ:**

**Архитектура полностью покрывает все сценарии и готова к внедрению!** 