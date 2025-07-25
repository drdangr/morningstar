#!/usr/bin/env python3
"""
Простая конфигурация Celery для локальной разработки
Согласно рекомендациям из CELERY.md
Обновлено для Docker deployment
"""

import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# Получаем broker URL из переменных окружения (Docker) или fallback на localhost
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Для локальной разработки используем простую конфигурацию
app = Celery('digest_bot')

app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    
    # ОТКЛЮЧАЕМ синхронный режим для Docker (Linux контейнер решает проблемы Windows)
    task_always_eager=False,
    task_eager_propagates=True,
    
    # Простая сериализация для начала
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Оптимизации для Docker
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    
    # Timezone настройки
    timezone='UTC',
    enable_utc=True,
    
    # Результаты
    result_expires=3600,
    task_ignore_result=False,
    
    # Настройки для production в Docker
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=5,
    
    # Task routing для масштабируемости
    task_routes={
        'celery_simple.ping_task': {'queue': 'default'},
        'celery_simple.test_task': {'queue': 'default'},
        'celery_simple.test_long_task': {'queue': 'default'},
    },
)

@app.task
def ping_task():
    """Простая проверка работы Celery"""
    logger.info("Ping task executed in Docker container")
    return "pong"

@app.task
def test_task(x, y):
    """Тест с параметрами"""
    logger.info(f"Test task executed: {x} + {y}")
    return x + y

@app.task
def test_long_task(duration):
    """Задача с задержкой для тестирования"""
    import time
    logger.info(f"Long task started: {duration}s")
    time.sleep(duration)
    logger.info(f"Long task completed: {duration}s")
    return f"Slept for {duration} seconds"

if __name__ == '__main__':
    print(f"Celery configuration:")
    print(f"Broker URL: {REDIS_URL}")
    print(f"Task always eager: {app.conf.task_always_eager}")
    print(f"Worker prefetch: {app.conf.worker_prefetch_multiplier}")
    print(f"Ready for Docker deployment!") 