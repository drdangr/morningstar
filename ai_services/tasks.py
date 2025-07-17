#!/usr/bin/env python3
"""
Unified Celery tasks for AI processing in MorningStarBot3
Задачи для единого контейнера с правильными именами
"""

import logging
import time
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Импорт Celery app - делаем это безопасно чтобы избежать циклических импортов
def get_celery_app():
    """Получаем экземпляр Celery app безопасным способом"""
    from celery_app import app
    return app

# Безопасная инициализация SettingsManager
settings_manager = None
try:
    from utils.settings_manager import SettingsManager
    settings_manager = SettingsManager()
    logger.info("✅ SettingsManager инициализирован")
except Exception as e:
    logger.warning(f"⚠️ SettingsManager недоступен: {e}")

# Получаем app для декораторов
app = get_celery_app()

# Test and health check tasks
@app.task(bind=True, name='tasks.ping_task')
def ping_task(self, message="Ping from AI Services"):
    """Простая задача для проверки связи"""
    logger.info(f"🏓 Ping task started: {message}")
    
    result = {
        'message': message,
        'task_id': self.request.id,
        'timestamp': time.time(),
        'worker': self.request.hostname,
        'queue': 'default',
        'status': 'success'
    }
    
    logger.info(f"🏓 Ping task completed: {result}")
    return result

@app.task(bind=True, name='tasks.test_task')
def test_task(self, message="Test from AI Services", delay=0):
    """Test task for debugging and monitoring"""
    logger.info(f"🧪 Test task started: {message}")
    
    if delay > 0:
        logger.info(f"⏳ Sleeping for {delay} seconds...")
        time.sleep(delay)
    
    result = {
        'message': message,
        'task_id': self.request.id,
        'timestamp': time.time(),
        'worker': self.request.hostname,
        'queue': 'default',
        'delay': delay,
        'status': 'success'
    }
    
    logger.info(f"🧪 Test task completed: {result}")
    return result

@app.task(bind=True, name='tasks.test_openai_connection')
def test_openai_connection(self):
    """Тест подключения к OpenAI API"""
    logger.info("🔌 Testing OpenAI connection...")
    
    try:
        # Проверяем наличие API ключа
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        # Пробуем создать клиент OpenAI
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        # Простой тест API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test message"}],
            max_tokens=10
        )
        
        result = {
            'status': 'success',
            'task_id': self.request.id,
            'timestamp': time.time(),
            'api_key_present': bool(openai_key),
            'test_response': response.choices[0].message.content if response.choices else None
        }
        
        logger.info("✅ OpenAI connection test successful")
        return result
        
    except Exception as e:
        logger.error(f"❌ OpenAI connection test failed: {e}")
        return {
            'status': 'error',
            'task_id': self.request.id,
            'timestamp': time.time(),
            'error': str(e)
        }

