"""
Unified Celery App для AI Services в Docker контейнере
"""

import os
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
import redis
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация Redis и Backend
REDIS_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
# Backend URL для AI Tasks (используется в tasks.py)
# BACKEND_INTERNAL_URL используется в tasks.py как BACKEND_URL

# Создание Celery app
app = Celery('ai_services')

# Конфигурация Celery
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=RESULT_BACKEND,
    
    # Настройки задач
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Настройки worker
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Настройки результатов
    result_expires=3600,  # 1 час
    
    # Настройки очередей - используем правильные имена задач
    task_routes={
        'tasks.categorize_post': {'queue': 'categorization'},
        'tasks.summarize_posts': {'queue': 'summarization'},
        'tasks.process_digest': {'queue': 'processing'},
        'tasks.test_openai_connection': {'queue': 'testing'},
        'tasks.trigger_ai_processing': {'queue': 'orchestration'},
        'tasks.process_bot_digest': {'queue': 'processing'},
        'tasks.check_for_new_posts': {'queue': 'monitoring'},  # Новая очередь для мониторинга
    },
    
    # Celery Beat конфигурация для автоматических задач
    beat_schedule={
        'auto-check-new-posts': {
            'task': 'tasks.check_for_new_posts',
            'schedule': 30.0,  # Каждые 30 секунд
            'options': {
                'queue': 'monitoring',
                'priority': 5,  # Низкий приоритет, не мешает основной обработке
            }
        },
    },
    beat_scheduler='celery.beat:PersistentScheduler',  # Сохраняет расписание в файл
    
    # Настройки безопасности
    worker_disable_rate_limits=True,
    task_ignore_result=False,
    
    # Настройки подключения
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Настройки мониторинга
    worker_send_task_events=True,
    task_send_sent_event=True,
)

def wait_for_redis():
    """Ожидание готовности Redis"""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            logger.info("✅ Redis connection established")
            return True
        except Exception as e:
            retry_count += 1
            logger.warning(f"⏳ Waiting for Redis... ({retry_count}/{max_retries}): {e}")
            time.sleep(2)
    
    logger.error("❌ Failed to connect to Redis after maximum retries")
    return False

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Обработчик готовности worker"""
    logger.info("🚀 AI Services Celery Worker is ready!")
    logger.info(f"Worker: {sender}")
    logger.info(f"Broker: {REDIS_URL}")
    logger.info(f"Backend: {RESULT_BACKEND}")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Обработчик выключения worker"""
    logger.info("🔄 AI Services Celery Worker is shutting down...")

# Импорт задач - используем локальные импорты без префикса ai_services
from tasks import (
    ping_task,
    test_task,
    categorize_post,
    summarize_posts,
    process_digest,
    test_openai_connection,
    categorize_batch,
    summarize_batch
)

# Регистрация задач - используем локальные модули
app.autodiscover_tasks(['tasks'])

if __name__ == '__main__':
    # Проверка подключения к Redis
    if wait_for_redis():
        logger.info("Starting Celery worker...")
        app.start()
    else:
        logger.error("Failed to start: Redis not available")
        exit(1) 