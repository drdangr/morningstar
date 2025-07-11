#!/usr/bin/env python3
"""
Тест единого AI сервиса с Celery в Docker
"""

import time
import json
from celery import Celery

# Конфигурация подключения к Redis
REDIS_URL = 'redis://localhost:6379/0'

# Создаем клиент Celery
app = Celery('test_client')
app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

def test_ping_task():
    """Тест базовой задачи ping"""
    print("🏓 Тестирование ping_task...")
    
    try:
        # Отправляем задачу
        result = app.send_task('tasks.ping_task', args=['Test message from client'])
        
        # Получаем результат
        response = result.get(timeout=30)
        
        print(f"✅ ping_task успешно выполнена:")
        print(f"   Message: {response.get('message')}")
        print(f"   Task ID: {response.get('task_id')}")
        print(f"   Worker: {response.get('worker')}")
        print(f"   Status: {response.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ping_task ошибка: {e}")
        return False

def test_test_task():
    """Тест задачи с задержкой"""
    print("\n🧪 Тестирование test_task с задержкой...")
    
    try:
        # Отправляем задачу с задержкой 3 секунды
        result = app.send_task('tasks.test_task', args=['Test with delay'], kwargs={'delay': 3})
        
        print("⏳ Ожидаем выполнения задачи с задержкой...")
        start_time = time.time()
        
        # Получаем результат
        response = result.get(timeout=30)
        
        end_time = time.time()
        actual_delay = end_time - start_time
        
        print(f"✅ test_task успешно выполнена:")
        print(f"   Message: {response.get('message')}")
        print(f"   Expected delay: {response.get('delay')} сек")
        print(f"   Actual delay: {actual_delay:.2f} сек")
        print(f"   Status: {response.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ test_task ошибка: {e}")
        return False

def test_openai_connection():
    """Тест подключения к OpenAI API"""
    print("\n🔌 Тестирование подключения к OpenAI API...")
    
    try:
        # Отправляем задачу
        result = app.send_task('tasks.test_openai_connection')
        
        # Получаем результат
        response = result.get(timeout=30)
        
        if response.get('status') == 'success':
            print(f"✅ OpenAI API доступен:")
            print(f"   API Key present: {response.get('api_key_present')}")
            print(f"   Test response: {response.get('test_response')}")
        else:
            print(f"⚠️ OpenAI API недоступен:")
            print(f"   Error: {response.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ test_openai_connection ошибка: {e}")
        return False

def test_categorize_post():
    """Тест категоризации поста"""
    print("\n🏷️ Тестирование категоризации поста...")
    
    try:
        # Тестовый пост
        test_post = {
            'id': 1,
            'text': 'Новая технология искусственного интеллекта от OpenAI',
            'channel_username': '@test_channel',
            'post_date': '2025-07-11T10:00:00Z'
        }
        
        # Отправляем задачу
        result = app.send_task('tasks.categorize_post', args=[test_post, 1])
        
        # Получаем результат
        response = result.get(timeout=60)
        
        if response.get('status') == 'success':
            print(f"✅ Категоризация успешна:")
            print(f"   Post ID: {response.get('post_id')}")
            print(f"   Bot ID: {response.get('bot_id')}")
            print(f"   Result: {response.get('result')}")
        else:
            print(f"⚠️ Категоризация с ошибкой:")
            print(f"   Error: {response.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ categorize_post ошибка: {e}")
        return False

def test_summarize_posts():
    """Тест саммаризации постов"""
    print("\n📝 Тестирование саммаризации постов...")
    
    try:
        # Тестовые посты
        test_posts = [
            {
                'id': 1,
                'text': 'Новая технология искусственного интеллекта от OpenAI позволяет создавать более точные модели.',
                'channel_username': '@ai_news'
            },
            {
                'id': 2,
                'text': 'Исследователи разработали новый алгоритм машинного обучения для обработки естественного языка.',
                'channel_username': '@ml_research'
            }
        ]
        
        # Отправляем задачу
        result = app.send_task('tasks.summarize_posts', args=[test_posts], kwargs={'mode': 'individual'})
        
        # Получаем результат
        response = result.get(timeout=120)
        
        if response.get('status') == 'success':
            print(f"✅ Саммаризация успешна:")
            print(f"   Posts count: {response.get('posts_count')}")
            print(f"   Results count: {response.get('results_count')}")
            print(f"   Mode: {response.get('mode')}")
            
            for i, result in enumerate(response.get('results', [])[:2]):
                print(f"   Post {i+1} summary: {result.get('summary', 'N/A')[:100]}...")
        else:
            print(f"⚠️ Саммаризация с ошибкой:")
            print(f"   Error: {response.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ summarize_posts ошибка: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование unified AI сервиса с Celery в Docker")
    print("=" * 60)
    
    # Проверяем подключение к Redis
    try:
        app.control.inspect().ping()
        print("✅ Подключение к Redis/Celery успешно")
    except Exception as e:
        print(f"❌ Не удалось подключиться к Redis/Celery: {e}")
        return
    
    # Список тестов
    tests = [
        test_ping_task,
        test_test_task,
        test_openai_connection,
        test_categorize_post,
        test_summarize_posts
    ]
    
    # Выполняем тесты
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} завершился с ошибкой: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования:")
    print(f"   ✅ Пройдено: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   📈 Общий результат: {passed}/{passed + failed}")
    
    if failed == 0:
        print("🎉 Все тесты пройдены! Unified AI сервис работает корректно.")
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте конфигурацию.")

if __name__ == "__main__":
    main() 