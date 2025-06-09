import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API данные
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

async def check_channel_info():
    client = TelegramClient('session/userbot', API_ID, API_HASH)
    await client.start()
    
    print("🔍 Проверяем реальные данные каналов Невзорова:")
    
    # Проверяем каналы по username
    channels_to_check = [
        "@nevzorovpodcast",  # Что у нас в базе
        "@nevzorovtv",       # Возможный основной канал  
        "@nevzorov",         # Простой вариант
        "@nevzorovofficial", # Официальный
    ]
    
    for username in channels_to_check:
        try:
            entity = await client.get_entity(username)
            print(f"\n✅ {username}:")
            print(f"   ID: {entity.id}")
            print(f"   Название: {entity.title}")
            print(f"   Подписчики: {getattr(entity, 'participants_count', 'Неизвестно')}")
            
            # Проверяем последние сообщения
            messages = await client.get_messages(entity, limit=5)
            recent_count = 0
            for msg in messages:
                if msg.date and (msg.date.day == 9):  # Сегодня 9 июня
                    recent_count += 1
            print(f"   Постов сегодня: {recent_count}")
            
        except Exception as e:
            print(f"\n❌ {username}: {str(e)}")
    
    # Проверяем конкретный канал из нашей базы
    print(f"\n🎯 Проверяем канал из нашей базы (ID: 1001231519967):")
    try:
        entity = await client.get_entity(1001231519967)
        print(f"   Реальный username: @{entity.username}")
        print(f"   Название: {entity.title}")
        print(f"   Подписчики: {getattr(entity, 'participants_count', 'Неизвестно')}")
        
        # Сообщения за сегодня
        messages = await client.get_messages(entity, limit=10)
        today_messages = []
        for msg in messages:
            if msg.date and msg.date.day == 9:  # Сегодня
                today_messages.append(msg)
        
        print(f"   Сообщений сегодня: {len(today_messages)}")
        for i, msg in enumerate(today_messages):
            text = (msg.text or "Медиа-пост")[:50]
            print(f"   {i+1}. {text}...")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_channel_info()) 