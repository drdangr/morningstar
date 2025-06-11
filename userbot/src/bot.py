import asyncio
import json
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
            
            # Проверяем содержимое .env файла для N8N_WEBHOOK_URL
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if line.strip().startswith('N8N_WEBHOOK_URL='):
                            print(f"📄 В .env файле найдено: {line.strip()}")
                            break
                    else:
                        print("📄 N8N_WEBHOOK_URL не найден в .env файле")
            except Exception as e:
                print(f"❌ Ошибка чтения .env файла: {e}")
            
            load_dotenv(abs_path, override=True)  # Добавляем override=True
            print(f"🔄 .env файл загружен с override=True")
            
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

# Детальная диагностика N8N_WEBHOOK_URL
print("🔍 Диагностика N8N_WEBHOOK_URL:")
print(f"   📋 Значение из os.getenv(): '{os.getenv('N8N_WEBHOOK_URL', 'НЕТ')}'")
print(f"   📋 Есть ли в os.environ: {'N8N_WEBHOOK_URL' in os.environ}")
if 'N8N_WEBHOOK_URL' in os.environ:
    print(f"   📋 Значение из os.environ: '{os.environ['N8N_WEBHOOK_URL']}'")

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/telegram-posts")
N8N_WEBHOOK_TOKEN = os.getenv("N8N_WEBHOOK_TOKEN", "")

print(f"   ✅ Финальное значение N8N_WEBHOOK_URL: '{N8N_WEBHOOK_URL}'")

# Настройки Backend API
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Детальная диагностика TEST_MODE
TEST_MODE_RAW = os.getenv("TEST_MODE", "true")
print(f"🔍 TEST_MODE диагностика:")
print(f"   📋 Сырое значение из .env: '{TEST_MODE_RAW}'")
print(f"   📋 Тип значения: {type(TEST_MODE_RAW)}")
print(f"   📋 Длина строки: {len(TEST_MODE_RAW)}")
print(f"   📋 После .lower(): '{TEST_MODE_RAW.lower()}'")
print(f"   📋 Сравнение с 'true': {TEST_MODE_RAW.lower()} == 'true' = {TEST_MODE_RAW.lower() == 'true'}")

TEST_MODE = TEST_MODE_RAW.lower() == "true"
print(f"   ✅ Финальное значение TEST_MODE: {TEST_MODE}")

# Получение каналов из переменных окружения (fallback для тестирования)
CHANNELS_ENV = os.getenv("CHANNELS", "")
print(f"🔍 CHANNELS_ENV из .env: '{CHANNELS_ENV}'")

FALLBACK_CHANNELS = []
if CHANNELS_ENV:
    FALLBACK_CHANNELS = [ch.strip() for ch in CHANNELS_ENV.split(",") if ch.strip()]
else:
    FALLBACK_CHANNELS = [
        "@rt_russian",
        "@rian_ru", 
        "@lentachold"
    ]

print(f"🌐 Backend API: {BACKEND_API_URL}")
print(f"🧪 Режим тестирования: {TEST_MODE}")
print(f"📡 Fallback каналы: {FALLBACK_CHANNELS}")
print(f"🔗 N8N Webhook URL: {N8N_WEBHOOK_URL}")

