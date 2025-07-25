#!/usr/bin/env python3
"""
🤖 MorningStar Bot v2 - Временное решение с локальным хранением подписок

РЕШЕНИЕ ПРОБЛЕМЫ:
- Backend API НЕ поддерживает мультитенантные подписки
- Используем локальное хранение подписок в памяти
- Фильтруем посты на стороне бота
- Все остальное работает через существующие endpoints
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
    """Создать основную клавиатуру с командами"""
    keyboard = [
        [
            InlineKeyboardButton("📁 Категории", callback_data="cmd_categories"),
            InlineKeyboardButton("🎯 Подписки", callback_data="cmd_subscribe")
        ],
        [
            InlineKeyboardButton("📰 Дайджест", callback_data="cmd_digest"),
            InlineKeyboardButton("❓ Справка", callback_data="cmd_help")
        ],
        [
            InlineKeyboardButton("🧪 Тест", callback_data="cmd_test"),
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

def save_user_subscriptions(user_id, category_ids):
    """Сохранить подписки пользователя (в память и файл)"""
    user_subscriptions[user_id] = category_ids
    save_subscriptions_to_file()  # Сохраняем в файл
    logger.info(f"💾 Сохранены подписки пользователя {user_id}: {category_ids} (в файл: {SUBSCRIPTIONS_FILE})")

def get_user_subscriptions(user_id):
    """Получить подписки пользователя (локально)"""
    return user_subscriptions.get(user_id, [])

def filter_posts_by_subscriptions(posts, subscribed_categories):
    """Фильтровать посты по подпискам"""
    if not subscribed_categories:
        return []
    
    filtered_posts = []
    for post in posts:
        # Защита от ошибок - проверяем, что post это словарь
        if not isinstance(post, dict):
            logger.warning(f"Пропускаем пост неправильного формата: {type(post)}")
            continue
            
        ai_category = post.get('ai_category', '')
        if ai_category:
            # Проверяем, содержит ли AI категория одну из подписанных категорий
            for sub_cat in subscribed_categories:
                if sub_cat.lower() in ai_category.lower():
                    filtered_posts.append(post)
                    break
    
    return filtered_posts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    keyboard = get_main_menu_keyboard()
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я MorningStar Bot (v2) - ваш персональный дайджест Telegram каналов.\n\n"
        f"🚀 Новая версия с поддержкой:\n"
        f"• 🤖 AI-категоризация и саммаризация постов\n"
        f"• 🎯 Мультитенантность (bot_id: {PUBLIC_BOT_ID})\n"
        f"• 📊 Умные метрики (важность, срочность, значимость)\n"
        f"• 🎪 Персональные дайджесты по подпискам\n\n"
        f"💾 Подписки сохраняются в файл (user_subscriptions.json)\n\n"
        f"Выберите действие из меню ниже:",
        reply_markup=keyboard
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = f"""
🤖 <b>MorningStar Bot v2 - Команды:</b>

📋 <b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать справку
/categories - Показать доступные категории
/subscribe - Управление подписками
/digest - Получить персональный дайджест

🔧 <b>Отладка:</b>
/test - Показать 10 AI постов
/debug - Техническая информация

