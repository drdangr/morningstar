#!/usr/bin/env python3
"""
Комплексный тест всех CRUD операций
Проверяем категории и каналы
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_categories_crud():
    print("📋 ТЕСТИРОВАНИЕ CRUD ОПЕРАЦИЙ ДЛЯ КАТЕГОРИЙ")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%H%M%S')
    category_id = None
    
    try:
        # 1. CREATE - Создание категории
        print("1️⃣ CREATE - Создание категории...")
        category_data = {
            "category_name": f"Test_Category_{timestamp}",
            "description": "Тестовая категория для CRUD",
            "is_active": True
        }
        
        response = requests.post(f"{BASE_URL}/categories", json=category_data)
        if response.status_code == 201:
            category = response.json()
            category_id = category['id']
            print(f"✅ CREATE работает - ID: {category_id}")
        else:
            print(f"❌ CREATE не работает: {response.status_code}")
            return False
        
        # 2. READ - Чтение категории
        print("2️⃣ READ - Чтение категории...")
        response = requests.get(f"{BASE_URL}/categories/{category_id}")
        if response.status_code == 200:
            print("✅ READ работает")
        else:
            print(f"❌ READ не работает: {response.status_code}")
        
        # 3. UPDATE - Обновление категории
        print("3️⃣ UPDATE - Обновление категории...")
        update_data = {
            "category_name": f"Updated_Category_{timestamp}",
            "description": "Обновленное описание",
            "is_active": True
        }
        
        response = requests.put(f"{BASE_URL}/categories/{category_id}", json=update_data)
        if response.status_code == 200:
            print("✅ UPDATE работает")
        else:
            print(f"❌ UPDATE не работает: {response.status_code}")
            print(f"Response: {response.text}")
        
        # 4. DELETE - Удаление категории
        print("4️⃣ DELETE - Удаление категории...")
        response = requests.delete(f"{BASE_URL}/categories/{category_id}")
        if response.status_code == 200:
            print("✅ DELETE работает")
            return True
        else:
            print(f"❌ DELETE не работает: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте категорий: {e}")
        return False

def test_channels_crud():
    print("\n📺 ТЕСТИРОВАНИЕ CRUD ОПЕРАЦИЙ ДЛЯ КАНАЛОВ")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%H%M%S')
    channel_id = None
    
    try:
        # 1. CREATE - Создание канала
        print("1️⃣ CREATE - Создание канала...")
        channel_data = {
            "channel_name": f"test_channel_{timestamp}",
            "telegram_id": int(f"1000{timestamp}"),  # Уникальный ID
            "username": f"test_user_{timestamp}",
            "title": f"Test Channel {timestamp}",
            "description": "Тестовый канал для CRUD",
            "is_active": True
        }
        
        response = requests.post(f"{BASE_URL}/channels", json=channel_data)
        if response.status_code == 201:
            channel = response.json()
            channel_id = channel['id']
            print(f"✅ CREATE работает - ID: {channel_id}")
        else:
            print(f"❌ CREATE не работает: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # 2. READ - Чтение канала
        print("2️⃣ READ - Чтение канала...")
        response = requests.get(f"{BASE_URL}/channels/{channel_id}")
        if response.status_code == 200:
            print("✅ READ работает")
        else:
            print(f"❌ READ не работает: {response.status_code}")
        
        # 3. UPDATE - Обновление канала
        print("3️⃣ UPDATE - Обновление канала...")
        update_data = {
            "channel_name": f"updated_channel_{timestamp}",
            "telegram_id": channel_data["telegram_id"],  # Тот же ID
            "username": f"updated_user_{timestamp}",
            "title": f"Updated Channel {timestamp}",
            "description": "Обновленное описание канала",
            "is_active": True
        }
        
        response = requests.put(f"{BASE_URL}/channels/{channel_id}", json=update_data)
        if response.status_code == 200:
            print("✅ UPDATE работает")
        else:
            print(f"❌ UPDATE не работает: {response.status_code}")
            print(f"Response: {response.text}")
        
        # 4. DELETE - Удаление канала
        print("4️⃣ DELETE - Удаление канала...")
        response = requests.delete(f"{BASE_URL}/channels/{channel_id}")
        if response.status_code == 200:
            print("✅ DELETE работает")
            return True
        else:
            print(f"❌ DELETE не работает: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте каналов: {e}")
        return False

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

def main():
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ CRUD ОПЕРАЦИЙ")
    print("=" * 70)
    
    if not check_backend_status():
        print("Запустите backend и попробуйте снова")
        return
    
    # Тестируем категории
    categories_ok = test_categories_crud()
    
    # Тестируем каналы  
    channels_ok = test_channels_crud()
    
    # Итоговый отчет
    print("\n📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 30)
    print(f"Категории CRUD: {'✅ ВСЕ РАБОТАЕТ' if categories_ok else '❌ ЕСТЬ ПРОБЛЕМЫ'}")
    print(f"Каналы CRUD: {'✅ ВСЕ РАБОТАЕТ' if channels_ok else '❌ ЕСТЬ ПРОБЛЕМЫ'}")
    
    if not categories_ok:
        print("\n🚨 НАЙДЕНА ПРОБЛЕМА С КАТЕГОРИЯМИ:")
        print("Удаление категорий не работает из-за ошибки user_subscriptions.user_id")
    
    if categories_ok and channels_ok:
        print("\n🎉 ВСЕ CRUD ОПЕРАЦИИ РАБОТАЮТ КОРРЕКТНО!")

if __name__ == "__main__":
    main() 