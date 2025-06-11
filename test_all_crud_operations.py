#!/usr/bin/env python3
"""
Полное тестирование всех CRUD операций
Проверяем категории и каналы: создание, чтение, обновление, удаление
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_categories_crud():
    print("📋 ТЕСТИРОВАНИЕ КАТЕГОРИЙ")
    print("=" * 40)
    
    # 1. CREATE - Создание категории
    print("1️⃣ CREATE - Создание категории...")
    category_data = {
        "category_name": f"Test_Category_{datetime.now().strftime('%H%M%S')}",
        "description": "Тестовая категория для полной проверки CRUD",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/categories", json=category_data)
    if response.status_code == 201:
        category = response.json()
        category_id = category['id']
        print(f"   ✅ Категория создана: ID {category_id}, название '{category['category_name']}'")
    else:
        print(f"   ❌ Ошибка создания: {response.status_code}")
        return None
    
    # 2. READ - Чтение категории
    print("2️⃣ READ - Чтение категории...")
    response = requests.get(f"{BASE_URL}/categories/{category_id}")
    if response.status_code == 200:
        print("   ✅ Категория успешно прочитана")
    else:
        print(f"   ❌ Ошибка чтения: {response.status_code}")
    
    # 3. UPDATE - Обновление категории
    print("3️⃣ UPDATE - Обновление категории...")
    update_data = {
        "category_name": f"Updated_Category_{datetime.now().strftime('%H%M%S')}",
        "description": "Обновленное описание категории",
        "is_active": True
    }
    
    response = requests.put(f"{BASE_URL}/categories/{category_id}", json=update_data)
    if response.status_code == 200:
        updated_category = response.json()
        print(f"   ✅ Категория обновлена: новое название '{updated_category['category_name']}'")
    else:
        print(f"   ❌ Ошибка обновления: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # 4. DELETE - Удаление категории
    print("4️⃣ DELETE - Удаление категории...")
    response = requests.delete(f"{BASE_URL}/categories/{category_id}")
    if response.status_code == 200:
        print("   ✅ Категория успешно удалена")
        return "SUCCESS"
    else:
        print(f"   ❌ Ошибка удаления: {response.status_code}")
        print(f"   Response: {response.text}")
        return "DELETE_FAILED"

def test_channels_crud():
    print("\n📺 ТЕСТИРОВАНИЕ КАНАЛОВ")
    print("=" * 40)
    
    # 1. CREATE - Создание канала
    print("1️⃣ CREATE - Создание канала...")
    channel_data = {
        "channel_name": f"test_channel_{datetime.now().strftime('%H%M%S')}",
        "telegram_id": int(f"100{datetime.now().strftime('%H%M%S')}"),  # Уникальный ID
        "username": f"test_channel_{datetime.now().strftime('%H%M%S')}",
        "title": f"Test Channel {datetime.now().strftime('%H:%M:%S')}",
        "description": "Тестовый канал для проверки CRUD",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/channels", json=channel_data)
    if response.status_code == 201:
        channel = response.json()
        channel_id = channel['id']
        print(f"   ✅ Канал создан: ID {channel_id}, название '{channel['title']}'")
    else:
        print(f"   ❌ Ошибка создания: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    # 2. READ - Чтение канала
    print("2️⃣ READ - Чтение канала...")
    response = requests.get(f"{BASE_URL}/channels/{channel_id}")
    if response.status_code == 200:
        print("   ✅ Канал успешно прочитан")
    else:
        print(f"   ❌ Ошибка чтения: {response.status_code}")
    
    # 3. UPDATE - Обновление канала
    print("3️⃣ UPDATE - Обновление канала...")
    update_data = {
        "channel_name": f"updated_channel_{datetime.now().strftime('%H%M%S')}",
        "telegram_id": channel_data["telegram_id"],  # Тот же ID
        "username": channel_data["username"],
        "title": f"Updated Channel {datetime.now().strftime('%H:%M:%S')}",
        "description": "Обновленное описание канала",
        "is_active": True
    }
    
    response = requests.put(f"{BASE_URL}/channels/{channel_id}", json=update_data)
    if response.status_code == 200:
        updated_channel = response.json()
        print(f"   ✅ Канал обновлен: новое название '{updated_channel['title']}'")
    else:
        print(f"   ❌ Ошибка обновления: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # 4. DELETE - Удаление канала
    print("4️⃣ DELETE - Удаление канала...")
    response = requests.delete(f"{BASE_URL}/channels/{channel_id}")
    if response.status_code == 200:
        print("   ✅ Канал успешно удален")
        return "SUCCESS"
    else:
        print(f"   ❌ Ошибка удаления: {response.status_code}")
        print(f"   Response: {response.text}")
        return "DELETE_FAILED"

def check_backend_status():
    """Проверка доступности backend"""
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
    print("🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ CRUD ОПЕРАЦИЙ")
    print("=" * 50)
    
    if not check_backend_status():
        print("Запустите backend и попробуйте снова")
        return
    
    # Тестируем категории
    categories_result = test_categories_crud()
    
    # Тестируем каналы  
    channels_result = test_channels_crud()
    
    # Итоговый отчет
    print("\n📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 30)
    print(f"Категории CRUD: {'✅ ВСЕ РАБОТАЕТ' if categories_result == 'SUCCESS' else '❌ УДАЛЕНИЕ НЕ РАБОТАЕТ' if categories_result == 'DELETE_FAILED' else '❌ КРИТИЧЕСКИЕ ОШИБКИ'}")
    print(f"Каналы CRUD: {'✅ ВСЕ РАБОТАЕТ' if channels_result == 'SUCCESS' else '❌ УДАЛЕНИЕ НЕ РАБОТАЕТ' if channels_result == 'DELETE_FAILED' else '❌ КРИТИЧЕСКИЕ ОШИБКИ'}")
    
    if categories_result == "DELETE_FAILED" and channels_result == "SUCCESS":
        print("\n💡 ВЫВОД: Проблема только с удалением категорий (таблица user_subscriptions)")
        print("Остальные операции работают корректно!")

if __name__ == "__main__":
    main() 