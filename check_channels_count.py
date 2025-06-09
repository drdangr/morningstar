import requests

try:
    response = requests.get('http://localhost:8000/api/channels')
    channels = response.json()
    
    print(f"Всего каналов в базе: {len(channels)}")
    print("\nСписок каналов:")
    for i, ch in enumerate(channels):
        print(f"{i+1}. {ch['title']} (ID: {ch['id']}, Telegram ID: {ch['telegram_id']})")
        
except Exception as e:
    print(f"Ошибка: {e}") 