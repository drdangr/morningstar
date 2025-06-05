import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError

# Улучшенный поиск и загрузка .env файла
def find_and_load_env():
    """Поиск .env файла в разных местах с подробной диагностикой"""
    # Определяем базовые пути
    current_file = Path(__file__).resolve()
    current_dir = current_file.parent  # userbot/src
    userbot_dir = current_dir.parent   # userbot
    project_root = userbot_dir.parent  # MorningStarBot3
    
    # Список путей для поиска
    possible_paths = [
        current_dir / '.env',              # userbot/src/.env
        userbot_dir / '.env',              # userbot/.env
        project_root / '.env',             # MorningStarBot3/.env
        Path('.env'),                      # текущая папка
        Path('../.env'),                   # папка выше
        Path('../../.env'),                # две папки выше
    ]
    
    print("🔍 Поиск .env файла...")
    print(f"📂 Текущий файл: {current_file}")
    print(f"📂 Корень проекта: {project_root}")
    
    for i, env_path in enumerate(possible_paths, 1):
        abs_path = env_path.resolve()
        print(f"   {i}. Проверяю: {abs_path}")
        
        if abs_path.exists():
            print(f"✅ Найден .env файл: {abs_path}")
            load_dotenv(abs_path)
            
            # Проверяем что переменные загрузились
            test_vars = ['API_ID', 'API_HASH', 'PHONE']
            loaded_vars = {var: os.getenv(var) for var in test_vars}
            
            print("📋 Проверка загруженных переменных:")
            for var, value in loaded_vars.items():
                status = "✅" if value else "❌"
                display_value = f"{value[:10]}..." if value and len(str(value)) > 10 else value
                print(f"   {status} {var}: {display_value}")
            
            if all(loaded_vars.values()):
                print("🎉 Все переменные успешно загружены!")
                return True
            else:
                print("⚠️ Файл найден, но не все переменные загружены")
                continue
    
    print("❌ .env файл не найден или переменные не загружены")
    print("💡 Проверенные пути:")
    for path in possible_paths:
        print(f"   - {path.resolve()}")
    
    # Попытка найти любые .env файлы в проекте
    print("\n🔍 Поиск всех .env файлов в проекте:")
    try:
        for env_file in project_root.rglob('.env'):
            print(f"   🔍 Найден: {env_file}")
    except Exception as e:
        print(f"   ❌ Ошибка поиска: {e}")
    
    return False

# Загрузка переменных окружения
print("🚀 Запуск MorningStar Userbot...")
if not find_and_load_env():
    print("\n💡 Решения:")
    print("   1. Скопируйте .env в папку userbot/src/")
    print("   2. Или убедитесь что .env находится в корне проекта")
    print("   3. Проверьте содержимое .env файла")
    sys.exit(1)

# Определение путей для логов и сессий
def get_app_paths():
    """Получение путей для приложения в зависимости от среды выполнения"""
    if os.path.exists('/app'):  # Docker среда
        logs_dir = Path('/app/logs')
        session_dir = Path('/app/session')
    else:  # Локальная разработка
        base_dir = Path(__file__).parent.parent  # userbot/
        logs_dir = base_dir / 'logs'
        session_dir = base_dir / 'session'
    
    # Создаем директории если их нет
    logs_dir.mkdir(exist_ok=True)
    session_dir.mkdir(exist_ok=True)
    
    return logs_dir, session_dir

LOGS_DIR, SESSION_DIR = get_app_paths()

# Настройка логирования
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "userbot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Включаем отладочные логи если нужно
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
if DEBUG_MODE:
    logging.getLogger().setLevel(logging.DEBUG)
    print("🔍 Включен режим отладки")

# Валидация и загрузка конфигурации
try:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    PHONE = os.getenv("PHONE", "")

    # Проверка обязательных параметров
    if not all([API_ID, API_HASH, PHONE]):
        raise ValueError(
            "Не все обязательные переменные окружения установлены: API_ID, API_HASH, PHONE"
        )

    if API_ID == 0:
        raise ValueError("API_ID должен быть числом больше 0")

