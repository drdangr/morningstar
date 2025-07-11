# 📋 ПЛАН МИГРАЦИИ AI СЕРВИСОВ НА CELERY (Local-First Approach)

## 1. 📝 ОПИСАНИЕ

Миграция существующей системы AI обработки постов с custom AI Orchestrator v5 на Celery - промышленный стандарт для распределенной обработки задач в Python экосистеме.

**Важно:** План адаптирован под local-first разработку без Docker. Контейнеризация будет выполнена после полной отладки и стабилизации.

**Текущая архитектура:**

- `ai_services/orchestrator_v5_parallel.py` - custom event-driven orchestrator с AsyncIO
- `CategorizationService` и `SummarizationService` - AI сервисы для обработки
- Backend API запускает orchestrator через `subprocess.Popen()`
- Boolean flags (`is_categorized`, `is_summarized`) для tracking состояния

**Целевая архитектура:**

- Celery workers для параллельной обработки задач
- Redis как message broker (локальная установка)
- Flower для мониторинга в реальном времени
- Backend API публикует задачи в очередь без subprocess

## 2. 🎯 ОБОСНОВАНИЕ

### Решаемые проблемы:

**1. Проблема subprocess.PIPE** ✅

- **Было:** Зависание после ~20 задач из-за заполнения буфера
- **Станет:** Celery workers независимы от родительского процесса

**2. Последовательная обработка вместо параллельной** ✅

- **Было:** Категоризация → Саммаризация последовательно
- **Станет:** Настоящая параллельность с отдельными worker pools

**3. Батчевая обработка не работает** ✅

- **Было:** LLM игнорирует промпты в batch режиме
- **Станет:** Динамическое разбиение на оптимальные батчи

**4. Сложность масштабирования** ✅

- **Было:** Один процесс orchestrator на все боты
- **Станет:** Горизонтальное масштабирование workers

### Преимущества Celery:

- **Battle-tested** - используется в production тысячами компаний
- **Retry механизмы** - автоматическая обработка сбоев OpenAI API
- **Rate limiting** - встроенное управление лимитами API
- **Monitoring** - Flower dashboard из коробки
- **Persistence** - задачи не теряются при перезапуске

## 3. 📊 ПОШАГОВЫЙ ПЛАН МИГРАЦИИ (LOCAL DEVELOPMENT)

### 🔧 PHASE 1: Local Infrastructure Setup (1-2 дня)

#### Task 1.1: Установка Redis локально

**Подзадачи:**

- [ ] Установить Redis на локальную машину
- [ ] Настроить Redis для персистентности данных
- [ ] Создать скрипт для запуска/остановки Redis
- [ ] Протестировать подключение из Python

**Установка Redis (в зависимости от ОС):**

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# Windows (через WSL2 или Redis for Windows)
# Рекомендую WSL2 для консистентности с production
```

**Конфигурация Redis для разработки:**

```bash
# redis.conf для локальной разработки
port 6379
bind 127.0.0.1
protected-mode yes
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir ./redis-data/
```

**Тестовый скрипт подключения:**

```python
# test_redis_connection.py
import redis

r = redis.Redis(host='localhost', port=6379, db=0)
r.set('test_key', 'Hello Celery!')
value = r.get('test_key')
print(f"Redis working: {value}")
```

**Definition of Done:**

- ✅ Redis запущен локально на порту 6379
- ✅ Тестовый скрипт успешно читает/пишет данные
- ✅ Redis сохраняет данные между перезапусками
- ✅ Есть скрипты start_redis.sh / stop_redis.sh

#### Task 1.2: Установка Celery и зависимостей

**Подзадачи:**

- [ ] Создать отдельный virtual environment для тестирования
- [ ] Установить Celery, Redis, Flower
- [ ] Создать базовую конфигурацию Celery
- [ ] Запустить тестовый worker

**Создание окружения и установка:**

```bash
# Создаем отдельное окружение для изоляции
python -m venv venv_celery
source venv_celery/bin/activate  # Windows: venv_celery\Scripts\activate

# Устанавливаем зависимости
pip install celery[redis]==5.3.4
pip install flower==2.0.1
pip install redis==5.0.1

