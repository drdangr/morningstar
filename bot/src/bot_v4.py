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
            InlineKeyboardButton("📺 Каналы", callback_data="cmd_channels"),
            InlineKeyboardButton("📁 Категории", callback_data="cmd_categories")
        ],
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
    """Получить AI-обработанные посты"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}&ai_status=processed&limit={limit}"
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
    for post in posts:
        # Защита от ошибок - проверяем, что post это словарь
        if not isinstance(post, dict):
            logger.warning(f"Пропускаем пост неправильного формата: {type(post)}")
            continue
        
        # ФИЛЬТР 1: По каналам (если выбраны каналы)
        if subscribed_channel_ids:
            channel_telegram_id = post.get('channel_telegram_id')
            if not channel_telegram_id or channel_telegram_id not in subscribed_channel_ids:
                continue  # Пост не из выбранного канала
        
        # ФИЛЬТР 2: По категориям (если выбраны категории)
        if subscribed_categories:
            ai_category = post.get('ai_category', '')
            if not ai_category:
                continue  # У поста нет AI категории
                
            # Проверяем, содержит ли AI категория одну из подписанных категорий
            category_matches = False
            for sub_cat in subscribed_categories:
                if sub_cat.lower() in ai_category.lower():
                    category_matches = True
                    break
            
            if not category_matches:
                continue  # Категория поста не подходит
        
        # ПОСТ ПРОШЕЛ ВСЕ ФИЛЬТРЫ
        filtered_posts.append(post)
    
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
        f"• 🎪 Группировка дайджестов по каналам\n"
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
• Группировка дайджестов по каналам
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
    """Управление подписками на каналы и категории"""
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
    
    # Формируем текст с подписками
    text = f"🎯 <b>Ваши подписки для бота {PUBLIC_BOT_ID}</b>\n\n"
    
    # Подписки на каналы
    text += f"📺 <b>Каналы ({len(channel_subscriptions)} из {len(channels)}):</b>\n"
    if channel_subscriptions:
        for ch in channels:
            if ch['id'] in channel_subscriptions:
                text += f"  ✅ {ch['name']}\n"
    else:
        text += "  📭 Нет подписок на каналы\n"
    
    text += "\n"
    
    # Подписки на категории
    text += f"📁 <b>Категории ({len(category_subscriptions)} из {len(categories)}):</b>\n"
    if category_subscriptions:
        for cat in categories:
            if cat['id'] in category_subscriptions:
                text += f"  ✅ {cat['name']}\n"
    else:
        text += "  📭 Нет подписок на категории\n"
    
    # Создаем клавиатуру
    keyboard = [
        [
            InlineKeyboardButton("📺 Настроить каналы", callback_data="manage_channels"),
            InlineKeyboardButton("📁 Настроить категории", callback_data="manage_categories")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="cmd_subscriptions"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получить персональный дайджест с двойной фильтрацией"""
    user_id = update.effective_user.id
    
    # Получаем подписки пользователя
    subscribed_category_ids = get_user_subscriptions(user_id, 'categories')
    subscribed_channel_ids = get_user_subscriptions(user_id, 'channels')
    
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
    
    # Получаем AI посты
    posts = await get_ai_posts(limit=30)
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await loading_msg.edit_text(
            "❌ Не удалось получить посты. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # ДВОЙНАЯ ФИЛЬТРАЦИЯ: каналы ∩ категории
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_category_names, subscribed_channel_telegram_ids)
    
    if not filtered_posts:
        keyboard = get_main_menu_keyboard()
        filter_info = ""
        if subscribed_channel_names:
            filter_info += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
        if subscribed_category_names:
            filter_info += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
            
        await loading_msg.edit_text(
            f"📭 Нет новых постов по вашим фильтрам.\n\n"
            f"🎯 <b>Ваши фильтры:</b>\n{filter_info}\n"
            f"💡 Попробуйте расширить подписки или попробуйте позже.",
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
    
    # Ограничиваем количество постов
    max_posts = 10
    filtered_posts = filtered_posts[:max_posts]
    
    # Группируем посты по каналам
    posts_by_channel = {}
    for post in filtered_posts:
        channel_id = post.get('channel_telegram_id')
        channel_name = 'Неизвестный канал'
        
        # Находим название канала
        for ch in channels:
            if ch['telegram_id'] == channel_id:
                channel_name = ch['name']
                break
        
        if channel_name not in posts_by_channel:
            posts_by_channel[channel_name] = []
        posts_by_channel[channel_name].append(post)
    
    # Формируем дайджест
    text = f"📰 <b>Персональный дайджест v4</b>\n"
    
    # Показываем активные фильтры
    text += f"🎯 <b>Фильтры:</b>\n"
    if subscribed_channel_names:
        text += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
    if subscribed_category_names:
        text += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
    
    text += f"📊 Найдено постов: {len(filtered_posts)}\n\n"
    
    # Показываем посты по каналам
    for channel_name, posts in posts_by_channel.items():
        text += f"📺 <b>{channel_name.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            ai_summary = post.get('ai_summary') or 'Нет описания'
            ai_category = post.get('ai_category') or 'Нет категории'
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
            
            text += f"   🏷️ {ai_category}\n"
        
        text += "\n"
    
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
            text += f"  Тип: {type(post)}\n"
            if isinstance(post, dict):
                text += f"  Ключи: {list(post.keys())[:5]}\n"
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
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Обработка команд через кнопки
    if data == "cmd_categories":
        await categories_command_callback(query, context)
    elif data == "cmd_channels":
        await channels_command_callback(query, context)
    elif data == "cmd_subscriptions":
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
    elif data == "manage_channels":
        await manage_channels_callback(query, context)
    elif data == "manage_categories":
        await manage_categories_callback(query, context)
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
        await manage_channels_callback(query, context)
        
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
        await manage_categories_callback(query, context)
        
    elif data == "save_subscriptions":
        # Показываем текущие подписки
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            f"✅ Подписки для бота {PUBLIC_BOT_ID} сохранены!\n\n"
            f"🎯 Теперь вы будете получать персональные дайджесты по выбранным фильтрам:\n"
            f"• 📺 Каналы - источники новостей\n"
            f"• 📁 Категории - темы новостей\n\n"
            f"Используйте команду /digest для получения дайджеста.",
            reply_markup=keyboard
        )

