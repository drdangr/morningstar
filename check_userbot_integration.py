import requests
import json
import os

API_BASE = 'http://localhost:8000'

print("=== ПРОВЕРКА USERBOT→БД ИНТЕГРАЦИИ ===")

print("\n1. ТЕКУЩЕЕ СОСТОЯНИЕ КАНАЛОВ В БД:")
channels = requests.get(f'{API_BASE}/api/channels').json()
print(f"Количество каналов в БД: {len(channels)}")

if channels:
    print("Каналы из БД:")
    for ch in channels:
        print(f"- {ch['title']} (@{ch['username']}) ID: {ch['telegram_id']}")
else:
    print("⚠️ В БД нет каналов! Добавим тестовые каналы...")
    
    # Добавим реальные каналы для тестирования
    test_channels = [
        {
            "channel_name": "Breaking Mash",
            "telegram_id": -1001312409582,
            "username": "breakingmash",
            "title": "Breaking Mash", 
            "description": "Новости и события",
            "is_active": True
        },
        {
            "channel_name": "Дуров",
            "telegram_id": -1001021202233,
            "username": "durov",
            "title": "Павел Дуров",
            "description": "Официальный канал Павла Дурова",
            "is_active": True
        }
    ]
    
    for channel_data in test_channels:
        try:
            response = requests.post(f'{API_BASE}/api/channels', json=channel_data)
            if response.status_code == 201:
                created = response.json()
                print(f"✅ Добавлен канал: {created['title']} (ID: {created['telegram_id']})")
            else:
                print(f"❌ Ошибка добавления канала {channel_data['title']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Исключение при добавлении канала: {e}")

print("\n2. ПРОВЕРКА КОНФИГУРАЦИИ USERBOT:")

# Проверим файл конфигурации userbot
userbot_config_files = [
    'userbot/src/config.py',
    'userbot/src/main.py',
    'userbot/src/telegram_client.py'
]

print("Проверка файлов userbot...")
for config_file in userbot_config_files:
    if os.path.exists(config_file):
        print(f"✅ {config_file} найден")
    else:
        print(f"❌ {config_file} не найден")

print("\n3. ПРОВЕРКА posts_cache ДАННЫХ:")
posts_response = requests.get(f'{API_BASE}/api/posts/cache')
posts_data = posts_response.json()
print(f"Количество постов в posts_cache: {len(posts_data)}")

if posts_data:
    print("Последние 3 поста:")
    for post in posts_data[:3]:
        print(f"- Канал ID: {post['channel_telegram_id']}, Дата: {post['post_date'][:10]}")
    
    # Проверим, соответствуют ли telegram_id постов каналам в БД
    channels_from_db = requests.get(f'{API_BASE}/api/channels').json()
    db_channel_ids = {ch['telegram_id'] for ch in channels_from_db}
    
    posts_channel_ids = {post['channel_telegram_id'] for post in posts_data}
    
    print(f"\nКаналы в БД: {db_channel_ids}")
    print(f"Каналы в posts_cache: {posts_channel_ids}")
    
    if posts_channel_ids.issubset(db_channel_ids):
        print("✅ Все посты соответствуют каналам из БД")
    else:
        missing_channels = posts_channel_ids - db_channel_ids
        print(f"⚠️ Найдены посты от каналов, отсутствующих в БД: {missing_channels}")
        print("Это может указывать на использование fallback данных")

print("\n4. ПРОВЕРКА НАСТРОЕК USERBOT:")

# Проверим настройки, которые влияют на источник каналов
collection_settings = [
    "COLLECTION_DEPTH_DAYS",
    "MAX_POSTS_PER_CHANNEL"
]

print("Настройки сбора данных:")
for setting_key in collection_settings:
    try:
        response = requests.get(f'{API_BASE}/api/config/{setting_key}')
        if response.status_code == 200:
            value = response.json().get('value', 'не найдено')
            print(f"- {setting_key}: {value}")
        else:
            print(f"- {setting_key}: не найдено в БД")
    except Exception as e:
        print(f"- {setting_key}: ошибка получения ({e})")

print("\n5. АНАЛИЗ ИСТОЧНИКА ДАННЫХ:")

# Проанализируем откуда приходят данные
channels_final = requests.get(f'{API_BASE}/api/channels').json()
posts_final = requests.get(f'{API_BASE}/api/posts/cache').json()

if not channels_final:
    print("❌ ПРОБЛЕМА: В БД нет каналов, но возможно userbot использует fallback")
elif not posts_final:
    print("⚠️ В posts_cache нет данных - userbot не запускался или не работает")
else:
    db_channels = {ch['telegram_id']: ch['title'] for ch in channels_final}
    post_channels = set(post['channel_telegram_id'] for post in posts_final)
    
    print("Соответствие данных:")
    all_match = True
    for channel_id in post_channels:
        if channel_id in db_channels:
            print(f"✅ Канал {channel_id} ({db_channels[channel_id]}) есть в БД")
        else:
            print(f"❌ Канал {channel_id} есть в постах, но НЕТ в БД - возможно fallback!")
            all_match = False
    
    if all_match:
        print("\n✅ РЕЗУЛЬТАТ: Userbot корректно использует каналы из БД")
    else:
        print("\n❌ РЕЗУЛЬТАТ: Обнаружено использование fallback данных")

print("\n=== РЕКОМЕНДАЦИИ ===")
print("1. Убедиться что userbot читает каналы из Backend API, а не из hardcoded списка")
print("2. Проверить код userbot на наличие fallback логики")
print("3. Возможно нужно перезапустить userbot после добавления каналов в БД") 