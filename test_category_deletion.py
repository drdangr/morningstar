#!/usr/bin/env python3
"""
Тест удаления категорий для диагностики проблемы с user_subscriptions
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_category_deletion():
    print("🧪 ТЕСТИРОВАНИЕ УДАЛЕНИЯ КАТЕГОРИЙ")
    print("=" * 50)
    
    try:
        # 1. Создаем тестовую категорию
        print("1️⃣ Создание тестовой категории...")
        category_data = {
            "category_name": f"Test_Category_{datetime.now().strftime('%H%M%S')}",
            "description": "Тестовая категория для проверки удаления",
            "is_active": True
        }
        
        response = requests.post(f"{BASE_URL}/categories", json=category_data)
        if response.status_code != 201:
            print(f"❌ Ошибка создания категории: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        category = response.json()
        category_id = category['id']
        print(f"✅ Категория создана с ID: {category_id}")
        
        # 2. Проверяем, что категория существует
        print(f"2️⃣ Проверка существования категории...")
        response = requests.get(f"{BASE_URL}/categories/{category_id}")
        if response.status_code != 200:
            print(f"❌ Категория не найдена: {response.status_code}")
            return
        print("✅ Категория найдена")
        
        # 3. Пытаемся удалить категорию
        print(f"3️⃣ Удаление категории ID: {category_id}...")
        response = requests.delete(f"{BASE_URL}/categories/{category_id}")
        
        if response.status_code == 200:
            print("✅ Категория успешно удалена")
            print("🎉 ПРОБЛЕМА С УДАЛЕНИЕМ КАТЕГОРИЙ РЕШЕНА!")
        else:
            print(f"❌ Ошибка удаления категории: {response.status_code}")
            print(f"Response: {response.text}")
            
            if "user_subscriptions.user_id does not exist" in response.text:
                print("\n🚨 НАЙДЕНА ПРОБЛЕМА:")
                print("Таблица user_subscriptions имеет неправильную структуру")
                print("Отсутствует столбец user_id")
                print("\n💡 РЕШЕНИЕ:")
                print("Нужно остановить backend и исправить структуру таблицы")
        
        # 4. Проверяем, что категория действительно удалена
        print(f"4️⃣ Проверка удаления...")
        response = requests.get(f"{BASE_URL}/categories/{category_id}")
        if response.status_code == 404:
            print("✅ Категория действительно удалена")
        elif response.status_code == 200:
            print("⚠️ Категория всё ещё существует, удаление неполное")
        
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к backend")
        print("Убедитесь, что backend запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_backend_status():
    """Проверка статуса backend"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend доступен")
            return True
        else:
            print(f"⚠️ Backend отвечает с кодом: {response.status_code}")
            return False
    except:
        print("❌ Backend недоступен")
        return False

if __name__ == "__main__":
    if check_backend_status():
        test_category_deletion()
    else:
        print("Запустите backend и попробуйте снова") 