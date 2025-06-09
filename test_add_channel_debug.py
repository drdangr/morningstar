#!/usr/bin/env python3
import requests
import json

# Backend URL
BACKEND_URL = "http://localhost:8000"

def test_add_channel():
    """Тестирует добавление канала напрямую через API"""
    
    channel_data = {
        "title": "GPT | ChatGPT | Midjourney — GPTMain News",
        "username": "@GPTMainNews", 
        "description": "Канал GPT | ChatGPT | Midjourney — GPTMain News",
        "telegram_id": 1794988016,
        "is_active": True
    }
    
    print("=== ТЕСТ ДОБАВЛЕНИЯ КАНАЛА ===")
    print(f"Данные канала: {json.dumps(channel_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/channels", json=channel_data)
        print(f"\nСтатус ответа: {response.status_code}")
        print(f"Заголовки ответа: {response.headers}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Успешно! Канал создан с ID: {result.get('id')}")
            print(f"Полный ответ: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"Ошибка! Код: {response.status_code}")
            print(f"Текст ответа: {response.text}")
            
    except Exception as e:
        print(f"Исключение при запросе: {e}")

def check_existing_channels():
    """Проверяет существующие каналы"""
    print("\n=== ПРОВЕРКА СУЩЕСТВУЮЩИХ КАНАЛОВ ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/channels")
        
        if response.status_code == 200:
            channels = response.json()
            print(f"Всего каналов: {len(channels.get('data', []))}")
            
            for channel in channels.get('data', []):
                print(f"ID: {channel['id']}, Title: {channel['title']}, "
                      f"Username: {channel.get('username', 'N/A')}, "
                      f"Telegram ID: {channel['telegram_id']}")
        else:
            print(f"Ошибка получения каналов: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"Ошибка при проверке каналов: {e}")

if __name__ == "__main__":
    print("Проверяем состояние каналов ДО добавления:")
    check_existing_channels()
    
    print("\n" + "="*50)
    
    print("Пытаемся добавить новый канал:")
    test_add_channel()
    
    print("\n" + "="*50)
    
    print("Проверяем состояние каналов ПОСЛЕ добавления:")
    check_existing_channels() 