#!/usr/bin/env python3
"""
Unified Celery tasks for AI processing in MorningStarBot3
Задачи для единого контейнера с правильными именами
"""

import logging
import time
import os
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import httpx

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

# === Helper constants ===
BACKEND_URL = os.getenv("BACKEND_INTERNAL_URL", "http://backend:8000")


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
        # Получаем API ключ через SettingsManager (правильная архитектура)
        
        async def get_api_key():
            if settings_manager:
                return await settings_manager.get_openai_key()
            else:
                raise ValueError("SettingsManager не инициализирован")
        
        # Выполняем асинхронное получение ключа
        openai_key = asyncio.run(get_api_key())
        
        if not openai_key:
            raise ValueError("OpenAI API ключ не найден в Backend API")
        
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
        
        # Получаем ключ - ПРИОРИТЕТ У SETTINGS_MANAGER
        openai_key = None
        if settings_manager:
            try:
                import asyncio
                openai_key = asyncio.run(settings_manager.get_openai_key())
                logger.info("✅ OpenAI ключ получен из SettingsManager")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить ключ из SettingsManager: {e}")
                openai_key = None
        
        # Fallback на переменную окружения только если SettingsManager недоступен
        if not openai_key:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                logger.info("⚠️ Используется OpenAI ключ из переменной окружения (fallback)")
        
        if not openai_key:
            logger.error("❌ OPENAI_API_KEY не найден ни в SettingsManager, ни в переменных окружения")
            return {
                'task_id': self.request.id,
                'bot_id': bot_id,
                'post_id': post.get('id'),
                'result': None,
                'status': 'error',
                'error': 'missing_openai_api_key',
                'timestamp': time.time()
            }

        categorization_service = CategorizationService(
            backend_url=os.getenv('BACKEND_API_URL', 'http://backend:8000'),
            settings_manager=settings_manager
        )
        
        # Заглушка для категорий бота (в реальности получаем из Backend API)
        bot_categories = kwargs.get('bot_categories', [
            {'id': 1, 'name': 'Технологии'},
            {'id': 2, 'name': 'Политика'},
            {'id': 3, 'name': 'Экономика'}
        ])
        
        # Создаём упрощённый PostData объект, необходимый сервису (id, content)
        from types import SimpleNamespace
        simple_post = SimpleNamespace(
            id=post.get('id'),
            channel_telegram_id=post.get('channel_telegram_id'),
            telegram_message_id=post.get('telegram_message_id'),
            title=post.get('title'),
            content=post.get('content')
        )

        import asyncio
        result_list = asyncio.run(
            categorization_service.process_with_bot_config([simple_post], bot_id)
        )
        result = result_list[0] if result_list else {}
        
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
            import asyncio
            results = []
            for post in posts:
                summary_res = asyncio.run(
                    summarization_service.process(
                        text=post.get('content') or '',
                        max_summary_length=kwargs.get('max_summary_length', 150)
                    )
                )
                results.append({
                    'post_id': post.get('id'),
                    'summary': summary_res.get('summary', ''),
                    'status': summary_res.get('status', 'success')
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
        # 🔄 Заменяем на новые Celery pipeline задачи
        task_map = []
        if bot_id is None:
            # Получаем список активных ботов через Backend API
            try:
                import httpx
                with httpx.Client(timeout=30) as client:
                    resp = client.get(f"{BACKEND_URL}/api/public-bots", params={"status_filter": "active"})
                    resp.raise_for_status()
                    bots = resp.json()
                    bot_ids = [b['id'] for b in bots]
            except Exception as e:
                logger.error(f"❌ Не удалось получить список ботов: {e}")
                bot_ids = []
        else:
            bot_ids = [bot_id]

        for b_id in bot_ids:
            t = process_bot_digest.delay(b_id)
            task_map.append({"bot_id": b_id, "task_id": t.id})

        logger.info(f"✅ AI trigger redirected: {task_map}")

        return {
            'task_id': self.request.id,
            'tasks': task_map,
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

# NEW TASK: Полная обработка постов конкретного бота
@app.task(bind=True, name='tasks.process_bot_digest')
def process_bot_digest(self, bot_id: int, limit: int = 50):
    """Полная обработка необработанных постов для одного бота (категоризация + саммаризация).

    Шаги:
    1. Получить список активных категорий бота
    2. Получить необработанные посты (require_categorization)
    3. Для каждого поста выполнить CategorizationService и SummarizationService
    4. Сохранить результаты батчем через /api/ai/results/batch
    """

    logger.info(f"🚀 process_bot_digest started for bot {bot_id}")

    try:
        session = httpx.Client()

        # 1. Получаем категории бота
        cat_resp = session.get(f"{BACKEND_URL}/api/public-bots/{bot_id}/categories", timeout=30)
        cat_resp.raise_for_status()
        bot_categories = cat_resp.json()

        if not bot_categories:
            logger.warning(f"⚠️ У бота {bot_id} нет категорий – пропуск")
            return {
                'status': 'skipped',
                'reason': 'no_categories',
                'bot_id': bot_id,
                'task_id': self.request.id,
                'timestamp': time.time()
            }

        # Преобразуем категории в упрощённый формат для сервиса категоризации
        categories_for_service = []
        for c in bot_categories:
            cat_name = c.get('name') or c.get('category_name') or c.get('category')
            if not cat_name:
                cat_name = f"Category {c.get('id')}"
            categories_for_service.append({'id': c['id'], 'name': cat_name})

        # 2. Получаем необработанные посты
        posts_resp = session.get(
            f"{BACKEND_URL}/api/posts/unprocessed",
            params={
                'bot_id': bot_id,
                'require_categorization': 'true',
                'limit': limit
            },
            timeout=60
        )
        posts_resp.raise_for_status()
        posts = posts_resp.json()

        if not posts:
            logger.info(f"✅ Нет новых постов для бота {bot_id}")
            return {
                'status': 'nothing_to_do',
                'bot_id': bot_id,
                'posts_processed': 0,
                'task_id': self.request.id,
                'timestamp': time.time()
            }

        # 3. Инициализируем AI сервисы
        from services.categorization import CategorizationService
        from services.summarization import SummarizationService

        # Получаем OpenAI API ключ - ПРИОРИТЕТ У SETTINGS_MANAGER
        openai_api_key = None
        if settings_manager:
            try:
                import asyncio
                openai_api_key = asyncio.run(settings_manager.get_openai_key())
                logger.info("✅ OpenAI ключ получен из SettingsManager для process_bot_digest")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить ключ из SettingsManager: {e}")
                openai_api_key = None
        
        # Fallback на переменную окружения только если SettingsManager недоступен
        if not openai_api_key:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                logger.info("⚠️ Используется OpenAI ключ из переменной окружения (fallback)")
        
        if not openai_api_key:
            logger.error("❌ OPENAI_API_KEY не найден ни в SettingsManager, ни в переменных окружения")
            return {
                'status': 'error',
                'error': 'missing_openai_api_key',
                'bot_id': bot_id,
                'task_id': self.request.id,
                'timestamp': time.time()
            }

        categorizer = CategorizationService(
            backend_url=BACKEND_URL,
            settings_manager=settings_manager
        )
        summarizer = SummarizationService(settings_manager=settings_manager)

        ai_results_payload = []

        for post in posts:
            try:
                cat_result = categorizer.categorize_post(post, categories_for_service)

                # summary может быть пустым для очень коротких постов
                summary_data = asyncio.run(
                    summarizer.process(
                        text=post.get('content') or '',
                        max_summary_length=150
                    )
                )

                ai_results_payload.append({
                    'post_id': post['id'],
                    'public_bot_id': bot_id,
                    'summaries': {
                        'summary': summary_data.get('summary', '')
                    },
                    'categories': {
                        'category': cat_result.get('category')
                    },
                    'metrics': {
                        'relevance': cat_result.get('relevance', 0)
                    }
                })

            except Exception as e:
                logger.error(f"❌ Ошибка обработки поста {post['id']}: {e}")

        if not ai_results_payload:
            logger.warning(f"⚠️ Не удалось обработать ни одного поста для бота {bot_id}")
            return {
                'status': 'error',
                'error': 'no_results',
                'bot_id': bot_id,
                'task_id': self.request.id,
                'timestamp': time.time()
            }

        # 4. Сохраняем результаты батчем
        save_resp = session.post(f"{BACKEND_URL}/api/ai/results/batch", json=ai_results_payload, timeout=60)
        save_resp.raise_for_status()

        saved_results = save_resp.json()

        logger.info(f"✅ process_bot_digest completed for bot {bot_id}: {len(saved_results)} results saved")

        return {
            'status': 'success',
            'bot_id': bot_id,
            'posts_processed': len(saved_results),
            'task_id': self.request.id,
            'timestamp': time.time()
        }

    except Exception as e:
        logger.error(f"❌ process_bot_digest failed for bot {bot_id}: {e}")
        return {
            'status': 'error',
            'bot_id': bot_id,
            'error': str(e),
            'task_id': self.request.id,
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
    'generate_digest_preview',
    'process_bot_digest'
] 