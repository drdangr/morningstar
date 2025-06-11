#!/usr/bin/env python3
"""
Скрипт для проверки каналов в posts_cache таблице
"""

import requests
import json

def check_posts_cache_channels():
    """Проверяем какие каналы есть в posts_cache"""
    
    try:
        # Получаем статистику posts_cache
        response = requests.get('http://localhost:8000/api/posts/stats')
        response.raise_for_status()
        data = response.json()
        
        print("📊 СТАТИСТИКА POSTS_CACHE:")
        print(f"Всего постов: {data['total_posts']}")
        print(f"Каналов в базе: {len(data['channels'])}")
        print()
        
        print("🔍 ДЕТАЛИЗАЦИЯ ПО КАНАЛАМ:")
        for i, channel in enumerate(data['channels'], 1):
            print(f"{i}. Telegram ID: {channel['telegram_id']}")
            print(f"   Title: {channel.get('title', 'N/A')}")
            print(f"   Username: {channel.get('username', 'N/A')}")  
            print(f"   Постов: {channel['posts_count']}")
            print(f"   Последний сбор: {channel['last_collected']}")
            print(f"   Макс просмотров: {channel.get('max_views', 0):,}")
            print()
        
        # Получаем статистику активных каналов
        print("🔍 АКТИВНЫЕ КАНАЛЫ ИЗ CHANNELS ТАБЛИЦЫ:")
        response2 = requests.get('http://localhost:8000/api/channels?active_only=true')
        response2.raise_for_status()
        channels_data = response2.json()
        
        print(f"Активных каналов в channels: {len(channels_data)}")
        for channel in channels_data:
            print(f"- {channel['title']} (@{channel['username']}) - ID: {channel['telegram_id']}")
        
        print()
        print("❓ АНАЛИЗ РАСХОЖДЕНИЯ:")
        posts_cache_ids = {c['telegram_id'] for c in data['channels']}
        active_channel_ids = {c['telegram_id'] for c in channels_data}
        
        extra_in_cache = posts_cache_ids - active_channel_ids
        if extra_in_cache:
            print(f"⚠️ В posts_cache есть данные от каналов, которых НЕТ в активных:")
            for telegram_id in extra_in_cache:
                cache_channel = next(c for c in data['channels'] if c['telegram_id'] == telegram_id)
                print(f"   - ID: {telegram_id}, Постов: {cache_channel['posts_count']}")
        else:
            print("✅ Все каналы из posts_cache соответствуют активным каналам")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_posts_cache_channels() 