# Сохраняем зависимости
pip freeze > requirements-celery.txt
```

**Базовая конфигурация Celery:**

```python
# ai_services/celery_app.py
from celery import Celery
import os

# Для локальной разработки используем простую конфигурацию
app = Celery('digest_bot')

app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # Важно для отладки - видим все ошибки сразу
    task_eager_propagates=True,
    task_always_eager=False,  # Переключить в True для синхронной отладки
    
    # Простая сериализация для начала
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Отключаем оптимизации для отладки
    worker_prefetch_multiplier=1,
    task_acks_late=False,
)
```

**Тестовая задача:**

```python
# ai_services/test_tasks.py
from .celery_app import app

@app.task
def test_task(x, y):
    """Простая задача для проверки работы Celery"""
    return x + y

@app.task
def test_long_task(duration):
    """Задача для проверки длительных операций"""
    import time
    time.sleep(duration)
    return f"Slept for {duration} seconds"
```

**Запуск worker для тестирования:**

```bash
# Terminal 1: Запуск worker
cd /path/to/project
celery -A ai_services.celery_app worker --loglevel=debug

# Terminal 2: Запуск Flower (опционально)
celery -A ai_services.celery_app flower

# Terminal 3: Тестирование
python -c "from ai_services.test_tasks import test_task; result = test_task.delay(2, 3); print(result.get())"
```

**Definition of Done:**

- ✅ Celery worker запускается без ошибок
- ✅ Тестовые задачи выполняются успешно
- ✅ Flower доступен на http://localhost:5555
- ✅ Логи показывают детальную информацию

### 🔄 PHASE 2: Task Implementation (3-4 дня)

#### Task 2.1: Создание Celery-совместимых задач

**Подзадачи:**

- [ ] Создать `ai_services/tasks.py` с основными задачами
- [ ] Адаптировать существующие сервисы для работы с Celery
- [ ] Реализовать оптимальное разбиение батчей
- [ ] Добавить обработку ошибок и retry логику
- [ ] Создать вспомогательные функции для работы с API

**Основные задачи с учетом локальной разработки:**

```python
# ai_services/tasks.py
from celery import Task, group, chain
from celery.utils.log import get_task_logger
from .celery_app import app
from .services.categorization import CategorizationService
from .services.summarization import SummarizationService
from .utils.settings_manager import SettingsManager
import requests
import os
from typing import List, Dict, Any

logger = get_task_logger(__name__)

# Для локальной разработки - настраиваем URL backend
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

class BaseAITask(Task):
    """
    Базовый класс для AI задач
    Важно: в локальной разработке не используем connection pooling,
    чтобы легче отлаживать
    """
    def __init__(self):
        self.settings_manager = None
        self.service = None
    
    def __call__(self, *args, **kwargs):
        """Инициализация при каждом вызове для отладки"""
        if self.settings_manager is None:
            self.settings_manager = SettingsManager()
        return self.run(*args, **kwargs)

