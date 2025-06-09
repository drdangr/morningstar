import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import aiohttp
import json

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/userbot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
SESSION_NAME = 'session/morningstar'
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
N8N_WEBHOOK_TOKEN = os.getenv('N8N_WEBHOOK_TOKEN')

# Тестовые каналы для MVP
TEST_CHANNELS = [
    '@durov',  # Канал Павла Дурова
    '@telegram',  # Официальный канал Telegram
    # Добавь свои тестовые каналы
]


class MorningStarUserbot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.session = None
        
    async def start(self):
        """Запуск и авторизация userbot"""
        try:
            await self.client.start(phone=PHONE)
            logger.info("Userbot успешно авторизован!")
            
            # Получаем информацию о себе
            me = await self.client.get_me()
            logger.info(f"Авторизован как: {me.first_name} (@{me.username})")
            
        except SessionPasswordNeededError:
            logger.error("Требуется двухфакторная аутентификация!")
            # В продакшене добавить обработку 2FA
            raise
        except Exception as e:
            logger.error(f"Ошибка при запуске: {e}")
            raise
    
    async def get_channel_posts(self, channel_username, hours=24):
        """Получение постов из канала за последние N часов"""
        try:
            # Получаем entity канала
            channel = await self.client.get_entity(channel_username)
            logger.info(f"Читаю канал: {channel.title}")
            
            # Временная метка для фильтрации
            time_limit = datetime.now() - timedelta(hours=hours)
            
            posts = []
            # Получаем последние сообщения
            async for message in self.client.iter_messages(channel, limit=50):
                # Фильтруем по времени
                if message.date.replace(tzinfo=None) < time_limit:
                    break
                    
                # Пропускаем пустые сообщения
                if not message.text and not message.media:
                    continue
                
                post_data = {
                    'id': message.id,
                    'channel_id': channel.id,
                    'channel_title': channel.title,
                    'text': message.text or '',
                    'date': message.date.isoformat(),
                    'views': message.views or 0,
                    'forwards': message.forwards or 0,
                }
                
                # Обработка медиа
                if message.media:
                    if hasattr(message.media, 'photo'):
                        post_data['media_type'] = 'photo'
                    elif hasattr(message.media, 'document'):
                        post_data['media_type'] = 'document'
                    else:
                        post_data['media_type'] = 'other'
                
                posts.append(post_data)
            
            logger.info(f"Получено {len(posts)} постов из {channel.title}")
            return posts
            
        except Exception as e:
            logger.error(f"Ошибка при чтении канала {channel_username}: {e}")
            return []
    
    async def send_to_n8n(self, data):
        """Отправка данных в n8n webhook"""
        if not N8N_WEBHOOK_URL:
            logger.warning("N8N_WEBHOOK_URL не настроен, пропускаю отправку")
            return
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {N8N_WEBHOOK_TOKEN}' if N8N_WEBHOOK_TOKEN else ''
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    N8N_WEBHOOK_URL,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Данные успешно отправлены в n8n")
                    else:
                        logger.error(f"Ошибка отправки в n8n: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка при отправке в n8n: {e}")
    
    async def collect_and_send(self):
        """Основной цикл сбора и отправки данных"""
        all_posts = []
        
        for channel in TEST_CHANNELS:
            logger.info(f"Обрабатываю канал: {channel}")
            posts = await self.get_channel_posts(channel, hours=24)
            all_posts.extend(posts)
            
            # Небольшая задержка между каналами
            await asyncio.sleep(2)
        
        # Отправляем данные в n8n
        if all_posts:
            await self.send_to_n8n({
                'timestamp': datetime.now().isoformat(),
                'posts_count': len(all_posts),
                'posts': all_posts
            })
        
        logger.info(f"Всего собрано {len(all_posts)} постов")
        return all_posts
    
    async def run(self):
        """Запуск userbot в режиме периодического сбора"""
        await self.start()
        
        # Для MVP - однократный сбор
        logger.info("Запуск сбора постов...")
        await self.collect_and_send()
        
        # В будущем здесь будет цикл с периодическим сбором
        # while True:
        #     await self.collect_and_send()
        #     await asyncio.sleep(1800)  # 30 минут
        
        logger.info("Сбор завершен!")


async def main():
    """Точка входа"""
    userbot = MorningStarUserbot()
    
    try:
        await userbot.run()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        await userbot.client.disconnect()
        logger.info("Userbot остановлен")


if __name__ == "__main__":
    asyncio.run(main())