# AI Processing tasks
@app.task(bind=True, name='tasks.categorize_post')
def categorize_post(self, post: Dict, bot_id: int, **kwargs):
    """
    Категоризация одного поста
    
    Args:
        post: Пост для категоризации
        bot_id: ID публичного бота
        **kwargs: Дополнительные параметры
        
    Returns:
        Результат категоризации
    """
    logger.info(f"🏷️ Categorize post task started: post {post.get('id')} for bot {bot_id}")
    
    try:
        # Используем существующий сервис категоризации
        from services.categorization import CategorizationService
        
        # Создаем сервис категоризации
        categorization_service = CategorizationService(
            model_name=kwargs.get('model_name', 'gpt-4o-mini'),
            max_tokens=kwargs.get('max_tokens', 1000),
            temperature=kwargs.get('temperature', 0.3),
            settings_manager=settings_manager
        )
        
        # Заглушка для категорий бота (в реальности получаем из Backend API)
        bot_categories = kwargs.get('bot_categories', [
            {'id': 1, 'name': 'Технологии'},
            {'id': 2, 'name': 'Политика'},
            {'id': 3, 'name': 'Экономика'}
        ])
        
        # Обрабатываем пост
        result = categorization_service.categorize_post(post, bot_categories)
        
        logger.info(f"✅ Categorize post task completed: {result}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'post_id': post.get('id'),
            'result': result,
            'status': 'success',
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Categorize post task failed: {e}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'post_id': post.get('id'),
            'result': None,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

@app.task(bind=True, name='tasks.categorize_batch')
def categorize_batch(self, posts: List[Dict], bot_id: int, **kwargs):
    """
    Батчевая категоризация постов
    
    Args:
        posts: Список постов для категоризации
        bot_id: ID публичного бота
        **kwargs: Дополнительные параметры
        
    Returns:
        Список результатов категоризации
    """
    logger.info(f"🏷️ Categorize batch task started: {len(posts)} posts for bot {bot_id}")
    
    try:
        results = []
        
        # Обрабатываем каждый пост отдельно
        for post in posts:
            result = categorize_post.delay(post, bot_id, **kwargs)
            results.append(result.get(timeout=60))  # Ждем результат 60 секунд
        
        logger.info(f"✅ Categorize batch task completed: {len(results)} results")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'posts_count': len(posts),
            'results_count': len(results),
            'results': results,
            'status': 'success',
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Categorize batch task failed: {e}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'posts_count': len(posts),
            'results_count': 0,
            'results': [],
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

@app.task(bind=True, name='tasks.summarize_posts')
def summarize_posts(self, posts: List[Dict], mode: str = 'individual', **kwargs):
    """
    Саммаризация постов
    
    Args:
        posts: Список постов для саммаризации
        mode: Режим обработки ('individual' или 'batch')
        **kwargs: Дополнительные параметры
        
    Returns:
        Список результатов саммаризации
    """
    logger.info(f"📝 Summarize posts task started: {len(posts)} posts in {mode} mode")
    
    try:
        # Используем существующий сервис саммаризации
        from services.summarization import SummarizationService
        
        # Создаем сервис саммаризации
        summarization_service = SummarizationService(
            model_name=kwargs.get('model_name', 'gpt-4o'),
            max_tokens=kwargs.get('max_tokens', 2000),
            temperature=kwargs.get('temperature', 0.7),
            settings_manager=settings_manager
        )
        
        # Выбираем режим обработки
        if mode == 'individual':
            results = []
            for post in posts:
                summary = summarization_service.summarize_post(post)
                results.append({
                    'post_id': post.get('id'),
                    'summary': summary,
                    'status': 'success'
                })
        else:
            # Батчевый режим - пока не реализован
            results = summarization_service.summarize_batch(posts)
        
        logger.info(f"✅ Summarize posts task completed: {len(results)} results")
        
        return {
            'task_id': self.request.id,
            'posts_count': len(posts),
            'results_count': len(results),
            'results': results,
            'mode': mode,
            'status': 'success',
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Summarize posts task failed: {e}")
        
        return {
            'task_id': self.request.id,
            'posts_count': len(posts),
            'results_count': 0,
            'results': [],
            'mode': mode,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

@app.task(bind=True, name='tasks.summarize_batch')
def summarize_batch(self, posts: List[Dict], **kwargs):
    """
    Батчевая саммаризация постов
    """
    return summarize_posts(posts, mode='batch', **kwargs)

@app.task(bind=True, name='tasks.process_digest')
def process_digest(self, bot_id: int, posts: List[Dict], **kwargs):
    """
    Полная обработка дайджеста: категоризация + саммаризация
    
    Args:
        bot_id: ID публичного бота
        posts: Список постов для обработки
        **kwargs: Дополнительные параметры
        
    Returns:
        Результат обработки дайджеста
    """
    logger.info(f"🔄 Process digest task started: {len(posts)} posts for bot {bot_id}")
    
    try:
        # Шаг 1: Категоризация
        categorization_result = categorize_batch.delay(posts, bot_id, **kwargs)
        categorization_data = categorization_result.get(timeout=300)  # 5 минут
        
        if categorization_data['status'] != 'success':
            raise Exception(f"Categorization failed: {categorization_data.get('error')}")
        
        # Шаг 2: Саммаризация
        summarization_result = summarize_posts.delay(posts, mode='individual', **kwargs)
        summarization_data = summarization_result.get(timeout=300)  # 5 минут
        
        if summarization_data['status'] != 'success':
            raise Exception(f"Summarization failed: {summarization_data.get('error')}")
        
        logger.info(f"✅ Process digest task completed for bot {bot_id}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'posts_count': len(posts),
            'categorization': categorization_data,
            'summarization': summarization_data,
            'status': 'success',
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Process digest task failed: {e}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'posts_count': len(posts),
            'categorization': None,
            'summarization': None,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

# Cleanup tasks
@app.task(bind=True, name='tasks.cleanup_expired_results')
def cleanup_expired_results(self, max_age_hours: int = 24):
    """
    Очистка устаревших результатов задач
    
    Args:
        max_age_hours: Максимальный возраст результатов в часах
        
    Returns:
        Количество удаленных результатов
    """
    logger.info(f"🧹 Cleanup expired results task started: max_age={max_age_hours}h")
    
    try:
        # Реализация очистки результатов
        # В реальности здесь будет логика очистки Redis
        
        result = {
            'task_id': self.request.id,
            'max_age_hours': max_age_hours,
            'deleted_count': 0,  # Placeholder
            'status': 'success',
            'timestamp': time.time()
        }
        
        logger.info(f"🧹 Cleanup expired results task completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Cleanup expired results task failed: {e}")
        return {
            'task_id': self.request.id,
            'max_age_hours': max_age_hours,
            'deleted_count': 0,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

# AI Orchestrator tasks
@app.task(bind=True, name='tasks.trigger_ai_processing')
def trigger_ai_processing(self, bot_id: Optional[int] = None, force_reprocess: bool = False):
    """
    Запуск AI Orchestrator для обработки постов
    
    Args:
        bot_id: ID публичного бота (None для всех ботов)
        force_reprocess: Принудительная переобработка всех постов
        
    Returns:
        Результат запуска AI Orchestrator
    """
    logger.info(f"🤖 AI Orchestrator task started: bot_id={bot_id}, force_reprocess={force_reprocess}")
    
    try:
        # Импортируем AI Orchestrator
        from orchestrator_v5_parallel import process_bot_parallel
        
        # Определяем режим обработки
        if force_reprocess:
            mode = "force_reprocess"
        else:
            mode = "parallel"
            
        # Запускаем обработку
        result = process_bot_parallel(bot_id=bot_id, mode=mode)
        
        logger.info(f"✅ AI Orchestrator task completed: {result}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'mode': mode,
            'result': result,
            'status': 'success',
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ AI Orchestrator task failed: {e}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'mode': mode if 'mode' in locals() else 'unknown',
            'result': None,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

@app.task(bind=True, name='tasks.generate_digest_preview')
def generate_digest_preview(self, bot_id: int, limit: int = 10):
    """
    Генерация превью дайджеста для конкретного бота
    
    Args:
        bot_id: ID публичного бота
        limit: Количество постов для превью
        
    Returns:
        Превью дайджеста
    """
    logger.info(f"📋 Generate digest preview task started: bot_id={bot_id}, limit={limit}")
    
    try:
        # Импортируем AI Orchestrator  
        from orchestrator_v5_parallel import generate_digest_preview_parallel
        
        # Генерируем превью
        preview_result = generate_digest_preview_parallel(bot_id=bot_id, limit=limit)
        
        logger.info(f"✅ Generate digest preview task completed for bot {bot_id}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'limit': limit,
            'preview': preview_result,
            'status': 'success',
            'timestamp': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Generate digest preview task failed: {e}")
        
        return {
            'task_id': self.request.id,
            'bot_id': bot_id,
            'limit': limit,
            'preview': None,
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }

# Export all tasks
__all__ = [
    'ping_task',
    'test_task',
    'test_openai_connection',
    'categorize_post',
    'categorize_batch',
    'summarize_posts',
    'summarize_batch',
    'process_digest',
    'cleanup_expired_results',
    'trigger_ai_processing',
    'generate_digest_preview'
] 