#!/usr/bin/env python3
"""
🤖 MorningStar Bot v4 - ДВОЙНАЯ ФИЛЬТРАЦИЯ: каналы ∩ категории

НОВАЯ ФУНКЦИОНАЛЬНОСТЬ:
- ✅ Двойная фильтрация: выбираем каналы И категории
- ✅ Фильтрация: (посты из выбранных каналов) ∩ (посты выбранных категорий)
- ✅ Локальное хранение подписок на каналы и категории
- ✅ Умное меню с разделением каналов и категорий
- ✅ Backend API интеграция для получения данных

ЛОГИКА РАБОТЫ:
1. Пользователь выбирает интересные каналы-источники
2. Пользователь выбирает интересные категории тем
3. Бот показывает только посты из выбранных каналов по выбранным категориям
"""
import asyncio
import json
import logging
import aiohttp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Конфигурация
BACKEND_URL = "http://127.0.0.1:8000"
PUBLIC_BOT_ID = 4
BOT_TOKEN = "8124620179:AAHNt4-7ZFg-zz0Cr6mJX483jDuNeARpIdE"

# 🔧 ЛОКАЛЬНОЕ ХРАНЕНИЕ ПОДПИСОК (с сохранением в файл)
SUBSCRIPTIONS_FILE = "user_subscriptions.json"

def load_user_subscriptions():
    """Загрузить подписки из файла"""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Преобразуем ключи обратно в int (JSON сохраняет ключи как строки)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Ошибка загрузки подписок: {e}")
            return {}
    return {}

def save_subscriptions_to_file():
    """Сохранить подписки в файл"""
    try:
        with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_subscriptions, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Подписки сохранены в файл: {SUBSCRIPTIONS_FILE}")
    except Exception as e:
        logger.error(f"Ошибка сохранения подписок: {e}")

# Загружаем подписки при запуске
user_subscriptions = load_user_subscriptions()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Логируем загрузку подписок
logger.info(f"📂 Загружено подписок пользователей: {len(user_subscriptions)} из файла: {SUBSCRIPTIONS_FILE}")

def get_main_menu_keyboard():
    """Создать основную клавиатуру с командами для двойной фильтрации"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Подписки", callback_data="cmd_subscriptions"),
            InlineKeyboardButton("📰 Дайджест", callback_data="cmd_digest")
        ],
        [
            InlineKeyboardButton("❓ Справка", callback_data="cmd_help"),
            InlineKeyboardButton("🧪 Тест", callback_data="cmd_test")
        ],
        [
            InlineKeyboardButton("🔧 Отладка", callback_data="cmd_debug")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_bot_categories():
    """Получить категории бота"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}/categories"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Исправляем проблему с именами категорий
                    categories = []
                    for cat in data:
                        # Используем category_name если name пустое
                        name = cat.get('name') or cat.get('category_name', f"Категория {cat.get('id')}")
                        categories.append({
                            'id': cat.get('id'),
                            'name': name,
                            'description': cat.get('description', ''),
                            'is_active': cat.get('is_active', True)
                        })
                    return categories
                else:
                    logger.error(f"Ошибка получения категорий: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка запроса категорий: {e}")
        return []