except ValueError as e:
    logger.error("❌ Ошибка конфигурации: %s", e)
    logger.error("💡 Проверьте файл .env и убедитесь, что все переменные установлены корректно")
    logger.error("📋 Необходимые переменные: API_ID, API_HASH, PHONE")
    print("\n🔧 Для диагностики запустите снова - будет показан подробный поиск .env")
    sys.exit(1)

# Пути с адаптацией под среду
SESSION_NAME = str(SESSION_DIR / "morningstar")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
N8N_WEBHOOK_TOKEN = os.getenv("N8N_WEBHOOK_TOKEN", "")

# Получение каналов из переменных окружения или использование по умолчанию
CHANNELS_ENV = os.getenv("CHANNELS", "")
print(f"🔍 CHANNELS_ENV из .env: '{CHANNELS_ENV}'")

if CHANNELS_ENV:
    TEST_CHANNELS = [ch.strip() for ch in CHANNELS_ENV.split(",") if ch.strip()]
else:
    TEST_CHANNELS = [
        "@rt_russian",
        "@rian_ru", 
        "@lentachold"
    ]

print(f"📡 Итоговые каналы: {TEST_CHANNELS}")

logger.info("📁 Логи сохраняются в: %s", LOGS_DIR)
logger.info("💾 Сессия сохраняется в: %s", SESSION_DIR)
logger.info("📡 Настроенные каналы: %s", TEST_CHANNELS)
logger.info("🔗 N8N Webhook: %s", "✅ Настроен" if N8N_WEBHOOK_URL else "❌ Не настроен")