# Callback версии команд
async def main_menu_callback(query, context):
    """Показать главное меню"""
    user = query.from_user
    keyboard = get_main_menu_keyboard()
    
    await query.edit_message_text(
        f"🏠 <b>Главное меню - MorningStar Bot v2</b>\n\n"
        f"Привет, {user.first_name}! 👋\n\n"
        f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
        f"⚡ Режим: Локальное хранение подписок\n\n"
        f"Выберите действие из меню ниже:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def categories_command_callback(query, context):
    """Показать категории через callback"""
    await query.edit_message_text("⏳ Загружаем категории...")
    
    categories = await get_bot_categories()
    
    if not categories:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
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
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def channels_command_callback(query, context):
    """Показать каналы через callback"""
    await query.edit_message_text("⏳ Загружаем каналы...")
    
    channels = await get_bot_channels()
    
    if not channels:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
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
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def subscriptions_command_callback(query, context):
    """Управление подписками через callback"""
    await query.edit_message_text("⏳ Загружаем подписки...")
    
    user_id = query.from_user.id
    categories = await get_bot_categories()
    
    if not categories:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить категории.",
            reply_markup=keyboard
        )
        return
    
    current_subscriptions = get_user_subscriptions(user_id)
    
    # Создаем inline клавиатуру
    keyboard = []
    for cat in categories:
        if cat['is_active']:
            is_subscribed = cat['id'] in current_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            text = f"{emoji} {cat['name']}"
            callback_data = f"toggle_category_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎯 <b>Управление подписками для бота {PUBLIC_BOT_ID}</b>\n\n"
    text += f"📊 Текущие подписки: {len(current_subscriptions)}\n\n"
    text += "Выберите категории для подписки:"
    
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
    
    # Получаем AI посты
    posts = await get_ai_posts(limit=30)
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить посты. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # ДВОЙНАЯ ФИЛЬТРАЦИЯ: каналы ∩ категории
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_category_names, subscribed_channel_telegram_ids)
    
    if not filtered_posts:
        keyboard = get_main_menu_keyboard()
        filter_info = ""
        if subscribed_channel_names:
            filter_info += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
        if subscribed_category_names:
            filter_info += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
            
        await query.edit_message_text(
            f"📭 Нет новых постов по вашим фильтрам.\n\n"
            f"🎯 <b>Ваши фильтры:</b>\n{filter_info}\n"
            f"💡 Попробуйте расширить подписки или попробуйте позже.",
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
    
    # Ограничиваем количество постов
    max_posts = 10
    filtered_posts = filtered_posts[:max_posts]
    
    # Группируем посты по каналам
    posts_by_channel = {}
    for post in filtered_posts:
        channel_id = post.get('channel_telegram_id')
        channel_name = 'Неизвестный канал'
        
        # Находим название канала
        for ch in channels:
            if ch['telegram_id'] == channel_id:
                channel_name = ch['name']
                break
        
        if channel_name not in posts_by_channel:
            posts_by_channel[channel_name] = []
        posts_by_channel[channel_name].append(post)
    
    # Формируем дайджест
    text = f"📰 <b>Персональный дайджест v4</b>\n"
    
    # Показываем активные фильтры
    text += f"🎯 <b>Фильтры:</b>\n"
    if subscribed_channel_names:
        text += f"📺 Каналы: {', '.join(subscribed_channel_names)}\n"
    if subscribed_category_names:
        text += f"📁 Категории: {', '.join(subscribed_category_names)}\n"
    
    text += f"📊 Найдено постов: {len(filtered_posts)}\n\n"
    
    # Показываем посты по каналам
    for channel_name, posts in posts_by_channel.items():
        text += f"📺 <b>{channel_name.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            ai_summary = post.get('ai_summary') or 'Нет описания'
            ai_category = post.get('ai_category') or 'Нет категории'
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
            
            text += f"   🏷️ {ai_category}\n"
        
        text += "\n"
    
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

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
• Группировка дайджестов по каналам
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
            text += f"  Тип: {type(post)}\n"
            if isinstance(post, dict):
                text += f"  Ключи: {list(post.keys())[:5]}\n"
                text += f"  ai_category: {post.get('ai_category', 'отсутствует')}\n"
                text += f"  channel_telegram_id: {post.get('channel_telegram_id', 'отсутствует')}\n"
                text += f"  title: {(post.get('title') or 'отсутствует')[:30]}\n"
            else:
                text += f"  Содержимое: {str(post)[:50]}\n"
    
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def manage_channels_callback(query, context):
    """Управление подписками на каналы"""
    await query.edit_message_text("⏳ Загружаем каналы...")
    
    user_id = query.from_user.id
    channels = await get_bot_channels()
    
    if not channels:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить каналы.",
            reply_markup=keyboard
        )
        return
    
    current_subscriptions = get_user_subscriptions(user_id, 'channels')
    
    # Создаем inline клавиатуру для каналов
    keyboard = []
    for ch in channels:
        if ch['is_active']:
            is_subscribed = ch['id'] in current_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            display_name = ch['name'][:30] + "..." if len(ch['name']) > 30 else ch['name']
            text = f"{emoji} {display_name}"
            callback_data = f"toggle_channel_{ch['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="cmd_subscriptions")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"📺 <b>Управление подписками на каналы</b>\n\n"
    text += f"📊 Текущие подписки: {len(current_subscriptions)} из {len(channels)}\n\n"
    text += "Выберите каналы для подписки:"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def manage_categories_callback(query, context):
    """Управление подписками на категории"""
    await query.edit_message_text("⏳ Загружаем категории...")
    
    user_id = query.from_user.id
    categories = await get_bot_categories()
    
    if not categories:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить категории.",
            reply_markup=keyboard
        )
        return
    
    current_subscriptions = get_user_subscriptions(user_id, 'categories')
    
    # Создаем inline клавиатуру для категорий
    keyboard = []
    for cat in categories:
        if cat['is_active']:
            is_subscribed = cat['id'] in current_subscriptions
            emoji = "✅" if is_subscribed else "⬜"
            text = f"{emoji} {cat['name']}"
            callback_data = f"toggle_category_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="cmd_subscriptions")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"📁 <b>Управление подписками на категории</b>\n\n"
    text += f"📊 Текущие подписки: {len(current_subscriptions)} из {len(categories)}\n\n"
    text += "Выберите категории для подписки:"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

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
    ]
    
    try:
        await application.bot.set_my_commands(commands)
        print("✅ Команды бота установлены (кнопка меню слева активна)")
    except Exception as e:
        print(f"❌ Ошибка установки команд: {e}")

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