async def get_bot_channels():
    """Получить каналы бота"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}/channels"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Исправляем проблему с именами каналов
                    channels = []
                    for ch in data:
                        # Используем title или channel_name
                        name = ch.get('title') or ch.get('channel_name', f"Канал {ch.get('id')}")
                        channels.append({
                            'id': ch.get('id'),
                            'name': name,
                            'telegram_id': ch.get('telegram_id'),
                            'username': ch.get('username', ''),
                            'is_active': ch.get('is_active', True)
                        })
                    return channels
                else:
                    logger.error(f"Ошибка получения каналов: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка запроса каналов: {e}")
        return []

async def get_ai_posts(limit=10):
    """ИСПРАВЛЕНО: Получить RAW посты (без AI фильтрации) для полных данных"""
    try:
        async with aiohttp.ClientSession() as session:
            # ИСПРАВЛЕНО: используем ai_status=completed (полностью обработанные)
            url = f"{BACKEND_URL}/api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}&ai_status=completed&limit={limit}&sort_by=post_date&sort_order=desc"
            logger.info(f"🔄 ИСПРАВЛЕНО: ai_status=completed: {url}")
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Детальная отладка
                    logger.info(f"📊 API Response - Тип: {type(data)}, Длина: {len(data) if isinstance(data, (list, dict)) else 'не применимо'}")
                    
                    # Если пришел словарь, ищем массив постов
                    if isinstance(data, dict):
                        logger.info(f"🔍 Ключи словаря: {list(data.keys())}")
                        
                        # Ищем поле с постами (возможные варианты)
                        posts_data = None
                        for key in ['posts', 'data', 'results', 'items']:
                            if key in data:
                                posts_data = data[key]
                                logger.info(f"✅ Найдены посты в поле '{key}', тип: {type(posts_data)}")
                                break
                        
                        if posts_data is None:
                            logger.error(f"❌ Не найдено поле с постами в ответе: {data}")
                            return []
                        
                        # Теперь обрабатываем найденные посты
                        if isinstance(posts_data, list):
                            if len(posts_data) > 0:
                                logger.info(f"🔍 Первый пост - Тип: {type(posts_data[0])}")
                                if isinstance(posts_data[0], str):
                                    # Парсим JSON строки
                                    try:
                                        parsed_posts = []
                                        for item in posts_data:
                                            if isinstance(item, str):
                                                parsed_item = json.loads(item)
                                                parsed_posts.append(parsed_item)
                                            else:
                                                parsed_posts.append(item)
                                        logger.info(f"✅ Успешно распарсили {len(parsed_posts)} постов")
                                        return parsed_posts
                                    except json.JSONDecodeError as e:
                                        logger.error(f"❌ Ошибка парсинга JSON: {e}")
                                        return []
                                else:
                                    logger.info(f"✅ Посты уже в правильном формате")
                                    return posts_data
                            else:
                                logger.info("📭 Массив постов пустой")
                                return []
                        else:
                            logger.error(f"❌ Поле с постами не является массивом: {type(posts_data)}")
                            return []
                    
                    # Если пришел массив напрямую
                    elif isinstance(data, list):
                        if len(data) > 0:
                            logger.info(f"🔍 Первый элемент - Тип: {type(data[0])}")
                            if isinstance(data[0], str):
                                # Пытаемся распарсить JSON строки
                                try:
                                    parsed_data = []
                                    for item in data:
                                        if isinstance(item, str):
                                            parsed_item = json.loads(item)
                                            parsed_data.append(parsed_item)
                                        else:
                                            parsed_data.append(item)
                                    logger.info(f"✅ Успешно распарсили {len(parsed_data)} элементов")
                                    return parsed_data
                                except json.JSONDecodeError as e:
                                    logger.error(f"❌ Ошибка парсинга JSON: {e}")
                                    return []
                            else:
                                logger.info(f"✅ Массив уже в правильном формате")
                        return data
                    
                    else:
                        logger.error(f"❌ Неожиданный тип ответа: {type(data)}")
                        return []
                        
                else:
                    logger.error(f"Ошибка получения AI постов: {response.status}")
                    text = await response.text()
                    logger.error(f"Ответ сервера: {text[:200]}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка запроса AI постов: {e}")
        return []

def save_user_subscriptions(user_id, category_ids=None, channel_ids=None):
    """Сохранить подписки пользователя (категории и/или каналы)"""
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = {
            'categories': [],
            'channels': []
        }
    
    if category_ids is not None:
        user_subscriptions[user_id]['categories'] = category_ids
    
    if channel_ids is not None:
        user_subscriptions[user_id]['channels'] = channel_ids
        
    save_subscriptions_to_file()  # Сохраняем в файл
    logger.info(f"💾 Сохранены подписки пользователя {user_id}: категории={user_subscriptions[user_id]['categories']}, каналы={user_subscriptions[user_id]['channels']}")

def get_user_subscriptions(user_id, subscription_type='categories'):
    """Получить подписки пользователя (категории или каналы)"""
    user_data = user_subscriptions.get(user_id, {'categories': [], 'channels': []})
    
    # Поддержка старого формата (массив category_ids)
    if isinstance(user_data, list):
        # Мигрируем старый формат в новый
        user_subscriptions[user_id] = {
            'categories': user_data,
            'channels': []
        }
        save_subscriptions_to_file()
        return user_data if subscription_type == 'categories' else []
    
    return user_data.get(subscription_type, [])

def filter_posts_by_subscriptions(posts, subscribed_categories, subscribed_channel_ids):
    """ДВОЙНАЯ ФИЛЬТРАЦИЯ: посты по каналам И категориям"""
    if not subscribed_categories and not subscribed_channel_ids:
        return []
    
    filtered_posts = []
    channel_stats = {}
    category_stats = {}
    
    for post in posts:
        # Защита от ошибок - проверяем, что post это словарь
        if not isinstance(post, dict):
            logger.warning(f"Пропускаем пост неправильного формата: {type(post)}")
            continue
        
        # Статистика для диагностики
        post_channel = post.get('channel_telegram_id', 'unknown')
        post_category = post.get('ai_category', 'unknown')
        
        if post_channel not in channel_stats:
            channel_stats[post_channel] = {'total': 0, 'filtered': 0}
        channel_stats[post_channel]['total'] += 1
        
        if post_category not in category_stats:
            category_stats[post_category] = {'total': 0, 'filtered': 0}
        category_stats[post_category]['total'] += 1
        
        # ФИЛЬТР 1: По каналам (если выбраны каналы)
        channel_passes = True
        if subscribed_channel_ids:  # Если каналы выбраны - фильтруем
            channel_telegram_id = post.get('channel_telegram_id')
            if not channel_telegram_id or channel_telegram_id not in subscribed_channel_ids:
                channel_passes = False
                logger.debug(f"❌ Пост отклонен по каналам: канал {channel_telegram_id} не в подписках {subscribed_channel_ids}")
            else:
                logger.debug(f"✅ Пост принят по каналам: канал {channel_telegram_id} найден в подписках")
        # Если каналы НЕ выбраны - пропускаем все посты по каналам
        
        # ФИЛЬТР 2: По категориям (если выбраны категории)
        category_passes = True
        if subscribed_categories:  # Если категории выбраны - фильтруем
            ai_category = post.get('ai_category', '')
            if not ai_category:
                category_passes = False
                logger.debug(f"❌ Пост отклонен: нет ai_category. Канал: {post_channel}")
            else:
                # Проверяем, содержит ли AI категория одну из подписанных категорий
                category_matches = False
                for sub_cat in subscribed_categories:
                    if sub_cat.lower() in ai_category.lower():
                        category_matches = True
                        break
                
                if not category_matches:
                    category_passes = False
                    logger.debug(f"❌ Пост отклонен: категория '{ai_category}' не совпадает с подписками {subscribed_categories}. Канал: {post_channel}")
                else:
                    logger.debug(f"✅ Пост принят: категория '{ai_category}' совпадает с подписками. Канал: {post_channel}")
        # Если категории НЕ выбраны - пропускаем все посты по категориям
        
        # ПОСТ ПРОХОДИТ ТОЛЬКО ЕСЛИ ОБА ФИЛЬТРА ПРОЙДЕНЫ
        if channel_passes and category_passes:
            filtered_posts.append(post)
            channel_stats[post_channel]['filtered'] += 1
            category_stats[post_category]['filtered'] += 1
    
    # Диагностические логи
    logger.info(f"🔍 Фильтрация: из {len(posts)} постов отфильтровано {len(filtered_posts)} (каналы: {bool(subscribed_channel_ids)}, категории: {bool(subscribed_categories)})")
    
    # Статистика по каналам
    logger.info(f"📊 Статистика по каналам:")
    for channel, stats in channel_stats.items():
        logger.info(f"  📺 {channel}: {stats['filtered']}/{stats['total']} постов")
    
    # Статистика по категориям
    logger.info(f"📊 Статистика по категориям:")
    for category, stats in category_stats.items():
        logger.info(f"  📁 {category}: {stats['filtered']}/{stats['total']} постов")
    
    return filtered_posts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    keyboard = get_main_menu_keyboard()
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я MorningStar Bot v4 - персональный дайджест с двойной фильтрацией.\n\n"
        f"🎯 <b>НОВАЯ ФУНКЦИОНАЛЬНОСТЬ:</b>\n"
        f"• 📺 Выбор каналов-источников новостей\n"
        f"• 📁 Выбор категорий тем новостей\n"
        f"• 🔍 Двойная фильтрация: каналы ∩ категории\n"
        f"• 💾 Локальное хранение подписок\n\n"
        f"🚀 <b>Технические особенности:</b>\n"
        f"• 🤖 AI-категоризация и саммаризация постов\n"
        f"• 📊 Умные метрики (важность, срочность, значимость)\n"
        f"• 📁 Группировка дайджестов по категориям\n"
        f"• 🔧 Mультитенантность (bot_id: {PUBLIC_BOT_ID})\n\n"
        f"💡 <b>Как это работает:</b>\n"
        f"1. Выберите интересные каналы\n"
        f"2. Выберите интересные категории\n"
        f"3. Получите посты только из выбранных каналов по выбранным темам\n\n"
        f"Выберите действие из меню ниже:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = f"""
🤖 <b>MorningStar Bot v4 - ДВОЙНАЯ ФИЛЬТРАЦИЯ</b>

📋 <b>Основные команды:</b>
/start - Начать работу с ботом
/channels - Показать доступные каналы
/categories - Показать доступные категории
/subscribe - Управление подписками
/digest - Получить персональный дайджест
/help - Показать справку

🔧 <b>Отладка:</b>
/test - Показать 10 AI постов
/debug - Техническая информация

🎯 <b>Двойная фильтрация:</b>
• 📺 Выбираете каналы-источники
• 📁 Выбираете категории тем
• 🔍 Получаете посты из выбранных каналов по выбранным темам

