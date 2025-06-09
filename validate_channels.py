import asyncio
from telethon import TelegramClient
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Telegram API данные
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

async def validate_all_channels():
    """Валидация всех каналов в системе через Telegram API"""
    client = TelegramClient('userbot/session/userbot', API_ID, API_HASH)
    await client.start()
    
    print("🔍 Получаем все каналы из базы данных...")
    
    # Получаем каналы из Backend API
    response = requests.get('http://localhost:8000/api/channels')
    channels = response.json()
    
    print(f"📋 Найдено {len(channels)} каналов для проверки\n")
    
    validation_results = []
    
    for channel in channels:
        print(f"🔍 Проверяю канал: {channel['title']}")
        print(f"   База данных: username={channel.get('username')}, telegram_id={channel.get('telegram_id')}")
        
        result = {
            'id': channel['id'],
            'title_db': channel['title'],
            'username_db': channel.get('username'),
            'telegram_id': channel.get('telegram_id'),
            'status': 'unknown',
            'real_data': {},
            'recommendations': []
        }
        
        try:
            # Пробуем получить данные по telegram_id
            if channel.get('telegram_id'):
                entity = await client.get_entity(channel['telegram_id'])
                
                result['real_data'] = {
                    'title': entity.title,
                    'username': f"@{entity.username}" if entity.username else None,
                    'participants_count': getattr(entity, 'participants_count', 'Неизвестно'),
                    'verified': getattr(entity, 'verified', False)
                }
                
                # Проверяем соответствие данных
                db_username = channel.get('username')
                real_username = result['real_data']['username']
                
                if db_username != real_username:
                    result['status'] = 'username_mismatch'
                    result['recommendations'].append(f"Обновить username: {db_username} → {real_username}")
                    print(f"   ⚠️  НЕСООТВЕТСТВИЕ username: {db_username} → {real_username}")
                else:
                    result['status'] = 'ok'
                    print(f"   ✅ Данные корректны")
                
                if channel['title'] != entity.title:
                    result['recommendations'].append(f"Обновить название: {channel['title']} → {entity.title}")
                    print(f"   💡 Можно обновить название: {channel['title']} → {entity.title}")
                
                print(f"   📊 Подписчики: {result['real_data']['participants_count']}")
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"   ❌ Ошибка: {e}")
        
        validation_results.append(result)
        print()
    
    await client.disconnect()
    
    # Формируем отчет
    print("📋 ОТЧЕТ ПО ВАЛИДАЦИИ:")
    print("=" * 50)
    
    issues_found = 0
    for result in validation_results:
        if result['status'] in ['username_mismatch', 'error']:
            issues_found += 1
            print(f"\n🔧 {result['title_db']} (ID: {result['id']})")
            print(f"   Статус: {result['status']}")
            if result.get('recommendations'):
                for rec in result['recommendations']:
                    print(f"   💡 {rec}")
            if result.get('error'):
                print(f"   ❌ Ошибка: {result['error']}")
    
    if issues_found == 0:
        print("\n✅ Все каналы корректны!")
    else:
        print(f"\n⚠️  Найдено проблем: {issues_found}")
    
    print(f"\n📊 Сводка:")
    print(f"   Всего каналов: {len(validation_results)}")
    print(f"   Корректных: {len([r for r in validation_results if r['status'] == 'ok'])}")
    print(f"   С ошибками username: {len([r for r in validation_results if r['status'] == 'username_mismatch'])}")
    print(f"   Недоступных: {len([r for r in validation_results if r['status'] == 'error'])}")
    
    return validation_results

if __name__ == "__main__":
    results = asyncio.run(validate_all_channels()) 