@app.task(base=BaseAITask, bind=True, name='categorize_posts')
def categorize_posts(self, post_ids: List[int], bot_id: int) -> Dict[str, Any]:
    """
    Категоризация постов для конкретного бота
    
    Args:
        post_ids: Список ID постов из posts_cache
        bot_id: ID публичного бота
        
    Returns:
        Dict с результатами обработки
    """
    logger.info(f"Starting categorization for {len(post_ids)} posts, bot {bot_id}")
    
    try:
        # Получаем посты - используем существующий endpoint
        response = requests.get(
            f"{BACKEND_URL}/api/posts/cache",
            params={"limit": 100}  # Временно, пока нет фильтрации по IDs
        )
        response.raise_for_status()
        
        all_posts = response.json()["items"]
        # Фильтруем нужные посты
        posts = [p for p in all_posts if p["id"] in post_ids]
        
        if not posts:
            logger.warning(f"No posts found for IDs: {post_ids}")
            return {"processed": 0, "bot_id": bot_id, "status": "no_posts"}
        
        # Получаем конфигурацию бота
        bot_response = requests.get(f"{BACKEND_URL}/api/public-bots/{bot_id}")
        bot_response.raise_for_status()
        bot_config = bot_response.json()
        
        # Инициализируем сервис
        if self.service is None:
            self.service = CategorizationService(settings_manager=self.settings_manager)
        
        # Обрабатываем батч
        # ВАЖНО: Здесь мы НЕ используем batch метод, а обрабатываем по одному
        # Это решение проблемы батчевой обработки
        results = []
        for post in posts:
            try:
                result = self.service.process(
                    post, 
                    bot_id,
                    categorization_prompt=bot_config.get("categorization_prompt", "")
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to categorize post {post['id']}: {e}")
                # Продолжаем обработку остальных
                continue
        
        # Сохраняем результаты через API
        if results:
            save_response = requests.put(
                f"{BACKEND_URL}/api/ai/results/batch-status",
                json={
                    "results": results,
                    "bot_id": bot_id,
                    "service": "categorization"
                }
            )
            save_response.raise_for_status()
        
        logger.info(f"Categorized {len(results)} posts for bot {bot_id}")
        return {
            "processed": len(results), 
            "bot_id": bot_id, 
            "status": "success",
            "failed": len(posts) - len(results)
        }
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        # Retry через 60 секунд при проблемах с API
        raise self.retry(exc=e, countdown=60, max_retries=3)
    except Exception as e:
        logger.error(f"Unexpected error in categorization: {e}", exc_info=True)
        # Не делаем retry для неожиданных ошибок - нужно исправлять код
        return {"processed": 0, "bot_id": bot_id, "status": "error", "error": str(e)}

@app.task(bind=True, name='summarize_posts')
def summarize_posts(self, post_ids: List[int], bot_id: int, 
                   categorization_result: Dict = None) -> Dict[str, Any]:
    """
    Саммаризация постов
    
    Важно: эта задача может вызываться как часть chain после категоризации,
    поэтому принимает результат предыдущей задачи
    """
    logger.info(f"Starting summarization for posts, bot {bot_id}")
    
    # Аналогичная логика, но с учетом is_categorized флага
    # ...
    
    return {"processed": len(post_ids), "bot_id": bot_id, "status": "success"}

@app.task(name='process_bot_digest')
def process_bot_digest(bot_id: int, limit: int = None) -> Dict[str, Any]:
    """
    Главная orchestration задача
    
    Эта задача заменяет твой AI Orchestrator v5
    """
    logger.info(f"Processing digest for bot {bot_id}")
    
    try:
        # Получаем настройки бота
        bot_response = requests.get(f"{BACKEND_URL}/api/public-bots/{bot_id}")
        bot_response.raise_for_status()
        bot_config = bot_response.json()
        
        # Используем настройку из бота или default
        posts_limit = limit or bot_config.get('max_posts_per_digest', 15)
        
        # Получаем необработанные посты
        # TODO: Нужно добавить endpoint для фильтрации по bot_id
        response = requests.get(
            f"{BACKEND_URL}/api/posts/unprocessed",
            params={"limit": posts_limit}
        )
        response.raise_for_status()
        posts = response.json()["items"]
        
        if not posts:
            logger.info(f"No unprocessed posts for bot {bot_id}")
            return {"bot_id": bot_id, "status": "no_posts"}
        
        # КЛЮЧЕВОЕ РЕШЕНИЕ: разбиваем на маленькие батчи
        # Это решает проблему игнорирования промптов в больших батчах
        OPTIMAL_BATCH_SIZE = 3  # Начнем с 3, потом подберем оптимальное
        
        # Создаем цепочки задач
        workflows = []
        for i in range(0, len(posts), OPTIMAL_BATCH_SIZE):
            batch = posts[i:i+OPTIMAL_BATCH_SIZE]
            batch_ids = [p["id"] for p in batch]
            
            # Каждый батч обрабатывается последовательно:
            # категоризация -> саммаризация
            workflow = chain(
                categorize_posts.s(batch_ids, bot_id),
                summarize_posts.s(batch_ids, bot_id)
            )
            workflows.append(workflow)
        
        # Запускаем все цепочки параллельно
        job = group(workflows).apply_async()
        
        return {
            "bot_id": bot_id,
            "status": "processing",
            "total_posts": len(posts),
            "batches": len(workflows),
            "batch_size": OPTIMAL_BATCH_SIZE,
            "job_id": str(job.id) if job.id else None
        }
        
    except Exception as e:
        logger.error(f"Failed to process bot digest: {e}", exc_info=True)
        return {"bot_id": bot_id, "status": "error", "error": str(e)}

# Вспомогательные задачи для отладки
@app.task(name='test_ai_service')
def test_ai_service(service_type: str = 'categorization') -> Dict[str, Any]:
    """Тестовая задача для проверки работы AI сервисов"""
    try:
        if service_type == 'categorization':
            service = CategorizationService()
        else:
            service = SummarizationService()
        
        # Тестовый пост
        test_post = {
            "id": 999,
            "content": "Test content for AI service validation",
            "channel_id": 1
        }
        
        result = service.process(test_post, bot_id=1)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

**Definition of Done:**

- ✅ Задачи импортируются без ошибок
- ✅ Каждая задача логирует свою работу подробно
- ✅ Retry механизм работает только для сетевых ошибок
- ✅ Батчи разбиваются на оптимальный размер

**План тестирования:**

```python
# test_local_tasks.py
import pytest
from ai_services.tasks import categorize_posts, process_bot_digest

def test_categorize_single_batch():
    """Тест категоризации маленького батча"""
    # Запускаем синхронно для отладки
    result = categorize_posts.apply(args=([1, 2, 3], 4)).get()
    
    assert result["status"] == "success"
    assert result["processed"] > 0
    print(f"Processed: {result['processed']} posts")

def test_optimal_batch_size():
    """Тест определения оптимального размера батча"""
    # Тестируем разные размеры
    for batch_size in [1, 3, 5, 10]:
        # Здесь нужно будет замерить время и качество
        pass

def test_error_handling():
    """Тест обработки ошибок"""
    # Тест с несуществующими ID
    result = categorize_posts.apply(args=([99999], 1)).get()
    assert result["status"] in ["no_posts", "error"]
```

#### Task 2.2: Backend API адаптация для локальной разработки

**Подзадачи:**

- [ ] Создать feature flag для включения Celery
- [ ] Добавить endpoints для Celery без удаления старых
- [ ] Реализовать fallback на старый orchestrator
- [ ] Добавить подробное логирование переключений
- [ ] Создать debug endpoints для отладки

**Backend изменения с feature flag:**

```python
# backend/main.py
import os
from typing import Optional

# Feature flag для постепенной миграции
USE_CELERY = os.getenv("USE_CELERY", "false").lower() == "true"
CELERY_DEBUG = os.getenv("CELERY_DEBUG", "true").lower() == "true"

# Только если Celery включен
if USE_CELERY:
    try:
        from celery import Celery
        celery_app = Celery('backend', broker='redis://localhost:6379/0')
        
        # Импортируем задачи чтобы Celery их зарегистрировал
        from ai_services.tasks import process_bot_digest, categorize_posts
        
        CELERY_AVAILABLE = True
    except ImportError:
        logger.warning("Celery not installed, falling back to legacy orchestrator")
        CELERY_AVAILABLE = False
else:
    CELERY_AVAILABLE = False

@app.post("/api/ai/orchestrator-commands")
async def handle_orchestrator_command(command: dict):
    """
    Обновленный endpoint с поддержкой обеих систем
    """
    logger.info(f"Orchestrator command: {command}, USE_CELERY={USE_CELERY}")
    
    if command["action"] == "start_background":
        if USE_CELERY and CELERY_AVAILABLE:
            return await _handle_celery_start(command)
        else:
            return await _handle_legacy_start(command)
    
    # Остальные команды аналогично

async def _handle_celery_start(command: dict):
    """Запуск через Celery"""
    try:
        active_bots = await get_active_bots()
        tasks_created = []
        
        for bot in active_bots:
            # Импортируем здесь чтобы не ломать импорты если Celery не установлен
            from ai_services.tasks import process_bot_digest
            
            # Запускаем асинхронно
            task = process_bot_digest.delay(bot.id)
            tasks_created.append({
                "bot_id": bot.id,
                "task_id": str(task.id),
                "status": "queued"
            })
            
            logger.info(f"Created Celery task {task.id} for bot {bot.id}")
        
        return {
            "status": "started",
            "mode": "celery",
            "tasks": tasks_created,
            "debug": CELERY_DEBUG
        }
    except Exception as e:
        logger.error(f"Celery start failed: {e}")
        if CELERY_DEBUG:
            # В debug режиме падаем с ошибкой
            raise
        else:
            # В production делаем fallback
            logger.warning("Falling back to legacy orchestrator")
            return await _handle_legacy_start(command)

async def _handle_legacy_start(command: dict):
    """Старый способ через subprocess"""
    # Существующий код с subprocess.Popen
    # ...
    return {"status": "started", "mode": "legacy"}

# Debug endpoints для локальной разработки
if CELERY_DEBUG:
    @app.get("/api/debug/celery-status")
    async def debug_celery_status():
        """Подробный статус Celery для отладки"""
        if not CELERY_AVAILABLE:
            return {"error": "Celery not available"}
        
        from celery.task.control import inspect
        i = inspect()
        
        return {
            "active": i.active(),
            "scheduled": i.scheduled(),
            "reserved": i.reserved(),
            "stats": i.stats(),
            "registered": i.registered_tasks(),
            "conf": {
                "broker": celery_app.conf.broker_url,
                "backend": celery_app.conf.result_backend
            }
        }
    
    @app.post("/api/debug/test-celery-task")
    async def test_celery_task(bot_id: int = 1):
        """Запуск тестовой задачи для отладки"""
        from ai_services.tasks import test_ai_service
        
        task = test_ai_service.delay()
        return {
            "task_id": str(task.id),
            "status": "queued",
            "get_result_command": f"celery -A ai_services.celery_app result {task.id}"
        }
```

**Definition of Done:**

- ✅ Backend работает как с Celery, так и без него
- ✅ Feature flag переключает между режимами
- ✅ Debug endpoints доступны в режиме разработки
- ✅ Подробное логирование всех операций

### 📊 PHASE 3: Локальное тестирование и отладка (3-4 дня)

#### Task 3.1: End-to-End тестирование

**Подзадачи:**

- [ ] Создать набор тестовых данных
- [ ] Протестировать обработку 1, 5, 10, 50 постов
- [ ] Сравнить результаты с legacy orchestrator
- [ ] Измерить производительность и найти bottlenecks
- [ ] Оптимизировать размер батчей

**Скрипт для E2E тестирования:**

```python
# test_e2e_celery.py
import time
import requests
from datetime import datetime

class E2ETest:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.results = []
    
    def test_batch_sizes(self):
        """Тестируем разные размеры батчей"""
        for batch_size in [1, 3, 5, 10]:
            print(f"\n--- Testing batch size: {batch_size} ---")
            
            # Устанавливаем размер батча
            os.environ["OPTIMAL_BATCH_SIZE"] = str(batch_size)
            
            # Перезапускаем Celery worker
            self._restart_celery_worker()
            
            # Запускаем обработку
            start_time = time.time()
            response = requests.post(
                f"{self.backend_url}/api/ai/orchestrator-commands",
                json={"action": "start_background"}
            )
            
            # Ждем завершения
            self._wait_for_completion()
            
            duration = time.time() - start_time
            
            # Собираем метрики
            metrics = self._collect_metrics()
            
            self.results.append({
                "batch_size": batch_size,
                "duration": duration,
                "success_rate": metrics["success_rate"],
                "avg_time_per_post": metrics["avg_time_per_post"]
            })
    
    def compare_with_legacy(self):
        """Сравнение с legacy orchestrator"""
        # Тест с legacy
        os.environ["USE_CELERY"] = "false"
        legacy_result = self._run_test("legacy")
        
        # Тест с Celery
        os.environ["USE_CELERY"] = "true"
        celery_result = self._run_test("celery")
        
        print("\n=== COMPARISON ===")
        print(f"Legacy: {legacy_result['duration']:.2f}s")
        print(f"Celery: {celery_result['duration']:.2f}s")
        print(f"Speedup: {legacy_result['duration'] / celery_result['duration']:.2f}x")
```

#### Task 3.2: Мониторинг и профилирование

**Подзадачи:**

- [ ] Настроить Flower для локальной разработки
- [ ] Добавить метрики в Prometheus формате
- [ ] Профилировать memory usage
- [ ] Найти оптимальное количество workers
- [ ] Создать dashboard для мониторинга

**Запуск мониторинга:**

```bash
#!/bin/bash
# start_monitoring.sh

# Запуск Redis с мониторингом
redis-cli CONFIG SET latency-monitor-threshold 100
redis-cli --latency

# Запуск Flower с дополнительными опциями
celery -A ai_services.celery_app flower \
    --port=5555 \
    --broker_api=redis://localhost:6379/0 \
    --max_tasks=10000 \
    --persistent=True \
    --db=flower.db

# Мониторинг памяти worker'ов
watch -n 1 'ps aux | grep celery'
```

### 🚀 PHASE 4: Оптимизация и стабилизация (2-3 дня)

#### Task 4.1: Оптимизация производительности

**Подзадачи:**

- [ ] Найти оптимальный BATCH_SIZE на основе тестов
- [ ] Оптимизировать connection pooling для requests
- [ ] Настроить правильные таймауты
- [ ] Оптимизировать сериализацию данных
- [ ] Уменьшить overhead на маленьких батчах

**Оптимизации для production:**

```python
# ai_services/optimizations.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Connection pooling для API calls
session = requests.Session()
retry = Retry(
    total=3,
    read=3,
    connect=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504)
)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Оптимальные настройки найденные тестированием
OPTIMAL_SETTINGS = {
    "batch_size": 5,  # Будет определено тестами
    "worker_concurrency": 4,  # Количество параллельных workers
    "prefetch_multiplier": 1,  # Для длинных задач
    "task_time_limit": 300,  # 5 минут максимум на задачу
    "task_soft_time_limit": 240,  # Warning после 4 минут
}
```

#### Task 4.2: Подготовка к production

**Подзадачи:**

- [ ] Создать production конфигурацию
- [ ] Написать документацию по deployment
- [ ] Создать скрипты для мониторинга
- [ ] Подготовить rollback процедуру
- [ ] Финальное тестирование на production данных

### 🐳 PHASE 5: Docker Integration (после стабилизации)

**Это будет отдельный этап после полной отладки:**

- Создание Dockerfile для Celery workers
- Docker Compose конфигурация
- Настройка сетей и volumes
- Integration тесты в контейнерах

## 4. 📈 МЕТРИКИ УСПЕХА

**Количественные (целевые после оптимизации):**

- ⬇️ Время обработки 100 постов: с ~160 сек до ~40 сек (4x улучшение)
- ⬆️ Параллельность: с 1 процесса до 4-8 workers
- ⬇️ Failure rate: с зависаний до <1% с auto-retry
- ⬆️ Throughput: 500+ постов/час на локальной машине

**Качественные:**

- ✅ Нет зависаний при любом объеме
- ✅ Простота отладки через Flower UI
- ✅ Предсказуемое поведение
- ✅ Легкость добавления новых задач

## 5. 🚨 РИСКИ И МИТИГАЦИЯ

**Риск 1: Проблемы с Redis на Windows**

- **Митигация:** Использовать WSL2 или Docker только для Redis

**Риск 2: Различия в поведении dev/prod**

- **Митигация:** Максимально близкая конфигурация, те же версии библиотек

**Риск 3: Сложность отладки распределенных задач**

- **Митигация:** Синхронный режим для отладки, подробное логирование, Flower UI

## 6. ⏱️ TIMELINE

**Общее время:** 9-12 дней (без Docker)

1. **Phase 1:** Local Infrastructure (1-2 дня)
2. **Phase 2:** Implementation (3-4 дня)
3. **Phase 3:** Testing & Debugging (3-4 дня)
4. **Phase 4:** Optimization (2-3 дня)
5. **Phase 5:** Docker (отдельно, после стабилизации)

**Критический путь:** Нельзя параллелить - каждая фаза зависит от предыдущей