💡 <b>Особенности v4:</b>
• Использует endpoint /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}
• Подписки сохраняются в файл user_subscriptions.json
• Фильтрация по каналам И категориям одновременно
• Группировка дайджестов по категориям
• Умная сортировка по AI метрикам
"""
    keyboard = get_main_menu_keyboard()
    await update.message.reply_text(help_text, reply_markup=keyboard, parse_mode='HTML')

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать доступные категории"""
    categories = await get_bot_categories()
    
    if not categories:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            "❌ Не удалось получить категории. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    text = f"📁 <b>Доступные категории для бота {PUBLIC_BOT_ID}:</b>\n\n"
    for cat in categories:
        status = "✅" if cat['is_active'] else "❌"
        text += f"{status} <b>{cat['name']}</b> (ID: {cat['id']})\n"
        if cat['description']:
            text += f"   📝 {cat['description']}\n"
        text += "\n"
    
    text += f"💡 Всего категорий: {len(categories)}"
    keyboard = get_main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать доступные каналы"""
    channels = await get_bot_channels()
    
    if not channels:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            "❌ Не удалось получить каналы. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    text = f"📺 <b>Доступные каналы для бота {PUBLIC_BOT_ID}:</b>\n\n"
    for ch in channels:
        status = "✅" if ch['is_active'] else "❌"
        username = f"@{ch['username']}" if ch['username'] else "Без username"
        text += f"{status} <b>{ch['name']}</b> (ID: {ch['id']})\n"
        text += f"   📱 {username}\n"
        text += f"   🆔 Telegram ID: {ch['telegram_id']}\n"
        text += "\n"
    
    text += f"💡 Всего каналов: {len(channels)}"
    keyboard = get_main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

async def subscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Единое управление подписками на каналы и категории"""
    user_id = update.effective_user.id
    
    # Получаем подписки пользователя
    category_subscriptions = get_user_subscriptions(user_id, 'categories')
    channel_subscriptions = get_user_subscriptions(user_id, 'channels')
    
    # Получаем данные для отображения
    categories = await get_bot_categories()
    channels = await get_bot_channels()
    
    if not categories and not channels:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            "❌ Не удалось получить данные. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # Создаем клавиатуру с прямым управлением
    keyboard = []
    
    # Заголовок каналов
    keyboard.append([InlineKeyboardButton("📺 === КАНАЛЫ ===", callback_data="noop")])
    
    # Добавляем каналы
    for ch in channels:
        if ch['is_active']:
            is_subscribed = ch['id'] in channel_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            display_name = ch['name'][:25] + "..." if len(ch['name']) > 25 else ch['name']
            text = f"{emoji} {display_name}"
            callback_data = f"toggle_channel_{ch['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Заголовок категорий
    keyboard.append([InlineKeyboardButton("📁 === КАТЕГОРИИ ===", callback_data="noop")])
    
    # Добавляем категории
    for cat in categories:
        if cat['is_active']:
            is_subscribed = cat['id'] in category_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            text = f"{emoji} {cat['name']}"
            callback_data = f"toggle_category_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data="cmd_subscriptions"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем текст с подписками
    text = f"🎯 <b>Управление подписками (бот {PUBLIC_BOT_ID})</b>\n\n"
    text += f"📺 <b>Каналы:</b> {len(channel_subscriptions)} из {len(channels)}\n"
    text += f"📁 <b>Категории:</b> {len(category_subscriptions)} из {len(categories)}\n\n"
    text += f"🔍 <b>Двойная фильтрация:</b>\n"
    text += f"Дайджест = посты из выбранных каналов по выбранным темам\n\n"
    text += f"💡 Нажимайте на элементы для переключения подписок:"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def get_bot_settings():
    """Получить настройки бота через Backend API"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}"
            logger.info(f"🔧 Запрос настроек бота: {url}")
            async with session.get(url) as response:
                if response.status == 200:
                    bot_settings = await response.json()
                    logger.info(f"🔧 Настройки бота получены: max_posts_per_digest={bot_settings.get('max_posts_per_digest', 10)}")
                    return bot_settings
                else:
                    logger.error(f"❌ Ошибка получения настроек бота: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ Ошибка при получении настроек бота: {e}")
        return None

def split_message(text, max_length=4000):
    """Разбить длинное сообщение на части для Telegram"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем по строкам
    lines = text.split('\n')
    
    for line in lines:
        # Если добавление строки превысит лимит
        if len(current_part + line + '\n') > max_length:
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
            
            # Если одна строка слишком длинная, обрезаем
            if len(line) > max_length:
                line = line[:max_length-3] + "..."
        
        current_part += line + '\n'
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part.strip())
    
    return parts

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получить персональный дайджест с двойной фильтрацией"""
    user_id = update.effective_user.id
    
    # Получаем подписки пользователя
    subscribed_category_ids = get_user_subscriptions(user_id, 'categories')
    subscribed_channel_ids = get_user_subscriptions(user_id, 'channels')
    
    logger.info(f"🎯 Дайджест для пользователя {user_id}: каналы={subscribed_channel_ids}, категории={subscribed_category_ids}")
    
    if not subscribed_category_ids and not subscribed_channel_ids:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            f"📭 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            f"🎯 Для получения дайджеста нужно:\n"
            f"• Выбрать интересные каналы (источники новостей)\n"
            f"• Выбрать интересные категории (темы новостей)\n\n"
            f"Используйте кнопку '🎯 Подписки' для настройки фильтрации.",
            reply_markup=keyboard
        )
        return
    
    # Показываем индикатор загрузки
    loading_msg = await update.message.reply_text("⏳ Формируем персональный дайджест с двойной фильтрацией...")
    
    # Получаем настройки бота
    bot_settings = await get_bot_settings()
    
    # Получаем лимит постов из настроек бота (по умолчанию 10)
    max_posts_per_digest = 10  # fallback значение
    if bot_settings:
        max_posts_per_digest = bot_settings.get('max_posts_per_digest', 10)
    
    logger.info(f"📊 Лимит постов в дайджесте: {max_posts_per_digest}")
    
    # Получаем данные для понимания названий
    categories = await get_bot_categories()
    channels = await get_bot_channels()
    
    category_names = {cat['id']: cat['name'] for cat in categories}
    channel_names = {ch['id']: ch['name'] for ch in channels}
    
    subscribed_category_names = [category_names.get(cat_id, f"Категория {cat_id}") for cat_id in subscribed_category_ids]
    subscribed_channel_names = [channel_names.get(ch_id, f"Канал {ch_id}") for ch_id in subscribed_channel_ids]
    
    # Получаем Telegram ID каналов для фильтрации
    subscribed_channel_telegram_ids = []
    for ch in channels:
        if ch['id'] in subscribed_channel_ids:
            subscribed_channel_telegram_ids.append(ch['telegram_id'])
    
    logger.info(f"📺 Подписки на каналы: {subscribed_channel_names} (telegram_ids: {subscribed_channel_telegram_ids})")
    logger.info(f"📁 Подписки на категории: {subscribed_category_names}")
    
    # ДИАГНОСТИКА: проверяем, подписан ли пользователь на ВСЕ каналы
    total_channels = len(channels)
    subscribed_channels_count = len(subscribed_channel_ids)
    total_categories = len(categories)
    subscribed_categories_count = len(subscribed_category_ids)
    
    logger.info(f"📊 ДИАГНОСТИКА: подписан на {subscribed_channels_count} из {total_channels} каналов")
    logger.info(f"📊 ДИАГНОСТИКА: подписан на {subscribed_categories_count} из {total_categories} категорий")
    
    # Если подписан на всё, предупреждаем о большом объеме
    if subscribed_channels_count == total_channels and subscribed_categories_count == total_categories:
        logger.warning(f"⚠️ ВНИМАНИЕ: пользователь подписан на ВСЕ каналы и категории - дайджест может быть очень большим")
    
    # Получаем AI посты (увеличиваем лимит для лучшей фильтрации)
    api_limit = max(max_posts_per_digest * 3, 50)  # Запрашиваем больше чем нужно для фильтрации
    posts = await get_ai_posts(limit=api_limit)
    logger.info(f"📊 Получено постов из API: {len(posts) if posts else 0}")
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await loading_msg.edit_text(
            "❌ Не удалось получить посты. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # ДИАГНОСТИКА: анализируем уникальные каналы в постах
    unique_channels = set()
    posts_by_channel = {}
    for post in posts:
        if isinstance(post, dict):
            channel_id = post.get('channel_telegram_id')
            if channel_id:
                unique_channels.add(channel_id)
                if channel_id not in posts_by_channel:
                    posts_by_channel[channel_id] = 0
                posts_by_channel[channel_id] += 1
    
    logger.info(f"📺 ДИАГНОСТИКА: уникальные каналы в постах: {unique_channels}")
    logger.info(f"📺 ДИАГНОСТИКА: каналы в подписках: {subscribed_channel_telegram_ids}")
    logger.info(f"📊 ДИАГНОСТИКА: постов по каналам: {posts_by_channel}")
    
    # ДВОЙНАЯ ФИЛЬТРАЦИЯ: каналы ∩ категории
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_category_names, subscribed_channel_telegram_ids)
    
    logger.info(f"🔍 ДИАГНОСТИКА: после фильтрации осталось {len(filtered_posts)} постов")
    
    if not filtered_posts:
        keyboard = get_main_menu_keyboard()
        filter_info = ""
        if subscribed_channel_names:
            filter_info += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
        if subscribed_category_names:
            filter_info += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
        
        # Дополнительная диагностика для пустого результата
        debug_info = f"\n🔍 <b>Диагностика:</b>\n"
        debug_info += f"📊 Всего постов из API: {len(posts)}\n"
        debug_info += f"📺 Уникальные каналы в постах: {len(unique_channels)}\n"
        debug_info += f"📁 Категории в подписках: {len(subscribed_category_names)}\n"
        debug_info += f"📺 Каналы в подписках: {len(subscribed_channel_ids)}\n"
            
        await loading_msg.edit_text(
            f"📭 Нет новых постов по вашим фильтрам.\n\n"
            f"🎯 <b>Ваши фильтры:</b>\n{filter_info}\n"
            f"💡 Попробуйте расширить подписки или попробуйте позже.\n{debug_info}",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    # Сортируем посты по метрикам
    def calculate_score(post):
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        return importance * 3 + urgency * 2 + significance * 2
    
    filtered_posts.sort(key=calculate_score, reverse=True)
    
    # Ограничиваем количество постов согласно настройкам бота
    filtered_posts = filtered_posts[:max_posts_per_digest]
    
    # Группируем посты по КАТЕГОРИЯМ (как просил пользователь)
    posts_by_category = {}
    for post in filtered_posts:
        category = post.get('ai_category', 'Без категории')
        
        if category not in posts_by_category:
            posts_by_category[category] = []
        posts_by_category[category].append(post)
    
    # Сортируем категории по количеству постов (больше постов = выше)
    sorted_categories = sorted(posts_by_category.keys(), key=lambda cat: len(posts_by_category[cat]), reverse=True)
    
    # Формируем дайджест
    text = f"📰 <b>Персональный дайджест v4</b>\n"
    
    # Показываем активные фильтры
    text += f"🎯 <b>Фильтры:</b>\n"
    if subscribed_channel_names:
        text += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
    if subscribed_category_names:
        text += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
    
    text += f"📊 Найдено постов: {len(filtered_posts)} (лимит: {max_posts_per_digest})\n\n"
    
    # Показываем посты по КАТЕГОРИЯМ
    for category_name in sorted_categories:
        posts = posts_by_category[category_name]
        text += f"📁 <b>{category_name.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            ai_summary = post.get('ai_summary') or 'Нет описания'
            
            # Ограничиваем длину саммари для экономии места
            if len(ai_summary) > 200:
                ai_summary = ai_summary[:200] + "..."
            
            # Находим название канала для каждого поста
            channel_name = 'Неизвестный канал'
            channel_id = post.get('channel_telegram_id')
            for ch in channels:
                if ch['telegram_id'] == channel_id:
                    channel_name = ch['name']
                    break
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
            
            # Показываем источник (канал)
            text += f"   📺 {channel_name}\n"
        
        text += "\n"
    
    # Проверяем длину сообщения и разбиваем на части если нужно
    logger.info(f"📏 Длина дайджеста: {len(text)} символов")
    
    keyboard = get_main_menu_keyboard()
    message_parts = split_message(text)
    
    if len(message_parts) == 1:
        # Одно сообщение
        await loading_msg.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        # Несколько сообщений
        await loading_msg.edit_text(
            f"📰 <b>Дайджест разбит на {len(message_parts)} частей из-за размера</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Отправляем части по очереди
        for i, part in enumerate(message_parts, 1):
            if i == len(message_parts):
                # Последняя часть с клавиатурой
                await update.message.reply_text(
                    f"📰 <b>Часть {i}/{len(message_parts)}</b>\n\n{part}",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                # Промежуточные части без клавиатуры
                await update.message.reply_text(
                    f"📰 <b>Часть {i}/{len(message_parts)}</b>\n\n{part}",
                    parse_mode='HTML'
                )

async def api_test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка API - показывает сырые данные без фильтрации"""
    loading_msg = await update.message.reply_text("⏳ Проверяем API данные...")
    
    # Тестируем ОБА endpoint'а для сравнения
    posts_with_bot = await get_ai_posts(limit=10)  # С bot_id=4
    categories = await get_bot_categories()
    channels = await get_bot_channels()
    
    # Тестируем endpoint БЕЗ bot_id фильтра (все посты в системе)
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/posts/cache-with-ai?limit=10"  # БЕЗ bot_id
            async with session.get(url) as response:
                if response.status == 200:
                    all_posts_data = await response.json()
                    if isinstance(all_posts_data, dict) and 'posts' in all_posts_data:
                        posts_all = all_posts_data['posts']
                    else:
                        posts_all = []
                else:
                    posts_all = []
    except Exception as e:
        posts_all = []
        logger.error(f"Ошибка получения всех постов: {e}")
    
    # Тестируем RAW POSTS (без AI фильтрации)
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/posts/cache?limit=100"  # Увеличиваем лимит
            logger.info(f"🔍 Запрос RAW постов: {url}")
            async with session.get(url) as response:
                logger.info(f"🔍 RAW ответ: статус {response.status}")
                if response.status == 200:
                    raw_posts_data = await response.json()
                    logger.info(f"🔍 RAW данные: тип {type(raw_posts_data)}, длина {len(raw_posts_data) if isinstance(raw_posts_data, list) else 'не список'}")
                    
                    # API возвращает список постов напрямую (не в объекте с 'posts')
                    if isinstance(raw_posts_data, list):
                        posts_raw = raw_posts_data
                    elif isinstance(raw_posts_data, dict) and 'posts' in raw_posts_data:
                        posts_raw = raw_posts_data['posts']
                    else:
                        posts_raw = []
                        logger.error(f"🔍 Неожиданный формат RAW данных: {type(raw_posts_data)}")
                else:
                    posts_raw = []
                    logger.error(f"🔍 RAW запрос неуспешен: {response.status}")
    except Exception as e:
        posts_raw = []
        logger.error(f"Ошибка получения RAW постов: {e}")
    
    if not posts_with_bot and not posts_all:
        keyboard = get_main_menu_keyboard()
        await loading_msg.edit_text(
            "❌ Не удалось получить посты из API.",
            reply_markup=keyboard
        )
        return
    
    # Анализируем посты С bot_id фильтром
    bot_channels = {}
    bot_categories = {}
    for post in (posts_with_bot or []):
        if isinstance(post, dict):
            channel_id = post.get('channel_telegram_id')
            category = post.get('ai_category')
            
            if channel_id:
                if channel_id not in bot_channels:
                    bot_channels[channel_id] = 0
                bot_channels[channel_id] += 1
            
            if category:
                if category not in bot_categories:
                    bot_categories[category] = 0
                bot_categories[category] += 1
    
    # Анализируем ВСЕ посты (без bot_id)
    all_channels = {}
    all_categories = {}
    for post in (posts_all or []):
        if isinstance(post, dict):
            channel_id = post.get('channel_telegram_id')
            category = post.get('ai_category')
            
            if channel_id:
                if channel_id not in all_channels:
                    all_channels[channel_id] = 0
                all_channels[channel_id] += 1
            
            if category:
                if category not in all_categories:
                    all_categories[category] = 0
                all_categories[category] += 1
    
    # Анализируем RAW посты (без AI обработки)
    raw_channels = {}
    for post in (posts_raw or []):
        if isinstance(post, dict):
            channel_id = post.get('channel_telegram_id')
            
            if channel_id:
                if channel_id not in raw_channels:
                    raw_channels[channel_id] = 0
                raw_channels[channel_id] += 1
    
    text = f"🔍 <b>API ДИАГНОСТИКА - НАЙДЕНА ПРОБЛЕМА!</b>\n\n"
    text += f"🤖 <b>AI посты с bot_id={PUBLIC_BOT_ID}:</b>\n"
    text += f"📊 Постов: {len(posts_with_bot or [])}\n"
    text += f"📺 Каналов: {len(bot_channels)}\n"
    text += f"📁 Категорий: {len(bot_categories)}\n\n"
    
    text += f"🌍 <b>AI посты (без bot_id):</b>\n"
    text += f"📊 Постов: {len(posts_all or [])}\n"
    text += f"📺 Каналов: {len(all_channels)}\n"
    text += f"📁 Категорий: {len(all_categories)}\n\n"
    
    text += f"📋 <b>RAW посты (без AI):</b>\n"
    text += f"📊 Постов: {len(posts_raw or [])}\n"
    text += f"📺 Каналов: {len(raw_channels)}\n\n"
    
    if len(raw_channels) > len(bot_channels):
        text += f"⚠️ <b>ПРОБЛЕМА НАЙДЕНА!</b>\n"
        text += f"RAW данных больше чем AI обработанных!\n\n"
    
    text += f"📺 <b>Каналы с bot_id={PUBLIC_BOT_ID}:</b>\n"
    for channel_id, count in bot_channels.items():
        text += f"• {channel_id}: {count} постов\n"
    
    text += f"\n📺 <b>AI каналы (без bot_id):</b>\n"
    for channel_id, count in all_channels.items():
        text += f"• {channel_id}: {count} постов\n"
    
    text += f"\n📺 <b>RAW каналы (все данные):</b>\n"
    for channel_id, count in raw_channels.items():
        text += f"• {channel_id}: {count} постов\n"
    
    text += f"\n🗂️ <b>Доступные категории API ({len(categories)}):</b>\n"
    for cat in categories:
        status = "✅" if cat['is_active'] else "❌"
        text += f"{status} ID:{cat['id']} - {cat['name']}\n"
    
    text += f"\n📺 <b>Доступные каналы API ({len(channels)}):</b>\n"
    for ch in channels:
        status = "✅" if ch['is_active'] else "❌"
        text += f"{status} ID:{ch['id']} - {ch['name']} (TG:{ch['telegram_id']})\n"
    
    text += f"\n📝 <b>Первые 3 поста (С bot_id):</b>\n"
    for i, post in enumerate((posts_with_bot or [])[:3], 1):
        if isinstance(post, dict):
            title = (post.get('title') or 'Без заголовка')[:40]
            category = post.get('ai_category', 'Без категории')
            channel = post.get('channel_telegram_id', 'Без канала')
            text += f"\n{i}. {title}\n"
            text += f"   📺 Канал: {channel}\n"
            text += f"   📁 Категория: {category}\n"
    
    text += f"\n📝 <b>Первые 3 поста (ВСЕ AI):</b>\n"
    for i, post in enumerate((posts_all or [])[:3], 1):
        if isinstance(post, dict):
            title = (post.get('title') or 'Без заголовка')[:40]
            category = post.get('ai_category', 'Без категории')
            channel = post.get('channel_telegram_id', 'Без канала')
            text += f"\n{i}. {title}\n"
            text += f"   📺 Канал: {channel}\n"
            text += f"   📁 Категория: {category}\n"
    
    text += f"\n📝 <b>Первые 3 поста (RAW):</b>\n"
    for i, post in enumerate((posts_raw or [])[:3], 1):
        if isinstance(post, dict):
            title = (post.get('title') or 'Без заголовка')[:40]
            content = (post.get('content') or 'Без содержимого')[:30]
            channel = post.get('channel_telegram_id', 'Без канала')
            views = post.get('views', 0)
            text += f"\n{i}. {title}\n"
            text += f"   📺 Канал: {channel}\n"
            text += f"   👀 Просмотры: {views}\n"
            text += f"   📄 Содержимое: {content}...\n"
    
    keyboard = get_main_menu_keyboard()
    await loading_msg.edit_text(text, reply_markup=keyboard, parse_mode='HTML')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Тестовая команда для отладки"""
    loading_msg = await update.message.reply_text("⏳ Загружаем тестовые посты...")
    
    posts = await get_ai_posts(limit=10)
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await loading_msg.edit_text(
            "❌ Не удалось получить тестовые посты.",
            reply_markup=keyboard
        )
        return
    
    text = f"🧪 <b>Тест AI постов (bot_id: {PUBLIC_BOT_ID})</b>\n\n"
    text += f"📊 Получено постов: {len(posts)}\n\n"
    
    for i, post in enumerate(posts[:5], 1):
        # Проверяем, что post это словарь
        if not isinstance(post, dict):
            text += f"<b>{i}. Ошибка формата</b>\n"
            text += f"Тип: {type(post)}\n\n"
            continue
            
        title = (post.get('title') or 'Без заголовка')[:30]
        ai_category = post.get('ai_category') or 'Нет категории'
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        
        text += f"<b>{i}. {title}</b>\n"
        text += f"🏷️ {ai_category}\n"
        text += f"📊 {importance:.1f}/{urgency:.1f}/{significance:.1f}\n\n"
    
    keyboard = get_main_menu_keyboard()
    await loading_msg.edit_text(text, reply_markup=keyboard, parse_mode='HTML')

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отладочная информация"""
    user_id = update.effective_user.id
    category_subscriptions = get_user_subscriptions(user_id, 'categories')
    channel_subscriptions = get_user_subscriptions(user_id, 'channels')
    
    # Проверяем API
    posts = await get_ai_posts(limit=3)
    
    text = f"🔧 <b>Отладочная информация v4</b>\n\n"
    text += f"👤 User ID: {user_id}\n"
    text += f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
    text += f"🔗 Backend URL: {BACKEND_URL}\n\n"
    
    text += f"📊 <b>Подписки пользователя:</b>\n"
    text += f"📁 Категории: {category_subscriptions}\n"
    text += f"📺 Каналы: {channel_subscriptions}\n"
    text += f"📝 Всего пользователей в памяти: {len(user_subscriptions)}\n\n"
    
    text += f"💾 <b>Система хранения:</b>\n"
    text += f"📂 Файл: {SUBSCRIPTIONS_FILE}\n"
    text += f"🔄 Режим: Локальное хранение с двойной фильтрацией\n"
    text += f"🎯 Endpoint: /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}\n\n"
    
    # Отладка API данных
    text += f"🔍 <b>API Debug:</b>\n"
    text += f"📊 Получено постов: {len(posts) if isinstance(posts, list) else 'не список'}\n"
    
    if posts and isinstance(posts, list):
        for i, post in enumerate(posts[:2], 1):
            text += f"\n📝 Пост {i}:\n"
            text += f"  Тип: {str(type(post))}\n"
            if isinstance(post, dict):
                keys_list = list(post.keys())[:5]
                text += f"  Ключи: {str(keys_list)}\n"
                text += f"  ai_category: {post.get('ai_category', 'отсутствует')}\n"
                text += f"  channel_telegram_id: {post.get('channel_telegram_id', 'отсутствует')}\n"
                text += f"  title: {(post.get('title') or 'отсутствует')[:30]}\n"
            else:
                text += f"  Содержимое: {str(post)[:50]}\n"
    
    keyboard = get_main_menu_keyboard()
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline кнопок"""
    query = update.callback_query
    
    user_id = query.from_user.id
    data = query.data
    
    # Игнорируем заголовки
    if data == "noop":
        await query.answer("🔘 Это заголовок раздела")
        return
    
    await query.answer()
    
    # Обработка команд через кнопки
    if data == "cmd_subscriptions":
        await subscriptions_command_callback(query, context)
    elif data == "cmd_digest":
        await digest_command_callback(query, context)
    elif data == "cmd_help":
        await help_command_callback(query, context)
    elif data == "cmd_test":
        await test_command_callback(query, context)
    elif data == "cmd_debug":
        await debug_command_callback(query, context)
    elif data == "main_menu":
        await main_menu_callback(query, context)
    elif data.startswith("toggle_channel_"):
        # Обработка toggle подписок на каналы
        channel_id = int(data.split("_")[2])
        current_subscriptions = get_user_subscriptions(user_id, 'channels')
        
        if channel_id in current_subscriptions:
            current_subscriptions.remove(channel_id)
        else:
            current_subscriptions.append(channel_id)
        
        save_user_subscriptions(user_id, channel_ids=current_subscriptions)
        
        # Обновляем сообщение
        await subscriptions_command_callback(query, context)
        
    elif data.startswith("toggle_category_"):
        # Обработка toggle подписок на категории
        category_id = int(data.split("_")[2])
        current_subscriptions = get_user_subscriptions(user_id, 'categories')
        
        if category_id in current_subscriptions:
            current_subscriptions.remove(category_id)
        else:
            current_subscriptions.append(category_id)
        
        save_user_subscriptions(user_id, category_ids=current_subscriptions)
        
        # Обновляем сообщение
        await subscriptions_command_callback(query, context)

# Callback версии команд
async def main_menu_callback(query, context):
    """Показать главное меню"""
    user = query.from_user
    keyboard = get_main_menu_keyboard()
    
    await query.edit_message_text(
        f"🏠 <b>Главное меню - MorningStar Bot v4</b>\n\n"
        f"Привет, {user.first_name}! 👋\n\n"
        f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
        f"⚡ Режим: Двойная фильтрация (каналы ∩ категории)\n"
        f"💾 Хранение: Локальные подписки\n\n"
        f"Выберите действие из меню ниже:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def help_command_callback(query, context):
    """Показать справку через callback"""
    help_text = f"""
