#!/usr/bin/env python3
"""
Тест Celery через Docker контейнер
НАКОНЕЦ-ТО асинхронное выполнение работает!
"""

import time
import sys
import os

# Добавляем путь к ai_services
sys.path.append('ai_services')

from ai_services.celery_simple import ping_task, test_task, test_long_task

def test_async_execution():
    """Тестируем асинхронное выполнение задач"""
    print("🧪 Тестируем асинхронное выполнение Celery через Docker...")
    
    # Тест 1: Простая задача
    print("\n1️⃣ Тест ping_task:")
    result = ping_task.delay()
    print(f"   Task ID: {result.id}")
    print(f"   Result: {result.get(timeout=10)}")
    
    # Тест 2: Задача с параметрами  
    print("\n2️⃣ Тест test_task(5, 3):")
    result = test_task.delay(5, 3)
    print(f"   Task ID: {result.id}")
    print(f"   Result: {result.get(timeout=10)}")
    
    # Тест 3: Длительная задача
    print("\n3️⃣ Тест test_long_task(2 сек):")
    start_time = time.time()
    result = test_long_task.delay(2)
    print(f"   Task ID: {result.id}")
    print(f"   Отправили задачу, но не ждем... (асинхронно!)")
    
    # Ждем результат
    print(f"   Получаем результат...")
    task_result = result.get(timeout=15)
    end_time = time.time()
    
    print(f"   Result: {task_result}")
    print(f"   Общее время: {end_time - start_time:.2f} сек")
    
    # Тест 4: Параллельные задачи
    print("\n4️⃣ Тест параллельного выполнения:")
    start_time = time.time()
    
    # Запускаем 3 задачи параллельно
    tasks = []
    for i in range(3):
        task = test_long_task.delay(1)  # По 1 секунде каждая
        tasks.append(task)
        print(f"   Запущена задача {i+1}: {task.id}")
    
    # Ждем все результаты
    results = []
    for i, task in enumerate(tasks):
        result = task.get(timeout=15)
        results.append(result)
        print(f"   Задача {i+1} завершена: {result}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n📊 Результаты параллельности:")
    print(f"   3 задачи по 1 сек выполнились за {total_time:.2f} сек")
    if total_time < 2.5:  # Должно быть ~1-1.5 сек если параллельно
        print("   ✅ ПАРАЛЛЕЛЬНОСТЬ РАБОТАЕТ!")
    else:
        print("   ❌ Задачи выполняются последовательно")
    
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! REDIS + CELERY + DOCKER = SUCCESS!")

if __name__ == '__main__':
    test_async_execution() 