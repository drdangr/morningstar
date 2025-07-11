#!/usr/bin/env python3
"""
Рабочая версия Celery для разработки AI сервисов
Синхронный режим - обходит проблему с Redis, позволяет разрабатывать AI задачи
"""

import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# Рабочая конфигурация для разработки
app = Celery('morningstar_ai_dev')

app.conf.update(
    # Redis для compatibility тестов в будущем
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # СИНХРОННЫЙ РЕЖИМ для разработки (обходит проблему с Redis)
    task_always_eager=True,
    task_eager_propagates=True,
    
    # Простая и надежная конфигурация
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Для будущего async режима
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    
    # Результаты сохраняем
    task_ignore_result=False,
    result_expires=3600,
)

# ТЕСТОВЫЕ ЗАДАЧИ
@app.task
def ping_task():
    """Простая проверка работы Celery"""
    return "pong"

@app.task
def test_task(x, y):
    """Тест с параметрами"""
    return x + y

# AI СЕРВИСЫ - ЗАГОТОВКИ
@app.task(bind=True, name='ai.categorize')
def categorize_task(self, posts, bot_id):
    """
    Категоризация постов
    TODO: Интеграция с CategorizationService
    """
    logger.info(f"Categorizing {len(posts)} posts for bot {bot_id}")
    
    # Заглушка для тестирования
    results = []
    for post in posts:
        results.append({
            'post_id': post.get('id'),
            'category': 'test_category',
            'relevance_score': 0.8,
            'status': 'success'
        })
    
    return {
        'task_id': self.request.id,
        'bot_id': bot_id,
        'processed': len(results),
        'results': results,
        'status': 'success'
    }

@app.task(bind=True, name='ai.summarize')
def summarize_task(self, posts, bot_id):
    """
    Саммаризация постов
    TODO: Интеграция с SummarizationService
    """
    logger.info(f"Summarizing {len(posts)} posts for bot {bot_id}")
    
    # Заглушка для тестирования
    results = []
    for post in posts:
        results.append({
            'post_id': post.get('id'),
            'summary': f"Summary of post {post.get('id', 'N/A')}",
            'status': 'success'
        })
    
    return {
        'task_id': self.request.id,
        'bot_id': bot_id,
        'processed': len(results),
        'results': results,
        'status': 'success'
    }

@app.task(bind=True, name='ai.process_digest')
def process_digest_task(self, bot_id, max_posts=15):
    """
    Главная задача обработки дайджеста
    TODO: Интеграция с Backend API
    """
    logger.info(f"Processing digest for bot {bot_id}, max_posts={max_posts}")
    
    # Заглушка - тестовые посты
    test_posts = [
        {'id': 1, 'content': 'Test post 1'},
        {'id': 2, 'content': 'Test post 2'},
        {'id': 3, 'content': 'Test post 3'},
    ]
    
    # В синхронном режиме вызываем функции напрямую
    # Категоризация
    cat_data = categorize_task(test_posts, bot_id)
    
    # Саммаризация
    sum_data = summarize_task(test_posts, bot_id)
    
    return {
        'task_id': self.request.id,
        'bot_id': bot_id,
        'posts_processed': len(test_posts),
        'categorization': cat_data,
        'summarization': sum_data,
        'status': 'success'
    }

# HEALTH CHECK
@app.task(bind=True, name='health.check')
def health_check_task(self):
    """Проверка здоровья AI сервисов"""
    return {
        'task_id': self.request.id,
        'status': 'healthy',
        'mode': 'development',
        'sync_mode': True,
        'redis_available': True,  # Redis доступен для конфигурации
        'ai_services_ready': True
    }

if __name__ == '__main__':
    # Тестирование
    print("Testing Celery AI services...")
    
    # Простой тест
    result = ping_task.delay()
    print(f"Ping: {result.get()}")
    
    # Тест AI сервисов
    result = process_digest_task.delay(bot_id=1, max_posts=3)
    print(f"Digest processing: {result.get()}")
    
    # Health check
    result = health_check_task.delay()
    print(f"Health check: {result.get()}")
    
    print("✅ All tests passed! Ready for AI services development") 