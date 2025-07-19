#!/usr/bin/env python3
"""
Простой тест AI Services изнутри контейнера
"""

from celery_app import app
import time
import json

def test_basic_tasks():
    """Тест базовых задач"""
    print("🧪 Базовые задачи:")
    
    # Ping task
    result = app.send_task('tasks.ping_task', args=['Container test'])
    response = result.get(timeout=10)
    print(f"✅ ping_task: {response['status']}")
    
    # Test task
    result = app.send_task('tasks.test_task', args=['Container data'])
    response = result.get(timeout=10)
    print(f"✅ test_task: {response['status']}")

def test_ai_tasks():
    """Тест AI задач"""
    print("\n🤖 AI задачи:")
    
    # OpenAI test
    result = app.send_task('tasks.test_openai_connection')
    try:
        response = result.get(timeout=30)
        print(f"✅ test_openai_connection: {response['status']}")
    except Exception as e:
        print(f"❌ test_openai_connection: {e}")
    
    # Categorization test
    test_post = {
        'id': 999,
        'text': 'Сегодня в Туле прошел концерт классической музыки.',
        'channel_name': 'test'
    }
    
    categories = [
        {'id': 1, 'name': 'Культура', 'description': 'Культурные события'},
        {'id': 2, 'name': 'Новости', 'description': 'Общие новости'}
    ]
    
    result = app.send_task('tasks.categorize_post', args=[test_post, categories])
    try:
        response = result.get(timeout=30)
        print(f"✅ categorize_post: {response['status']}")
    except Exception as e:
        print(f"❌ categorize_post: {e}")

def main():
    print("🚀 AI Services Test (Container)")
    print("=" * 40)
    
    test_basic_tasks()
    test_ai_tasks()
    
    print("\n🎉 Тест завершен!")

if __name__ == '__main__':
    main() 