💡 <b>Особенности v2:</b>
• Использует endpoint /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}
• Подписки сохраняются в файл user_subscriptions.json
• Фильтрация постов по AI категориям
• Умная сортировка по метрикам
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

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Управление подписками"""
    user_id = update.effective_user.id
    categories = await get_bot_categories()
    
    if not categories:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
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
            callback_data = f"toggle_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎯 <b>Управление подписками для бота {PUBLIC_BOT_ID}</b>\n\n"
    text += f"📊 Текущие подписки: {len(current_subscriptions)}\n\n"
    text += "Выберите категории для подписки:"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получить персональный дайджест"""
    user_id = update.effective_user.id
    subscribed_category_ids = get_user_subscriptions(user_id)
    
    if not subscribed_category_ids:
        keyboard = get_main_menu_keyboard()
        await update.message.reply_text(
            f"📭 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            f"Используйте команду /subscribe для выбора интересующих категорий, "
            f"а затем повторите запрос дайджеста.",
            reply_markup=keyboard
        )
        return
    
    # Показываем индикатор загрузки
    loading_msg = await update.message.reply_text("⏳ Формируем персональный дайджест...")
    
    # Получаем категории для понимания названий
    categories = await get_bot_categories()
    category_names = {cat['id']: cat['name'] for cat in categories}
    subscribed_names = [category_names.get(cat_id, f"Категория {cat_id}") for cat_id in subscribed_category_ids]
    
    # Получаем AI посты
    posts = await get_ai_posts(limit=20)
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await loading_msg.edit_text(
            "❌ Не удалось получить посты. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # Фильтруем посты по подпискам
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_names)
    
    if not filtered_posts:
        keyboard = get_main_menu_keyboard()
        await loading_msg.edit_text(
            f"📭 Нет новых постов по вашим подпискам.\n\n"
            f"🎯 Ваши подписки: {', '.join(subscribed_names)}\n\n"
            f"Попробуйте позже или измените подписки командой /subscribe.",
            reply_markup=keyboard
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
    
    # Группируем посты по категориям
    posts_by_category = {}
    for post in filtered_posts:
        category = post.get('ai_category') or 'Нет категории'
        if category not in posts_by_category:
            posts_by_category[category] = []
        posts_by_category[category].append(post)
    
    # Формируем компактный дайджест
    text = f"📰 <b>Персональный дайджест</b>\n"
    text += f"🎯 Подписки: {', '.join(subscribed_names)}\n"
    text += f"📊 Найдено постов: {len(filtered_posts)}\n\n"
    
    for category, posts in posts_by_category.items():
        text += f"<b>{category.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            ai_summary = post.get('ai_summary') or 'Нет описания'
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
        
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
    subscriptions = get_user_subscriptions(user_id)
    
    # Проверяем API
    posts = await get_ai_posts(limit=3)
    
    text = f"🔧 <b>Отладочная информация</b>\n\n"
    text += f"👤 User ID: {user_id}\n"
    text += f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
    text += f"🔗 Backend URL: {BACKEND_URL}\n"
    text += f"📊 Локальные подписки: {subscriptions}\n"
    text += f"📝 Всего пользователей в памяти: {len(user_subscriptions)}\n\n"
    text += f"💾 Режим: Подписки в файле {SUBSCRIPTIONS_FILE}\n"
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
    elif data == "cmd_subscribe":
        await subscribe_command_callback(query, context)
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
    elif data.startswith("toggle_"):
        # Обработка toggle подписок
        category_id = int(data.split("_")[1])
        current_subscriptions = get_user_subscriptions(user_id)
        
        if category_id in current_subscriptions:
            current_subscriptions.remove(category_id)
        else:
            current_subscriptions.append(category_id)
        
        save_user_subscriptions(user_id, current_subscriptions)
        
        # Обновляем сообщение
        await subscribe_command_callback(query, context)
        
    elif data == "save_subscriptions":
        current_subscriptions = get_user_subscriptions(user_id)
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            f"✅ Подписки для бота {PUBLIC_BOT_ID} сохранены!\n\n"
            f"Подписки обновлены. Выбрано категорий: {len(current_subscriptions)}\n\n"
            f"Теперь вы будете получать персональные дайджесты по выбранным категориям.",
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

async def subscribe_command_callback(query, context):
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
            callback_data = f"toggle_{cat['id']}"
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
    await query.edit_message_text("⏳ Формируем персональный дайджест...")
    
    user_id = query.from_user.id
    subscribed_category_ids = get_user_subscriptions(user_id)
    
    if not subscribed_category_ids:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            f"📭 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            f"Используйте кнопку 'Подписки' для выбора интересующих категорий, "
            f"а затем повторите запрос дайджеста.",
            reply_markup=keyboard
        )
        return
    
    # Получаем категории для понимания названий
    categories = await get_bot_categories()
    category_names = {cat['id']: cat['name'] for cat in categories}
    subscribed_names = [category_names.get(cat_id, f"Категория {cat_id}") for cat_id in subscribed_category_ids]
    
    # Получаем AI посты
    posts = await get_ai_posts(limit=20)
    
    if not posts:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Не удалось получить посты. Попробуйте позже.",
            reply_markup=keyboard
        )
        return
    
    # Фильтруем посты по подпискам
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_names)
    
    if not filtered_posts:
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            f"📭 Нет новых постов по вашим подпискам.\n\n"
            f"🎯 Ваши подписки: {', '.join(subscribed_names)}\n\n"
            f"Попробуйте позже или измените подписки.",
            reply_markup=keyboard
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
    
    # Группируем посты по категориям
    posts_by_category = {}
    for post in filtered_posts:
        category = post.get('ai_category') or 'Нет категории'
        if category not in posts_by_category:
            posts_by_category[category] = []
        posts_by_category[category].append(post)
    
    # Формируем компактный дайджест
    text = f"📰 <b>Персональный дайджест</b>\n"
    text += f"🎯 Подписки: {', '.join(subscribed_names)}\n"
    text += f"📊 Найдено постов: {len(filtered_posts)}\n\n"
    
    for category, posts in posts_by_category.items():
        text += f"<b>{category.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            ai_summary = post.get('ai_summary') or 'Нет описания'
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
        
        text += "\n"
    
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def help_command_callback(query, context):
    """Показать справку через callback"""
    help_text = f"""
🤖 <b>MorningStar Bot v2 - Справка</b>

📋 <b>Основные функции:</b>
• 📁 Категории - Показать доступные категории
• 🎯 Подписки - Управление подписками на категории
• 📰 Дайджест - Получить персональный дайджест
• ❓ Справка - Показать эту справку

🔧 <b>Отладка:</b>
• 🧪 Тест - Показать 10 AI постов
• 🔧 Отладка - Техническая информация

💡 <b>Особенности v2:</b>
• Использует endpoint /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}
• Подписки сохраняются в файл user_subscriptions.json
• Фильтрация постов по AI категориям
• Умная сортировка по метрикам
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
    subscriptions = get_user_subscriptions(user_id)
    
    # Проверяем API
    posts = await get_ai_posts(limit=3)
    
    text = f"🔧 <b>Отладочная информация</b>\n\n"
    text += f"👤 User ID: {user_id}\n"
    text += f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
    text += f"🔗 Backend URL: {BACKEND_URL}\n"
    text += f"📊 Локальные подписки: {subscriptions}\n"
    text += f"📝 Всего пользователей в памяти: {len(user_subscriptions)}\n\n"
    text += f"💾 Режим: Подписки в файле {SUBSCRIPTIONS_FILE}\n"
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
                text += f"  title: {(post.get('title') or 'отсутствует')[:30]}\n"
            else:
                text += f"  Содержимое: {str(post)[:50]}\n"
    
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='HTML')

async def setup_bot_commands(application):
    """Настройка команд бота (кнопка меню слева)"""
    commands = [
        BotCommand("start", "🚀 Начать работу с ботом"),
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
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("digest", digest_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("debug", debug_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    print(f"🚀 Запуск MorningStar Bot v2 (Подписки в файле)")
    print(f"🤖 Bot ID: {PUBLIC_BOT_ID}")
    print(f"💾 Режим: Подписки сохраняются в {SUBSCRIPTIONS_FILE}")
    
    # Настраиваем команды бота и запускаем
    async def post_init(application):
        await setup_bot_commands(application)
    
    application.post_init = post_init
    application.run_polling()

if __name__ == '__main__':
    main() 