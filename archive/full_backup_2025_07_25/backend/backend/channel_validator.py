"""
Модуль валидации и автозаполнения данных каналов
"""
import asyncio
import re
from telethon import TelegramClient
from telethon.errors import UsernameNotOccupiedError, UsernameInvalidError
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API данные (можно вынести в конфиг)
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE = os.getenv('PHONE', '')

class ChannelValidator:
    """Валидатор и автозаполнятель данных каналов"""
    
    def __init__(self):
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = TelegramClient('../userbot/session/morningstar', API_ID, API_HASH)
        await self.client.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.disconnect()
    
    def parse_channel_input(self, user_input: str) -> dict:
        """
        Парсинг пользовательского ввода и извлечение идентификатора канала
        
        Поддерживаемые форматы:
        - @username
        - username  
        - https://t.me/username
        - t.me/username
        - 1001234567890 (telegram_id)
        """
        user_input = user_input.strip()
        result = {
            'input_type': 'unknown',
            'identifier': None,
            'username': None,
            'telegram_id': None
        }
        
        # 1. Проверяем telegram_id (только цифры, длина больше или равна 10 символов)
        if user_input.isdigit() and len(user_input) >= 10:
            result['input_type'] = 'telegram_id'
            result['telegram_id'] = int(user_input)
            result['identifier'] = int(user_input)  # Для ID не добавляем @
            return result
        
        # 2. Извлекаем username из различных форматов
        tme_patterns = [
            r'https?://t\.me/([a-zA-Z0-9_]+)',
            r't\.me/([a-zA-Z0-9_]+)',
            r'@([a-zA-Z0-9_]+)',
            r'^([a-zA-Z0-9_]+)$'
        ]
        
        for pattern in tme_patterns:
            match = re.match(pattern, user_input)
            if match:
                username = match.group(1)
                result['input_type'] = 'username'
                result['username'] = f"@{username}"
                result['identifier'] = f"@{username}"  # Для username добавляем @
                break
        
        return result
    
    async def suggest_channel_data(self, user_input: str) -> dict:
        """
        Предложение данных для заполнения формы канала
        
        Returns:
        {
            'suggestions': {
                'title': str,
                'username': str,
                'telegram_id': int,
                'description': str,
                'is_active': bool
            },
            'validation': {
                'valid': bool,
                'warnings': [str],
                'info': [str]
            }
        }
        """
        result = {
            'suggestions': {},
            'validation': {
                'valid': False,
                'warnings': [],
                'info': []
            }
        }
        
        try:
            parsed = self.parse_channel_input(user_input)
            
            if not parsed['identifier']:
                result['validation']['warnings'].append('Неподдерживаемый формат ввода')
                return result
            
            entity = await self.client.get_entity(parsed['identifier'])
            
            if not hasattr(entity, 'broadcast') or not entity.broadcast:
                result['validation']['warnings'].append('Указанный объект не является каналом')
                return result
            
            result['suggestions'] = {
                'title': entity.title,
                'username': f"@{entity.username}" if entity.username else None,
                'telegram_id': entity.id,
                'description': getattr(entity, 'about', None) or f"Канал {entity.title}",
                'is_active': True
            }
            
            result['validation']['valid'] = True
            result['validation']['info'].append(f"✅ Канал найден: {entity.title}")
            result['validation']['info'].append(f"📊 Подписчиков: {getattr(entity, 'participants_count', 0):,}")
            
            if getattr(entity, 'verified', False):
                result['validation']['info'].append("✅ Верифицированный канал")
            
            if not entity.username:
                result['validation']['warnings'].append("⚠️ У канала нет публичного username")
                
        except UsernameNotOccupiedError:
            result['validation']['warnings'].append('Канал с таким username не найден')
        except Exception as e:
            result['validation']['warnings'].append(f'Ошибка: {str(e)}')
        
        return result


# Функция для использования в FastAPI endpoints
async def validate_channel_for_api(user_input: str) -> dict:
    """Функция-обертка для использования в FastAPI"""
    async with ChannelValidator() as validator:
        return await validator.suggest_channel_data(user_input) 