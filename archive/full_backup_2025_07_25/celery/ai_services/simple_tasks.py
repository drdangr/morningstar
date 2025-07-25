#!/usr/bin/env python3
"""
Простые Celery задачи для тестирования
Без сложных зависимостей и циклических импортов
"""

import logging
import time
import os
from celery import Celery

logger = logging.getLogger(__name__)

# Создаем простую конфигурацию Celery
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

app = Celery('simple_tasks',
             broker=REDIS_URL,
             backend=REDIS_URL)

# Простая конфигурация
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,
)

@app.task(bind=True, name='simple_tasks.ping')
def ping(self):
    """Простейшая задача для проверки работы Celery"""
    logger.info("Ping task started")
    
    result = {
        'message': 'pong',
        'task_id': self.request.id,
        'timestamp': time.time(),
        'worker': self.request.hostname,
        'status': 'success'
    }
    
    logger.info(f"Ping task completed: {result}")
    return result

@app.task(bind=True, name='simple_tasks.hello')
def hello(self, name="World"):
    """Простая задача с параметром"""
    logger.info(f"Hello task started: {name}")
    
    result = {
        'message': f'Hello, {name}!',
        'task_id': self.request.id,
        'timestamp': time.time(),
        'worker': self.request.hostname,
        'status': 'success'
    }
    
    logger.info(f"Hello task completed: {result}")
    return result

@app.task(bind=True, name='simple_tasks.sleep_test')
def sleep_test(self, duration=1):
    """Задача с задержкой для тестирования"""
    logger.info(f"Sleep test started: {duration}s")
    
    time.sleep(duration)
    
    result = {
        'message': f'Slept for {duration} seconds',
        'task_id': self.request.id,
        'timestamp': time.time(),
        'worker': self.request.hostname,
        'duration': duration,
        'status': 'success'
    }
    
    logger.info(f"Sleep test completed: {result}")
    return result 