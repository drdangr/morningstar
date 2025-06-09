import requests
import json

# Получаем все каналы
response = requests.get('http://localhost:8000/api/channels')
channels = response.json()

print(f"Всего каналов в базе: {len(channels)}")
print(f"Активных каналов: {len([c for c in channels if c.get('is_active')])}")
print("\nДетальная информация о каналах:")

for i, channel in enumerate(channels, 1):
    print(f"\n{i}. {channel['title']}")
    print(f"   Username: {channel.get('username', 'Не указано')}")
    print(f"   Telegram ID: {channel.get('telegram_id', 'Не указано')}")
    print(f"   Активен: {'✅' if channel.get('is_active') else '❌'}")
    print(f"   Последний парсинг: {channel.get('last_parsed', 'Никогда')}")
    print(f"   Ошибки: {channel.get('error_count', 0)}")

# Проверяем что получает userbot
print(f"\n🤖 Проверяем что получает userbot (активные каналы):")
userbot_response = requests.get('http://localhost:8000/api/channels?active_only=true')
if userbot_response.status_code == 200:
    userbot_channels = userbot_response.json()
    print(f"Userbot получает {len(userbot_channels)} каналов:")
    for channel in userbot_channels:
        print(f"  📺 {channel['title']} (ID: {channel['telegram_id']})")
else:
    print(f"❌ Ошибка получения каналов для userbot: {userbot_response.status_code}") 