logger.info("📁 Логи сохраняются в: %s", LOGS_DIR)
logger.info("💾 Сессия сохраняется в: %s", SESSION_DIR)
logger.info("🌐 Backend API: %s", BACKEND_API_URL)
logger.info("🧪 Режим тестирования: %s", TEST_MODE)
logger.info("🔗 N8N Webhook: %s", "✅ Настроен" if N8N_WEBHOOK_URL else "❌ Не настроен")
logger.info("📡 N8N Webhook URL: %s", N8N_WEBHOOK_URL or "НЕ ЗАДАН")


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

    async def get_config_value(self, key: str, default=None):
        """Получение значения конфигурации из Backend API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BACKEND_API_URL}/api/config/{key}") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📋 Получена настройка {key}: {data.get('value', default)}")
                        return data.get('value', default)
                    else:
                        logger.warning(f"⚠️ Настройка {key} не найдена, используем значение по умолчанию: {default}")
                        return default
        except Exception as e:
            logger.error(f"❌ Ошибка при получении настройки {key}: {e}")
            return default

    async def get_channels_from_api(self):
        """Получение списка активных каналов из Backend API с метаданными"""
        try:
            url = f"{BACKEND_API_URL}/api/channels"
            params = {"active_only": "true"}
            
            logger.info("🌐 Запрос каналов из Backend API: %s", url)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        channels_data = await response.json()
                        
                        # Сохраняем полную информацию о каналах с категориями
                        self.channels_metadata = {}
                        api_channels = []
                        
                        for channel in channels_data:
                            if channel.get('is_active', False):
                                username = channel.get('username')
                                if username:
                                    # Добавляем @ если его нет
                                    if not username.startswith('@'):
                                        username = f"@{username}"
                                    
                                    # Сохраняем метаданные канала включая категории
                                    self.channels_metadata[username] = {
                                        'id': channel.get('id'),
                                        'telegram_id': channel.get('telegram_id'),
                                        'title': channel.get('title'),
                                        'categories': channel.get('categories', [])
                                    }
                                    
                                    api_channels.append(username)
                                elif channel.get('telegram_id'):
                                    # Можно использовать telegram_id если нет username
                                    telegram_id = str(channel['telegram_id'])
                                    self.channels_metadata[telegram_id] = {
                                        'id': channel.get('id'),
                                        'telegram_id': channel.get('telegram_id'),
                                        'title': channel.get('title'),
                                        'categories': channel.get('categories', [])
                                    }
                                    api_channels.append(telegram_id)
                        
                        logger.info("✅ Получено %d активных каналов из API", len(api_channels))
                        logger.info("📡 Каналы из API: %s", api_channels)
                        
                        # Логируем категории для каждого канала
                        for username, metadata in self.channels_metadata.items():
                            categories = metadata.get('categories', [])
                            if categories:
                                category_names = [cat.get('name', 'N/A') for cat in categories]
                                logger.info("🏷️ %s → категории: %s", username, category_names)
                            else:
                                logger.warning("⚠️ %s → категории не найдены", username)
                        
                        return api_channels
                    
                    else:
                        logger.warning("⚠️ API вернул статус %d, используем fallback каналы", response.status)
                        self.channels_metadata = {}
                        return FALLBACK_CHANNELS
                        
        except Exception as e:
            logger.error("❌ Ошибка при получении каналов из API: %s", e)
            logger.info("🔄 Используем fallback каналы: %s", FALLBACK_CHANNELS)
            self.channels_metadata = {}
            return FALLBACK_CHANNELS

    async def get_channel_info(self, channel_identifier):
        """Получение информации о канале с fallback логикой"""
        # Получаем метаданные канала для fallback
        metadata = self.channels_metadata.get(channel_identifier, {})
        telegram_id = metadata.get('telegram_id')
        
        # Список способов подключения для fallback
        connection_methods = []
        
        # 1. Основной способ - как передан
        connection_methods.append(("основной", channel_identifier))
        
        # 2. Fallback к telegram_id если есть
        if telegram_id:
            connection_methods.append(("telegram_id", telegram_id))
        
        # 3. Если это t.me ссылка - извлекаем username
        if isinstance(channel_identifier, str) and "t.me/" in channel_identifier:
            username = channel_identifier.split("/")[-1]
            if username and not username.startswith("@"):
                username = f"@{username}"
            connection_methods.append(("t.me_link", username))
        
        # Пробуем все способы подключения
        for method_name, identifier in connection_methods:
            try:
                logger.debug("🔍 Пробую подключение (%s): %s", method_name, identifier)
                channel = await self.client.get_entity(identifier)
                logger.info("✅ Канал найден (%s): %s (ID: %s)", method_name, channel.title, channel.id)
                return channel
            except Exception as e:
                logger.debug("❌ Способ %s не сработал для %s: %s", method_name, identifier, e)
                continue
        
        logger.error("❌ Все способы подключения к каналу исчерпаны: %s", channel_identifier)
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

    async def send_to_backend(self, data):
        """Отправка данных в Backend API posts_cache"""
        # В режиме тестирования просто логируем данные
        if TEST_MODE:
            logger.info("🧪 ТЕСТОВЫЙ РЕЖИМ: данные для Backend API:")
            logger.info("📊 Статистика: %s", data.get('collection_stats', {}))
            logger.info("📝 Количество постов: %d", len(data.get('posts', [])))
            
            # Показываем примеры постов
            posts = data.get('posts', [])
            if posts:
                logger.info("📄 Примеры постов:")
                for i, post in enumerate(posts[:3]):  # Показываем первые 3 поста
                    logger.info("  %d. %s: %s", i+1, post.get('channel_title', 'N/A'), 
                               (post.get('text', '') or 'Без текста')[:100] + '...')
            
            return True
            
        BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        # Конвертируем данные в формат PostsBatchCreate
        posts_batch = {
            "timestamp": data.get("timestamp"),
            "collection_stats": data.get("collection_stats", {}),
            "posts": [],
            "channels_metadata": data.get("channels_metadata", {})
        }
        
        # Конвертируем каждый пост в формат PostCacheCreate
        for post in data.get("posts", []):
            post_cache = {
                "channel_telegram_id": post.get("channel_id"),
                "telegram_message_id": post.get("id"),
                "title": None,  # В userbot нет разделения title/content
                "content": post.get("text", ""),
                "media_urls": [post.get("url")] if post.get("url") else [],  # Массив URL, не JSON строка
                "views": post.get("views", 0),
                "post_date": post.get("date"),
                "processing_status": "pending"
            }
            posts_batch["posts"].append(post_cache)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MorningStarUserbot/1.0",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                backend_url = f"{BACKEND_API_URL}/api/posts/batch"
                logger.info("📤 Отправляю данные в Backend API: %s", backend_url)
                logger.debug("📊 Размер данных: %d постов", len(posts_batch["posts"]))

                async with session.post(
                    backend_url, json=posts_batch, headers=headers
                ) as response:
                    if response.status == 201:
                        response_json = await response.json()
                        logger.info(
                            "✅ Данные успешно отправлены в Backend: создано %s постов, пропущено %s",
                            response_json.get("created_posts", 0),
                            response_json.get("skipped_posts", 0)
                        )
                        return True
                    else:
                        response_text = await response.text()
                        logger.error(
                            "❌ Ошибка отправки в Backend API: %s - %s",
                            response.status,
                            response_text,
                        )
                        return False

        except asyncio.TimeoutError:
            logger.error("⏰ Timeout при отправке в Backend API")
            return False
        except Exception as e:
            logger.error("💥 Ошибка при отправке в Backend API: %s", e)
            return False

    async def collect_and_send(self):
        """Основной цикл сбора и отправки данных"""
        all_posts = []
        successful_channels = 0
        failed_channels = 0

        # Получаем настройки из Backend API
        collection_depth_days = await self.get_config_value("COLLECTION_DEPTH_DAYS", 3)
        max_posts_per_channel = await self.get_config_value("MAX_POSTS_PER_CHANNEL", 50)
        
        # Конвертируем дни в часы
        collection_hours = int(collection_depth_days) * 24
        max_posts_limit = int(max_posts_per_channel)
        
        logger.info("📋 Настройки сбора: %d дней (%d часов), максимум %d постов с канала", 
                   collection_depth_days, collection_hours, max_posts_limit)

        # Получаем список каналов из API
        channels = await self.get_channels_from_api()
        if not channels:
            logger.warning("⚠️ Нет активных каналов для сбора постов")
            return []

        logger.info("📊 Начинаю сбор постов из %s каналов...", len(channels))

        for i, channel in enumerate(channels):
            logger.info(
                "📺 Обрабатываю канал %s/%s: %s", i + 1, len(channels), channel
            )

            try:
                posts = await self.get_channel_posts(channel, hours=collection_hours)
                
                # Применяем лимит постов с канала
                if posts and len(posts) > max_posts_limit:
                    posts = posts[:max_posts_limit]
                    logger.info("✂️ %s: ограничено до %d постов (было %d)", 
                               channel, max_posts_limit, len(posts))
                
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
            if i < len(channels) - 1:  # Не ждем после последнего канала
                await asyncio.sleep(3)

        logger.info(
            "📈 Сбор завершен: успешно %s, ошибок %s",
            successful_channels,
            failed_channels,
        )

        # Отправляем данные в Backend API
        if all_posts:
            webhook_data = {
                "timestamp": datetime.now().isoformat(),
                "collection_stats": {
                    "total_posts": len(all_posts),
                    "successful_channels": successful_channels,
                    "failed_channels": failed_channels,
                    "channels_processed": channels,
                },
                "posts": all_posts,
                "channels_metadata": getattr(self, 'channels_metadata', {}),  # Добавляем метаданные каналов с категориями
            }

            success = await self.send_to_backend(webhook_data)
            if success:
                logger.info("📤 Отправлено %s постов в Backend API", len(all_posts))
            else:
                logger.error("❌ Ошибка отправки в Backend API")
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
