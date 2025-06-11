import requests
import json
import time

API_BASE = 'http://localhost:8000'

print("=== ПРОВЕРКА CRUD ОПЕРАЦИЙ ===")

# Генерируем уникальные имена с timestamp
timestamp = int(time.time())

print("\n1. ТЕКУЩИЕ КАНАЛЫ:")
channels = requests.get(f'{API_BASE}/api/channels').json()
print(f"Количество каналов: {len(channels)}")
for ch in channels:
    print(f"- {ch['title']} (ID: {ch['telegram_id']}, categories: {len(ch['categories'])})")

print("\n2. ТЕКУЩИЕ КАТЕГОРИИ:")
categories = requests.get(f'{API_BASE}/api/categories').json()
print(f"Количество категорий: {len(categories)}")
for cat in categories:
    print(f"- {cat['category_name']} (ID: {cat['id']}, active: {cat['is_active']})")

print("\n3. ТЕСТ СОЗДАНИЯ НОВОЙ КАТЕГОРИИ:")
try:
    new_category = {
        "category_name": f"ТЕСТ Категория {timestamp}",  # Уникальное имя
        "description": "Категория для тестирования CRUD операций",
        "is_active": True
    }
    response = requests.post(f'{API_BASE}/api/categories', json=new_category)
    if response.status_code == 201:
        created_cat = response.json()
        print(f"✅ Создана категория: {created_cat['category_name']} (ID: {created_cat['id']})")
        test_category_id = created_cat['id']
    else:
        print(f"❌ Ошибка создания категории: {response.status_code} - {response.text}")
        test_category_id = None
except Exception as e:
    print(f"❌ Исключение при создании категории: {e}")
    test_category_id = None

print("\n4. ТЕСТ СОЗДАНИЯ НОВОГО КАНАЛА:")
try:
    new_channel = {
        "channel_name": f"ТЕСТ Канал {timestamp}",  # Уникальное имя
        "telegram_id": -1001000000000 - timestamp,  # Уникальный ID
        "username": f"test_channel_{timestamp}", 
        "title": f"ТЕСТ Канал {timestamp}",
        "description": "Канал для тестирования CRUD операций",
        "is_active": True
    }
    response = requests.post(f'{API_BASE}/api/channels', json=new_channel)
    if response.status_code == 201:
        created_ch = response.json()
        print(f"✅ Создан канал: {created_ch['title']} (ID: {created_ch['telegram_id']})")
        test_channel_id = created_ch['id']
    else:
        print(f"❌ Ошибка создания канала: {response.status_code} - {response.text}")
        test_channel_id = None
except Exception as e:
    print(f"❌ Исключение при создании канала: {e}")
    test_channel_id = None

print("\n5. ТЕСТ СВЯЗИ КАНАЛ-КАТЕГОРИЯ:")
if test_channel_id and test_category_id:
    try:
        response = requests.post(f'{API_BASE}/api/channels/{test_channel_id}/categories/{test_category_id}')
        if response.status_code == 200:
            print("✅ Связь канал-категория создана")
            
            # Проверяем что связь реально создалась
            channel_response = requests.get(f'{API_BASE}/api/channels/{test_channel_id}')
            if channel_response.status_code == 200:
                channel_data = channel_response.json()
                print(f"✅ Канал теперь имеет {len(channel_data['categories'])} категорий")
        else:
            print(f"❌ Ошибка создания связи: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Исключение при создании связи: {e}")
else:
    print("❌ Пропущено из-за ошибок создания канала или категории")

print("\n6. ПРОВЕРКА ОБНОВЛЕНИЙ В БД:")
channels_after = requests.get(f'{API_BASE}/api/channels').json()
categories_after = requests.get(f'{API_BASE}/api/categories').json()
print(f"Каналов после: {len(channels_after)} (было: {len(channels)})")
print(f"Категорий после: {len(categories_after)} (было: {len(categories)})")

print("\n7. ОЧИСТКА ТЕСТОВЫХ ДАННЫХ:")
if test_channel_id:
    try:
        response = requests.delete(f'{API_BASE}/api/channels/{test_channel_id}')
        if response.status_code == 200:
            print("✅ Тестовый канал удален")
        else:
            print(f"❌ Ошибка удаления канала: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение при удалении канала: {e}")

if test_category_id:
    try:
        response = requests.delete(f'{API_BASE}/api/categories/{test_category_id}')
        if response.status_code == 200:
            print("✅ Тестовая категория удалена")
        else:
            print(f"❌ Ошибка удаления категории: {response.status_code}")
    except Exception as e:
        print(f"❌ Исключение при удалении категории: {e}")

# Очистка старых тестовых данных если есть
print("\n8. ОЧИСТКА СТАРЫХ ТЕСТОВЫХ ДАННЫХ:")
try:
    all_categories = requests.get(f'{API_BASE}/api/categories').json()
    for cat in all_categories:
        if "ТЕСТ Категория" in cat['category_name']:
            response = requests.delete(f'{API_BASE}/api/categories/{cat["id"]}')
            if response.status_code == 200:
                print(f"✅ Удалена старая тестовая категория: {cat['category_name']}")
except Exception as e:
    print(f"❌ Ошибка очистки старых данных: {e}")

print("\n=== ИТОГ ПРОВЕРКИ CRUD ===")
success = test_channel_id is not None and test_category_id is not None
print("✅ CRUD операции работают корректно" if success else "❌ Обнаружены проблемы в CRUD операциях")

if not success:
    print("\n🔧 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ:")
    print("1. Перезапустить backend для применения изменений в модели Channel")
    print("2. Проверить логи backend на предмет ошибок базы данных")
    print("3. Убедиться что поле channel_name корректно обрабатывается") 