class MorningStarUserbot:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.session = None
        self.me = None

    async def start(self):
        """Запуск и авторизация userbot"""
        try:
            logger.info("🚀 Запуск userbot...")
            await self.client.start(phone=PHONE)
            logger.info("✅ Userbot успешно авторизован!")

            # Получаем информацию о себе
            self.me = await self.client.get_me()
            username = self.me.username or "No username"
            logger.info("👤 Авторизован как: %s (@%s)", self.me.first_name, username)
            return True

        except SessionPasswordNeededError:
            logger.error("🔐 Требуется двухфакторная аутентификация!")
            logger.error(
                "💡 Установите пароль через переменную окружения TWO_FACTOR_PASSWORD"
            )
            raise
        except FloodWaitError as e:
            logger.error("⏰ Превышен лимит запросов. Ждите %s секунд", e.seconds)
            raise
        except Exception as e:
            logger.error("💥 Ошибка при запуске: %s", e)
            raise

    async def get_channel_info(self, channel_username):
        """Получение информации о канале"""
        try:
            channel = await self.client.get_entity(channel_username)
            logger.debug("📺 Канал найден: %s (ID: %s)", channel.title, channel.id)
            return channel
        except Exception as e:
            logger.error(
                "❌ Ошибка получения информации о канале %s: %s", channel_username, e
            )
            return None

    async def get_channel_posts(self, channel_username, hours=72):
        """Получение постов из канала за последние N часов"""
        try:
            # Получаем entity канала
            channel = await self.get_channel_info(channel_username)
            if not channel:
                return []

            logger.info("📖 Читаю канал: %s", channel.title)

            # Временная метка для фильтрации
            time_limit = datetime.now() - timedelta(hours=hours)

            posts = []
            message_count = 0

            # Получаем последние сообщения (увеличили лимит)
            async for message in self.client.iter_messages(channel, limit=200):
                message_count += 1

                # Фильтруем по времени
                try:
                    message_date = message.date.replace(tzinfo=None)
                    if message_date < time_limit:
                        logger.debug(
                            "⏰ Сообщение %s слишком старое: %s", message.id, message_date
                        )
                        break
                except Exception as e:
                    logger.debug("⚠️ Ошибка обработки даты сообщения %s: %s", message.id, e)
                    continue

                # Пропускаем пустые сообщения
                if not message.text and not message.media:
                    logger.debug("⏭️ Пропускаю пустое сообщение %s", message.id)
                    continue

                post_data = {
                    "id": message.id,
                    "channel_id": channel.id,
                    "channel_username": channel_username,
                    "channel_title": channel.title,
                    "text": message.text or "",
                    "date": message.date.isoformat(),
                    "views": message.views or 0,
                    "forwards": message.forwards or 0,
                    "replies": 0,  # Безопасное значение по умолчанию
                    "url": f"https://t.me/{channel_username.replace('@', '')}/{message.id}",
                    "media_type": "text"  # Значение по умолчанию
                }

                # Безопасная обработка replies
                try:
                    if hasattr(message, "replies") and message.replies is not None:
                        replies_count = getattr(message.replies, "replies", 0)
                        post_data["replies"] = replies_count if replies_count else 0
                except Exception as e:
                    logger.debug("⚠️ Ошибка обработки replies для сообщения %s: %s", message.id, e)

                # Безопасная обработка медиа
                try:
                    if message.media:
                        if hasattr(message.media, "photo"):
                            post_data["media_type"] = "photo"
                        elif hasattr(message.media, "document") and message.media.document:
                            mime_type = getattr(message.media.document, "mime_type", "")
                            if mime_type:
                                if "video" in mime_type:
                                    post_data["media_type"] = "video"
                                elif "audio" in mime_type:
                                    post_data["media_type"] = "audio"
                                else:
                                    post_data["media_type"] = "document"
                            else:
                                post_data["media_type"] = "document"
                        else:
                            post_data["media_type"] = "other"
                except Exception as e:
                    logger.debug("⚠️ Ошибка обработки медиа для сообщения %s: %s", message.id, e)

                posts.append(post_data)
                
                # Логируем каждый найденный пост
                logger.debug("📝 Найден пост %s: %s", message.id, (message.text or "")[:100])

            logger.info(
                "✅ Получено %s постов из %s (проверено %s сообщений за %s часов)",
                len(posts),
                channel.title,
                message_count,
                hours,
            )
            return posts

        except FloodWaitError as e:
            logger.warning(
                "⏰ Rate limit для канала %s. Ждем %s секунд",
                channel_username,
                e.seconds,
            )
            await asyncio.sleep(e.seconds)
            return []
        except Exception as e:
            logger.error("❌ Ошибка при чтении канала %s: %s", channel_username, e)
            logger.exception("Полная трассировка ошибки:")  # Добавляем полную трассировку
            return []

    async def send_to_n8n(self, data):
        """Отправка данных в n8n webhook"""
        if not N8N_WEBHOOK_URL:
            logger.warning("⚠️ N8N_WEBHOOK_URL не настроен, пропускаю отправку")
            return False

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MorningStarUserbot/1.0",
        }

        if N8N_WEBHOOK_TOKEN:
            headers["Authorization"] = f"Bearer {N8N_WEBHOOK_TOKEN}"

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.debug("📤 Отправляю данные в n8n: %s", N8N_WEBHOOK_URL)

                async with session.post(
                    N8N_WEBHOOK_URL, json=data, headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(
                            "✅ Данные успешно отправлены в n8n: %s", response.status
                        )
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(
                            "❌ Ошибка отправки в n8n: %s - %s",
                            response.status,
                            response_text,
                        )
                        return False

        except asyncio.TimeoutError:
            logger.error("⏰ Timeout при отправке в n8n")
            return False
        except Exception as e:
            logger.error("💥 Ошибка при отправке в n8n: %s", e)
            return False

    async def collect_and_send(self):
        """Основной цикл сбора и отправки данных"""
        all_posts = []
        successful_channels = 0
        failed_channels = 0

        logger.info("📊 Начинаю сбор постов из %s каналов...", len(TEST_CHANNELS))

        for i, channel in enumerate(TEST_CHANNELS):
            logger.info(
                "📺 Обрабатываю канал %s/%s: %s", i + 1, len(TEST_CHANNELS), channel
            )

            try:
                posts = await self.get_channel_posts(channel, hours=72)  # Увеличили до 72 часов
                if posts:
                    all_posts.extend(posts)
                    successful_channels += 1
                    logger.info("✅ %s: получено %s постов", channel, len(posts))
                else:
                    logger.warning("⚠️ %s: постов не найдено", channel)

            except Exception as e:
                failed_channels += 1
                logger.error("❌ %s: ошибка - %s", channel, e)

            # Задержка между каналами для избежания rate limits
            if i < len(TEST_CHANNELS) - 1:  # Не ждем после последнего канала
                await asyncio.sleep(3)

        logger.info(
            "📈 Сбор завершен: успешно %s, ошибок %s",
            successful_channels,
            failed_channels,
        )

        # Отправляем данные в n8n
        if all_posts:
            webhook_data = {
                "timestamp": datetime.now().isoformat(),
                "collection_stats": {
                    "total_posts": len(all_posts),
                    "successful_channels": successful_channels,
                    "failed_channels": failed_channels,
                    "channels_processed": TEST_CHANNELS,
                },
                "posts": all_posts,
            }

            success = await self.send_to_n8n(webhook_data)
            if success:
                logger.info("📤 Отправлено %s постов в n8n", len(all_posts))
            else:
                logger.error("❌ Ошибка отправки в n8n")
        else:
            logger.warning("⚠️ Нет постов для отправки")

        return all_posts

    async def run_once(self):
        """Однократный запуск сбора данных"""
        await self.start()
        logger.info("🚀 Запуск однократного сбора постов...")
        posts = await self.collect_and_send()
        logger.info("✅ Сбор завершен! Всего постов: %s", len(posts))
        return posts

    async def run_periodic(self, interval_minutes=30):
        """Запуск в режиме периодического сбора"""
        await self.start()

        logger.info("🔄 Запуск периодического сбора каждые %s минут", interval_minutes)

        while True:
            try:
                logger.info("📊 Начинаю периодический сбор...")
                posts = await self.collect_and_send()
                logger.info("✅ Цикл завершен! Собрано постов: %s", len(posts))

                # Ожидание до следующего цикла
                sleep_seconds = interval_minutes * 60
                logger.info(
                    "😴 Ожидание %s минут до следующего сбора...", interval_minutes
                )
                await asyncio.sleep(sleep_seconds)

            except KeyboardInterrupt:
                logger.info("⏹️ Получен сигнал остановки")
                break
            except Exception as e:
                logger.error("💥 Ошибка в периодическом цикле: %s", e)
                logger.info("⏳ Жду 5 минут перед повтором...")
                await asyncio.sleep(300)  # 5 минут

    async def run(self):
        """Запуск userbot в режиме, определенном переменными окружения"""
        mode = os.getenv("USERBOT_MODE", "once")  # 'once' или 'periodic'
        interval = (
            int(os.getenv("POLLING_INTERVAL", 1800)) // 60
        )  # Конвертируем секунды в минуты

        logger.info("🎯 Режим работы: %s", mode)

        if mode == "periodic":
            await self.run_periodic(interval_minutes=interval)
        else:
            await self.run_once()

    async def disconnect(self):
        """Отключение клиента"""
        try:
            await self.client.disconnect()
            logger.info("🔌 Userbot отключен")
        except Exception as e:
            logger.error("❌ Ошибка при отключении: %s", e)


async def main():
    """Точка входа"""
    userbot = MorningStarUserbot()

    try:
        await userbot.run()
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error("💥 Критическая ошибка: %s", e)
        raise
    finally:
        await userbot.disconnect()


if __name__ == "__main__":
    logger.info("🌅 MorningStar Userbot v1.0")
    asyncio.run(main())