🤖 <b>MorningStar Bot v4 - Справка</b>

📋 <b>Основные функции:</b>
• 📁 Категории - Показать доступные категории
• 🎯 Подписки - Управление подписками на категории
• 📰 Дайджест - Получить персональный дайджест
• ❓ Справка - Показать эту справку

🔧 <b>Отладка:</b>
• 🧪 Тест - Показать 10 AI постов
• 🔧 Отладка - Техническая информация

🎯 <b>Двойная фильтрация:</b>
• 📺 Выбираете каналы-источники
• 📁 Выбираете категории тем
• 🔍 Получаете посты из выбранных каналов по выбранным темам

💡 <b>Особенности v4:</b>
• Использует endpoint /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}
• Подписки сохраняются в файл user_subscriptions.json
• Фильтрация по каналам И категориям одновременно
• Группировка дайджестов по категориям
• Умная сортировка по AI метрикам
"""
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(help_text, reply_markup=keyboard, parse_mode='HTML')

async def test_command_callback(query, context):
    """Тест через callback"""
    await query.edit_message_text("⏳ Загружаем тестовые посты...")
    
    posts = await get_ai_posts(limit=10)
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить тестовые посты.",
            reply_markup=keyboard
        )
        return
    
    text = f"🧪 <b>Тест AI постов (bot_id: {PUBLIC_BOT_ID})</b>\n\n"
    text += f"📊 Получено постов: {len(posts)}\n\n"
    
    for i, post in enumerate(posts[:5], 1):
        # Проверяем, что post это словарь
        if not isinstance(post, dict):
            text += f"<b>{i}. Ошибка формата</b>\n"
            text += f"Тип: {type(post)}\n\n"
            continue
            
        title = (post.get('title') or 'Без заголовка')[:30]
        ai_category = post.get('ai_category') or 'Нет категории'
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        
        text += f"<b>{i}. {title}</b>\n"
        text += f"🏷️ {ai_category}\n"
        text += f"📊 {importance:.1f}/{urgency:.1f}/{significance:.1f}\n\n"
    
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def debug_command_callback(query, context):
    """Отладка через callback"""
    await query.edit_message_text("⏳ Собираем отладочную информацию...")
    
    user_id = query.from_user.id
    category_subscriptions = get_user_subscriptions(user_id, 'categories')
    channel_subscriptions = get_user_subscriptions(user_id, 'channels')
    
    # Проверяем API
    posts = await get_ai_posts(limit=3)
    
    text = f"🔧 <b>Отладочная информация v4</b>\n\n"
    text += f"👤 User ID: {user_id}\n"
    text += f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
    text += f"🔗 Backend URL: {BACKEND_URL}\n\n"
    
    text += f"📊 <b>Подписки пользователя:</b>\n"
    text += f"📁 Категории: {category_subscriptions}\n"
    text += f"📺 Каналы: {channel_subscriptions}\n"
    text += f"📝 Всего пользователей в памяти: {len(user_subscriptions)}\n\n"
    
    text += f"💾 <b>Система хранения:</b>\n"
    text += f"📂 Файл: {SUBSCRIPTIONS_FILE}\n"
    text += f"🔄 Режим: Локальное хранение с двойной фильтрацией\n"
    text += f"🎯 Endpoint: /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}\n\n"
    
    # Отладка API данных
    text += f"🔍 <b>API Debug:</b>\n"
    text += f"📊 Получено постов: {len(posts) if isinstance(posts, list) else 'не список'}\n"
    
    if posts and isinstance(posts, list):
        for i, post in enumerate(posts[:2], 1):
            text += f"\n📝 Пост {i}:\n"
            text += f"  Тип: {str(type(post))}\n"
            if isinstance(post, dict):
                keys_list = list(post.keys())[:5]
                text += f"  Ключи: {str(keys_list)}\n"
                text += f"  ai_category: {post.get('ai_category', 'отсутствует')}\n"
                text += f"  channel_telegram_id: {post.get('channel_telegram_id', 'отсутствует')}\n"
                text += f"  title: {(post.get('title') or 'отсутствует')[:30]}\n"
            else:
                text += f"  Содержимое: {str(post)[:50]}\n"
    
    keyboard = get_main_menu_keyboard()
    # Убираем HTML парсинг для debug чтобы избежать ошибок
    await query.edit_message_text(text, reply_markup=keyboard)

async def subscriptions_command_callback(query, context):
    """Единое управление подписками через callback"""
    await query.edit_message_text("⏳ Загружаем подписки...")
    
    user_id = query.from_user.id
    
    # Получаем подписки пользователя
    category_subscriptions = get_user_subscriptions(user_id, 'categories')
    channel_subscriptions = get_user_subscriptions(user_id, 'channels')
    
    # Получаем данные для отображения
    categories = await get_bot_categories()
    channels = await get_bot_channels()
    
    if not categories and not channels:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить данные. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # Создаем клавиатуру с прямым управлением
    keyboard = []
    
    # Заголовок каналов
    keyboard.append([InlineKeyboardButton("📺 === КАНАЛЫ ===", callback_data="noop")])
    
    # Добавляем каналы
    for ch in channels:
        if ch['is_active']:
            is_subscribed = ch['id'] in channel_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            display_name = ch['name'][:25] + "..." if len(ch['name']) > 25 else ch['name']
            text = f"{emoji} {display_name}"
            callback_data = f"toggle_channel_{ch['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Заголовок категорий
    keyboard.append([InlineKeyboardButton("📁 === КАТЕГОРИИ ===", callback_data="noop")])
    
    # Добавляем категории
    for cat in categories:
        if cat['is_active']:
            is_subscribed = cat['id'] in category_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            text = f"{emoji} {cat['name']}"
            callback_data = f"toggle_category_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    # Кнопки управления
    keyboard.append([
        InlineKeyboardButton("🔄 Обновить", callback_data="cmd_subscriptions"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем текст с подписками
    text = f"🎯 <b>Управление подписками (бот {PUBLIC_BOT_ID})</b>\n\n"
    text += f"📺 <b>Каналы:</b> {len(channel_subscriptions)} из {len(channels)}\n"
    text += f"📁 <b>Категории:</b> {len(category_subscriptions)} из {len(categories)}\n\n"
    text += f"🔍 <b>Двойная фильтрация:</b>\n"
    text += f"Дайджест = посты из выбранных каналов по выбранным темам\n\n"
    text += f"💡 Нажимайте на элементы для переключения подписок:"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def digest_command_callback(query, context):
    """Получить дайджест через callback"""
    await query.edit_message_text("⏳ Формируем персональный дайджест с двойной фильтрацией...")
    
    user_id = query.from_user.id
    
    # Получаем подписки пользователя
    subscribed_category_ids = get_user_subscriptions(user_id, 'categories')
    subscribed_channel_ids = get_user_subscriptions(user_id, 'channels')
    
    if not subscribed_category_ids and not subscribed_channel_ids:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            f"📭 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            f"🎯 Для получения дайджеста нужно:\n"
            f"• Выбрать интересные каналы (источники новостей)\n"
            f"• Выбрать интересные категории (темы новостей)\n\n"
            f"Используйте кнопку '🎯 Подписки' для настройки фильтрации.",
            reply_markup=keyboard
        )
        return
    
    # Получаем настройки бота
    bot_settings = await get_bot_settings()
    
    # Получаем лимит постов из настроек бота (по умолчанию 10)
    max_posts_per_digest = 10  # fallback значение
    if bot_settings:
        max_posts_per_digest = bot_settings.get('max_posts_per_digest', 10)
    
    logger.info(f"📊 Лимит постов в дайджесте: {max_posts_per_digest}")
    
    # Получаем данные для понимания названий
    categories = await get_bot_categories()
    channels = await get_bot_channels()
    
    category_names = {cat['id']: cat['name'] for cat in categories}
    channel_names = {ch['id']: ch['name'] for ch in channels}
    
    subscribed_category_names = [category_names.get(cat_id, f"Категория {cat_id}") for cat_id in subscribed_category_ids]
    subscribed_channel_names = [channel_names.get(ch_id, f"Канал {ch_id}") for ch_id in subscribed_channel_ids]
    
    # Получаем Telegram ID каналов для фильтрации
    subscribed_channel_telegram_ids = []
    for ch in channels:
        if ch['id'] in subscribed_channel_ids:
            subscribed_channel_telegram_ids.append(ch['telegram_id'])
    
    logger.info(f"📺 Подписки на каналы: {subscribed_channel_names} (telegram_ids: {subscribed_channel_telegram_ids})")
    logger.info(f"📁 Подписки на категории: {subscribed_category_names}")
    
    # ДИАГНОСТИКА: проверяем, подписан ли пользователь на ВСЕ каналы
    total_channels = len(channels)
    subscribed_channels_count = len(subscribed_channel_ids)
    total_categories = len(categories)
    subscribed_categories_count = len(subscribed_category_ids)
    
    logger.info(f"📊 ДИАГНОСТИКА: подписан на {subscribed_channels_count} из {total_channels} каналов")
    logger.info(f"📊 ДИАГНОСТИКА: подписан на {subscribed_categories_count} из {total_categories} категорий")
    
    # Если подписан на всё, предупреждаем о большом объеме
    if subscribed_channels_count == total_channels and subscribed_categories_count == total_categories:
        logger.warning(f"⚠️ ВНИМАНИЕ: пользователь подписан на ВСЕ каналы и категории - дайджест может быть очень большим")
    
    # Получаем AI посты (увеличиваем лимит для лучшей фильтрации)
    api_limit = max(max_posts_per_digest * 3, 50)  # Запрашиваем больше чем нужно для фильтрации
    posts = await get_ai_posts(limit=api_limit)
    logger.info(f"📊 Получено постов из API: {len(posts) if posts else 0}")
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить посты. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # ДИАГНОСТИКА: анализируем уникальные каналы в постах
    unique_channels = set()
    posts_by_channel = {}
    for post in posts:
        if isinstance(post, dict):
            channel_id = post.get('channel_telegram_id')
            if channel_id:
                unique_channels.add(channel_id)
                if channel_id not in posts_by_channel:
                    posts_by_channel[channel_id] = 0
                posts_by_channel[channel_id] += 1
    
    logger.info(f"📺 ДИАГНОСТИКА: уникальные каналы в постах: {unique_channels}")
    logger.info(f"📺 ДИАГНОСТИКА: каналы в подписках: {subscribed_channel_telegram_ids}")
    logger.info(f"📊 ДИАГНОСТИКА: постов по каналам: {posts_by_channel}")
    
    # ДВОЙНАЯ ФИЛЬТРАЦИЯ: каналы ∩ категории
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_category_names, subscribed_channel_telegram_ids)
    
    logger.info(f"🔍 ДИАГНОСТИКА: после фильтрации осталось {len(filtered_posts)} постов")
    
    if not filtered_posts:
        keyboard = get_main_menu_keyboard()
        filter_info = ""
        if subscribed_channel_names:
            filter_info += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
        if subscribed_category_names:
            filter_info += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
        
        # Дополнительная диагностика для пустого результата
        debug_info = f"\n🔍 <b>Диагностика:</b>\n"
        debug_info += f"📊 Всего постов из API: {len(posts)}\n"
        debug_info += f"📺 Уникальные каналы в постах: {len(unique_channels)}\n"
        debug_info += f"📁 Категории в подписках: {len(subscribed_category_names)}\n"
        debug_info += f"📺 Каналы в подписках: {len(subscribed_channel_ids)}\n"
            
        await query.edit_message_text(
            f"📭 Нет новых постов по вашим фильтрам.\n\n"
            f"🎯 <b>Ваши фильтры:</b>\n{filter_info}\n"
            f"💡 Попробуйте расширить подписки или попробуйте позже.\n{debug_info}",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    # Сортируем посты по метрикам
    def calculate_score(post):
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        return importance * 3 + urgency * 2 + significance * 2
    
    filtered_posts.sort(key=calculate_score, reverse=True)
    
    # Ограничиваем количество постов согласно настройкам бота
    filtered_posts = filtered_posts[:max_posts_per_digest]
    
    # Группируем посты по КАТЕГОРИЯМ (как просил пользователь)
    posts_by_category = {}
    for post in filtered_posts:
        category = post.get('ai_category', 'Без категории')
        
        if category not in posts_by_category:
            posts_by_category[category] = []
        posts_by_category[category].append(post)
    
    # Сортируем категории по количеству постов (больше постов = выше)
    sorted_categories = sorted(posts_by_category.keys(), key=lambda cat: len(posts_by_category[cat]), reverse=True)
    
    # Формируем дайджест
    text = f"📰 <b>Персональный дайджест v4</b>\n"
    
    # Показываем активные фильтры
    text += f"🎯 <b>Фильтры:</b>\n"
    if subscribed_channel_names:
        text += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
    if subscribed_category_names:
        text += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
    
    text += f"📊 Найдено постов: {len(filtered_posts)} (лимит: {max_posts_per_digest})\n\n"
    
    # Показываем посты по КАТЕГОРИЯМ
    for category_name in sorted_categories:
        posts = posts_by_category[category_name]
        text += f"📁 <b>{category_name.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            ai_summary = post.get('ai_summary') or 'Нет описания'
            
            # Ограничиваем длину саммари для экономии места
            if len(ai_summary) > 200:
                ai_summary = ai_summary[:200] + "..."
            
            # Находим название канала для каждого поста
            channel_name = 'Неизвестный канал'
            channel_id = post.get('channel_telegram_id')
            for ch in channels:
                if ch['telegram_id'] == channel_id:
                    channel_name = ch['name']
                    break
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
            
            # Показываем источник (канал)
            text += f"   📺 {channel_name}\n"
        
        text += "\n"
    
    # Проверяем длину сообщения и разбиваем на части если нужно
    logger.info(f"📏 Длина дайджеста: {len(text)} символов")
    
    keyboard = get_main_menu_keyboard()
    message_parts = split_message(text)
    
    if len(message_parts) == 1:
        # Одно сообщение
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')
    else:
        # Несколько сообщений
        await query.edit_message_text(
            f"📰 <b>Дайджест разбит на {len(message_parts)} частей из-за размера</b>",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Отправляем части по очереди
        for i, part in enumerate(message_parts, 1):
            if i == len(message_parts):
                # Последняя часть с клавиатурой
                await query.message.reply_text(
                    f"📰 <b>Часть {i}/{len(message_parts)}</b>\n\n{part}",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                # Промежуточные части без клавиатуры
                await query.message.reply_text(
                    f"📰 <b>Часть {i}/{len(message_parts)}</b>\n\n{part}",
                    parse_mode='HTML'
                )

async def setup_bot_commands(application):
    """Настройка команд бота (кнопка меню слева)"""
    commands = [
        BotCommand("start", "🚀 Начать работу с ботом"),
        BotCommand("channels", "📺 Показать доступные каналы"),
        BotCommand("categories", "📁 Показать доступные категории"),
        BotCommand("subscribe", "🎯 Управление подписками"),
        BotCommand("digest", "📰 Получить персональный дайджест"),
        BotCommand("help", "❓ Показать справку"),
        BotCommand("test", "🧪 Тестовые данные"),
        BotCommand("debug", "🔧 Отладочная информация"),
        BotCommand("apitest", "🔍 API тест - анализ данных"),
        BotCommand("unsubscribe_all", "🗑️ Отписаться от всех каналов/категорий"),
        BotCommand("settings", "⚙️ Настройки бота (админ)"),
        BotCommand("setlimit", "📊 Изменить лимит постов (админ)"),
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        print("✅ Команды бота установлены (кнопка меню слева активна)")
    except Exception as e:
        print(f"❌ Ошибка установки команд: {e}")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Просмотр и изменение настроек бота (только для администратора)"""
    user_id = update.effective_user.id
    
    # Проверка прав администратора (можно настроить через переменные окружения)
    admin_ids = [123456789]  # Замените на реальный ID администратора
    if user_id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для изменения настроек бота.")
        return
    
    # Получаем текущие настройки
    bot_settings = await get_bot_settings()
    
    if not bot_settings:
        await update.message.reply_text("❌ Не удалось получить настройки бота.")
        return
    
    # Показываем текущие настройки
    text = f"⚙️ <b>Настройки бота</b>\n\n"
    text += f"📊 <b>Лимит постов в дайджесте:</b> {bot_settings.get('max_posts_per_digest', 10)}\n"
    text += f"📝 <b>Макс. длина саммари:</b> {bot_settings.get('max_summary_length', 150)}\n"
    text += f"🌐 <b>Язык по умолчанию:</b> {bot_settings.get('default_language', 'ru')}\n"
    text += f"⏰ <b>Часовой пояс:</b> {bot_settings.get('timezone', 'Europe/Moscow')}\n\n"
    
    text += f"📈 <b>Статистика:</b>\n"
    text += f"👥 Пользователей: {bot_settings.get('users_count', 0)}\n"
    text += f"📰 Дайджестов: {bot_settings.get('digests_count', 0)}\n"
    text += f"📺 Каналов: {bot_settings.get('channels_count', 0)}\n"
    text += f"📁 Категорий: {bot_settings.get('topics_count', 0)}\n\n"
    
    text += f"💡 <b>Для изменения лимита постов:</b>\n"
    text += f"Используйте команду: <code>/setlimit 15</code>\n"
    text += f"(допустимые значения: 5-30)"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def setlimit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Изменить лимит постов в дайджесте"""
    user_id = update.effective_user.id
    
    # Проверка прав администратора
    admin_ids = [123456789]  # Замените на реальный ID администратора
    if user_id not in admin_ids:
        await update.message.reply_text("❌ У вас нет прав для изменения настроек бота.")
        return
    
    # Получаем аргумент команды
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите новый лимит постов.\n\n"
            "Пример: <code>/setlimit 15</code>\n"
            "Допустимые значения: 5-30",
            parse_mode='HTML'
        )
        return
    
    try:
        new_limit = int(context.args[0])
        if new_limit < 5 or new_limit > 30:
            await update.message.reply_text("❌ Лимит должен быть от 5 до 30 постов.")
            return
    except ValueError:
        await update.message.reply_text("❌ Некорректное значение. Укажите число от 5 до 30.")
        return
    
    # Обновляем настройки через Backend API
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}"
            data = {"max_posts_per_digest": new_limit}
            
            async with session.put(url, json=data) as response:
                if response.status == 200:
                    await update.message.reply_text(
                        f"✅ Лимит постов в дайджесте изменен на {new_limit}.\n\n"
                        f"Изменения вступят в силу для новых дайджестов."
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Ошибка при обновлении настроек: {response.status}"
                    )
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении настроек: {e}")
        await update.message.reply_text("❌ Произошла ошибка при обновлении настроек.")

async def unsubscribe_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отписаться от всех каналов и категорий"""
    user_id = update.effective_user.id
    
    # Получаем текущие подписки
    current_category_ids = get_user_subscriptions(user_id, 'categories')
    current_channel_ids = get_user_subscriptions(user_id, 'channels')
    
    if not current_category_ids and not current_channel_ids:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            "📭 У вас нет активных подписок.",
            reply_markup=keyboard
        )
        return
    
    # Очищаем все подписки
    save_user_subscriptions(user_id, category_ids=[], channel_ids=[])
    
    # Подсчитываем что было удалено
    removed_categories = len(current_category_ids)
    removed_channels = len(current_channel_ids)
    
    keyboard = get_main_menu_keyboard()
    await update.message.reply_text(
        f"✅ <b>Все подписки удалены!</b>\n\n"
        f"📁 Удалено категорий: {removed_categories}\n"
        f"📺 Удалено каналов: {removed_channels}\n\n"
        f"💡 Используйте кнопку '🎯 Подписки' для настройки новых фильтров.",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("subscribe", subscriptions_command))
    application.add_handler(CommandHandler("digest", digest_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(CommandHandler("apitest", api_test_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("setlimit", setlimit_command))
    application.add_handler(CommandHandler("unsubscribe_all", unsubscribe_all_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    print(f"🚀 Запуск MorningStar Bot v4 (ДВОЙНАЯ ФИЛЬТРАЦИЯ)")
    print(f"🤖 Bot ID: {PUBLIC_BOT_ID}")
    print(f"💾 Режим: Подписки сохраняются в {SUBSCRIPTIONS_FILE}")
    print(f"🎯 Фильтрация: каналы ∩ категории")
    print(f"✅ Поддержка: каналы + категории + локальное хранение")
    
    # Настраиваем команды бота и запускаем
    async def post_init(application):
        await setup_bot_commands(application)
    
    application.post_init = post_init
    application.run_polling()

if __name__ == '__main__':
    main() 