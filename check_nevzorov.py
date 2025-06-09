import requests
import json

# Получаем все каналы
response = requests.get('http://localhost:8000/api/channels')
channels = response.json()

# Ищем каналы Невзорова
nevzorov_channels = [c for c in channels if 'евзоров' in c.get('title', '').lower() or 'nevzorov' in c.get('username', '').lower()]

print(f"🔍 Найдено каналов Невзорова: {len(nevzorov_channels)}")

for i, channel in enumerate(nevzorov_channels, 1):
    print(f"\n{i}. 📺 {channel['title']}")
    print(f"   Username: {channel.get('username', 'Не указано')}")
    print(f"   Telegram ID: {channel.get('telegram_id', 'Не указано')}")
    print(f"   Активен: {'✅' if channel.get('is_active') else '❌'}")
    print(f"   Описание: {channel.get('description', 'Нет описания')}")
    print(f"   Последний парсинг: {channel.get('last_parsed', 'Никогда')}")
    print(f"   Ошибки: {channel.get('error_count', 0)}")
    
    # Получаем категории канала
    try:
        cat_response = requests.get(f'http://localhost:8000/api/channels/{channel["id"]}/categories')
        if cat_response.status_code == 200:
            categories = cat_response.json()
            cat_names = [cat['name'] for cat in categories]
            print(f"   Категории: {', '.join(cat_names) if cat_names else 'Не назначены'}")
        else:
            print(f"   Категории: Ошибка получения ({cat_response.status_code})")
    except Exception as e:
        print(f"   Категории: Ошибка - {e}")

print(f"\n💡 На скриншоте показан канал:")
print(f"   Название: НЕВЗОРОВ")
print(f"   Подписчики: 1 106 040")
print(f"   Есть посты от 'Today'")
print(f"\n🔧 Проверьте:")
print(f"   1. Совпадает ли username канала в админке с реальным каналом")
print(f"   2. Правильный ли Telegram ID")
print(f"   3. Нет ли дубликатов каналов Невзорова") 