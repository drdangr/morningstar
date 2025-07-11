#!/usr/bin/env python3
"""
Celery с thread-based backend вместо Redis
Для обхода проблемы совместимости с Redis
"""

import os
from celery import Celery

# Используем встроенный thread-based backend
app = Celery('digest_bot_threads')

app.conf.update(
    # Используем memory transport вместо Redis
    broker_url='memory://',
    result_backend='cache+memory://',
    
    # Простая конфигурация
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone настройки
    timezone='UTC',
    enable_utc=True,
    
    # Для production в будущем вернем False
    task_always_eager=False,
    task_eager_propagates=True,
    
    # Настройки для workers
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    
    # Настройки для thread-based выполнения
    worker_pool='threads',
    worker_concurrency=4,
)

# Тестовые задачи
@app.task
def ping_task():
    """Самая простая задача"""
    return "pong"

@app.task
def test_task(x, y):
    """Простая задача с параметрами"""
    return x + y

@app.task
def test_long_task(duration):
    """Задача с задержкой"""
    import time
    time.sleep(duration)
    return f"Slept for {duration} seconds"

@app.task
def test_ai_mock(text):
    """Мок AI задачи"""
    return {
        'text': text,
        'category': 'test_category',
        'summary': f'Summary of: {text[:50]}...',
        'importance': 5,
        'status': 'success'
    } 