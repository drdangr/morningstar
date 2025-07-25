#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 TELEGRAM BOT v3.0 - ПОЛНАЯ МУЛЬТИТЕНАНТНАЯ АРХИТЕКТУРА
- Двойная фильтрация: подписки на категории И каналы  
- Backend API интеграция (без файлового хранения)
- Автоподписка на все категории/каналы при первом старте
- Учет max_posts_per_digest из настроек бота
- Inline-клавиатура с удобным UI
"""

import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode

# =============================================================================
# КОНФИГУРАЦИЯ БОТА
# =============================================================================
BOT_TOKEN = "8124620179:AAHNt4-7ZFg-zz0Cr6mJX483jDuNeARpIdE"
BOT_ID = 4  # ID бота в Backend API
BACKEND_URL = "http://127.0.0.1:8000"

# =============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =============================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================================================
# BACKEND API ИНТЕГРАЦИЯ
# =============================================================================

async def api_request(method, endpoint, data=None):
    """Универсальная функция для запросов к Backend API"""
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, params=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API Error {response.status}: {await response.text()}")
                        return None
            
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        logger.error(f"API Error {response.status}: {await response.text()}")
                        return None
            
            elif method.upper() == "DELETE":
                async with session.delete(url) as response:
                    if response.status in [200, 204]:
                        return {"success": True}
                    else:
                        logger.error(f"API Error {response.status}: {await response.text()}")
                        return None
                        
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return None

async def get_bot_data():
    """Получить данные бота из Backend API"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}")

async def get_bot_categories():
    """Получить категории бота"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/categories")

async def get_bot_channels():
    """Получить каналы бота"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/channels")

async def get_user_category_subscriptions(telegram_id):
    """Получить подписки пользователя на категории"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/subscriptions")

async def get_user_channel_subscriptions(telegram_id):
    """Получить подписки пользователя на каналы"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/channel-subscriptions")

async def update_user_category_subscriptions(telegram_id, category_ids):
    """Обновить подписки пользователя на категории"""
    return await api_request("POST", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/subscriptions", 
                           {"category_ids": category_ids})

async def update_user_channel_subscriptions(telegram_id, channel_ids):
    """Обновить подписки пользователя на каналы"""
    return await api_request("POST", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/channel-subscriptions", 
                           {"channel_ids": channel_ids})

async def get_ai_posts_filtered(subscribed_channel_ids, subscribed_categories, max_posts):
    """
    Получить посты с двойной фильтрацией:
    1. Только из подписанных каналов  
    2. Только с подписанными категориями
    """
    try:
        # Формируем параметры запроса
        params = {
            "bot_id": BOT_ID,
            "limit": max_posts * 3,  # Запрашиваем больше для качественной фильтрации
            "ai_status": "processed",
            "sort_by": "collected_at",
            "sort_order": "desc"
        }
        
        response = await api_request("GET", "/api/posts/cache-with-ai", params)
        
        if not response:
            return []
        
        # Определяем структуру ответа
        if isinstance(response, dict):
            posts_data = None
            for key in ['posts', 'data', 'results', 'items']:
                if key in response:
                    posts_data = response[key]
                    break
            
            if posts_data is None:
                logger.warning(f"Не найдено поле с постами в ответе API. Ключи: {response.keys()}")
                return []
        else:
            posts_data = response

        if not isinstance(posts_data, list):
            logger.error(f"Неожиданная структура данных: {type(posts_data)}")
            return []

        filtered_posts = []
        
        for post in posts_data:
            # Парсим пост если он в виде строки
            if isinstance(post, str):
                try:
                    post = json.loads(post)
                except:
                    continue
            
            if not isinstance(post, dict):
                continue
            
            # 1. ФИЛЬТР ПО КАНАЛАМ: пост должен быть из подписанного канала
            channel_telegram_id = post.get('channel_telegram_id')
            if not channel_telegram_id or channel_telegram_id not in subscribed_channel_ids:
                continue
            
            # 2. ФИЛЬТР ПО КАТЕГОРИЯМ: получаем AI категорию поста
            ai_categories = post.get('ai_categories')
            if ai_categories:
                # Парсим JSON если нужно
                if isinstance(ai_categories, str):
                    try:
                        ai_categories = json.loads(ai_categories)
                    except:
                        continue
                
                # Ищем category в разных возможных форматах
                post_category = None
                if isinstance(ai_categories, dict):
                    post_category = ai_categories.get('category') or ai_categories.get('categories')
                
                # Проверяем что категория поста входит в подписки пользователя
                if post_category and post_category in subscribed_categories:
                    # Получаем AI summary
                    ai_summaries = post.get('ai_summaries', {})
                    if isinstance(ai_summaries, str):
                        try:
                            ai_summaries = json.loads(ai_summaries)
                        except:
                            ai_summaries = {}
                    
                    summary = ai_summaries.get('summary', 'Описание недоступно')
                    
                    # Формируем ссылку на пост
                    channel_username = None
                    # Здесь нужно было бы получить username канала, но пока упростим
                    message_id = post.get('telegram_message_id')
                    post_url = f"https://t.me/c/{abs(channel_telegram_id)}/{message_id}" if message_id else "#"
                    
                    filtered_posts.append({
                        'title': (post.get('title') or 'Без заголовка')[:50],
                        'ai_summary': summary,
                        'ai_category': post_category,
                        'post_url': post_url,
                        'channel_telegram_id': channel_telegram_id,
                        'post_date': post.get('post_date')
                    })
                    
                    # Ограничиваем количество постов
                    if len(filtered_posts) >= max_posts:
                        break
        
        return filtered_posts
        
    except Exception as e:
        logger.error(f"Ошибка при получении постов: {e}")
        return []

async def ensure_user_subscriptions(telegram_id):
    """
    Убеждаемся что пользователь подписан на все категории и каналы бота
    (автоподписка при первом старте)
    """
    try:
        # Получаем все категории и каналы бота
        bot_categories = await get_bot_categories()
        bot_channels = await get_bot_channels()
        
        if not bot_categories or not bot_channels:
            logger.warning("Не удалось получить категории или каналы бота")
            return False
        
        # Получаем текущие подписки пользователя
        user_category_subs = await get_user_category_subscriptions(telegram_id)
        user_channel_subs = await get_user_channel_subscriptions(telegram_id)
        
        # Извлекаем ID подписанных категорий и каналов
        subscribed_category_ids = []
        if user_category_subs and 'subscribed_categories' in user_category_subs:
            subscribed_category_ids = [cat['id'] for cat in user_category_subs['subscribed_categories']]
        
        subscribed_channel_ids = []
        if user_channel_subs and 'subscribed_channels' in user_channel_subs:
            subscribed_channel_ids = [ch['id'] for ch in user_channel_subs['subscribed_channels']]
        
        # Получаем ID всех доступных категорий и каналов
        all_category_ids = [cat['id'] for cat in bot_categories]
        all_channel_ids = [ch['id'] for ch in bot_channels]
        
        # Проверяем нужно ли обновить подписки
        needs_category_update = set(subscribed_category_ids) != set(all_category_ids)
        needs_channel_update = set(subscribed_channel_ids) != set(all_channel_ids)
        
        # Обновляем подписки если нужно
        if needs_category_update:
            logger.info(f"Автоподписка на категории для пользователя {telegram_id}")
            await update_user_category_subscriptions(telegram_id, all_category_ids)
        
        if needs_channel_update:
            logger.info(f"Автоподписка на каналы для пользователя {telegram_id}")
            await update_user_channel_subscriptions(telegram_id, all_channel_ids)
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обеспечении подписок: {e}")
        return False

# =============================================================================
# UI КОМПОНЕНТЫ
# =============================================================================

def get_main_menu_keyboard():
    """Главное меню с inline-кнопками"""
    keyboard = [
        [
            InlineKeyboardButton("📁 Категории", callback_data="categories"),
            InlineKeyboardButton("📺 Каналы", callback_data="channels")
        ],
        [
            InlineKeyboardButton("🎯 Мои подписки", callback_data="my_subscriptions"),
            InlineKeyboardButton("📰 Дайджест", callback_data="digest")
        ],
        [
            InlineKeyboardButton("❓ Справка", callback_data="help"),
            InlineKeyboardButton("🔧 Настройки", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_categories_keyboard(telegram_id):
    """Клавиатура с категориями и их статусом подписки"""
    categories = await get_bot_categories()
    user_subs = await get_user_category_subscriptions(telegram_id)
    
    if not categories:
        return None
    
    subscribed_ids = []
    if user_subs and 'subscribed_categories' in user_subs:
        subscribed_ids = [cat['id'] for cat in user_subs['subscribed_categories']]
    
    keyboard = []
    for cat in categories:
        status = "✅" if cat['id'] in subscribed_ids else "⭕"
        text = f"{status} {cat['name']}"
        callback_data = f"toggle_category_{cat['id']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

async def get_channels_keyboard(telegram_id):
    """Клавиатура с каналами и их статусом подписки"""
    channels = await get_bot_channels()
    user_subs = await get_user_channel_subscriptions(telegram_id)
    
    if not channels:
        return None
    
    subscribed_ids = []
    if user_subs and 'subscribed_channels' in user_subs:
        subscribed_ids = [ch['id'] for ch in user_subs['subscribed_channels']]
    
    keyboard = []
    for ch in channels:
        status = "✅" if ch['id'] in subscribed_ids else "⭕"
        text = f"{status} {ch.get('title', ch.get('channel_name', 'Канал'))}"
        callback_data = f"toggle_channel_{ch['id']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

# =============================================================================
# ОБРАБОТЧИКИ КОМАНД
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    # Автоподписка на все категории и каналы
    await ensure_user_subscriptions(user.id)
    
    welcome_text = f"""
🤖 **Добро пожаловать, {user.first_name}!**

Это умный новостной бот с персонализированными дайджестами.

**🎯 Как это работает:**
• Выберите интересующие **категории** новостей
• Выберите интересующие **каналы** источников  
• Получайте дайджесты только с постами из выбранных каналов по выбранным темам

**📱 Управление:**
Используйте меню ниже или команды:
/categories - управление категориями
/channels - управление каналами  
/digest - получить дайджест
/help - справка
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 **СПРАВКА ПО БОТУ**

**🎯 Основная логика:**
Дайджест формируется по принципу двойной фильтрации:
1️⃣ Берутся посты только из ваших **подписанных каналов**
2️⃣ Из них выбираются только посты по **подписанным категориям**

**📱 Доступные команды:**
/start - запуск и главное меню
/categories - управление подписками на категории
/channels - управление подписками на каналы
/digest - получить персональный дайджест
/subscriptions - просмотр всех подписок
/help - эта справка

**💡 Совет:**
Подпишитесь на несколько интересных каналов и категорий для получения релевантного контента!
"""
    
    await update.effective_message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /categories"""
    user_id = update.effective_user.id
    keyboard = await get_categories_keyboard(user_id)
    
    if not keyboard:
        await update.effective_message.reply_text(
            "❌ Не удалось загрузить категории. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await update.effective_message.reply_text(
        "📁 **УПРАВЛЕНИЕ КАТЕГОРИЯМИ**\n\n"
        "Выберите категории, которые вас интересуют:\n"
        "✅ - подписан\n"
        "⭕ - не подписан",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /channels"""
    user_id = update.effective_user.id
    keyboard = await get_channels_keyboard(user_id)
    
    if not keyboard:
        await update.effective_message.reply_text(
            "❌ Не удалось загрузить каналы. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await update.effective_message.reply_text(
        "📺 **УПРАВЛЕНИЕ КАНАЛАМИ**\n\n"
        "Выберите каналы-источники, которые вас интересуют:\n"
        "✅ - подписан\n"
        "⭕ - не подписан",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /digest"""
    user_id = update.effective_user.id
    
    # Показываем индикатор загрузки
    loading_msg = await update.effective_message.reply_text("🔍 Формирую персональный дайджест...")
    
    try:
        # Получаем настройки бота
        bot_data = await get_bot_data()
        max_posts = bot_data.get('max_posts_per_digest', 10) if bot_data else 10
        
        # Получаем подписки пользователя
        category_subs = await get_user_category_subscriptions(user_id)
        channel_subs = await get_user_channel_subscriptions(user_id)
        
        if not category_subs or not channel_subs:
            await loading_msg.edit_text(
                "❌ Не удалось загрузить ваши подписки. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Извлекаем подписанные категории и каналы
        subscribed_categories = [cat['name'] for cat in category_subs.get('subscribed_categories', [])]
        subscribed_channel_ids = [ch['telegram_id'] for ch in channel_subs.get('subscribed_channels', [])]
        
        if not subscribed_categories or not subscribed_channel_ids:
            await loading_msg.edit_text(
                "⚠️ У вас нет активных подписок.\n\n"
                "Подпишитесь на категории и каналы для получения дайджеста.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Получаем отфильтрованные посты
        posts = await get_ai_posts_filtered(subscribed_channel_ids, subscribed_categories, max_posts)
        
        if not posts:
            await loading_msg.edit_text(
                "📭 **Дайджест пуст**\n\n"
                f"По вашим подпискам ({len(subscribed_categories)} категорий, {len(subscribed_channel_ids)} каналов) "
                "новых релевантных постов не найдено.\n\n"
                "Попробуйте:\n"
                "• Расширить список категорий\n"
                "• Добавить больше каналов\n"
                "• Проверить позже",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Формируем дайджест по категориям
        digest_text = f"📰 **ПЕРСОНАЛЬНЫЙ ДАЙДЖЕСТ**\n"
        digest_text += f"🎯 {len(subscribed_categories)} категорий, {len(subscribed_channel_ids)} каналов\n"
        digest_text += f"📊 Найдено {len(posts)} релевантных постов\n\n"
        
        # Группируем по категориям
        posts_by_category = {}
        for post in posts:
            category = post['ai_category']
            if category not in posts_by_category:
                posts_by_category[category] = []
            posts_by_category[category].append(post)
        
        # Выводим посты по категориям
        for category, category_posts in posts_by_category.items():
            digest_text += f"**📁 {category.upper()}**\n"
            for i, post in enumerate(category_posts, 1):
                digest_text += f"{i}. {post['ai_summary']} <a href='{post['post_url']}'>🔗</a>\n"
            digest_text += "\n"
        
        digest_text += f"⏰ Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        await loading_msg.edit_text(
            digest_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard(),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка при формировании дайджеста: {e}")
        await loading_msg.edit_text(
            "❌ Произошла ошибка при формировании дайджеста. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def subscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /subscriptions"""
    user_id = update.effective_user.id
    
    try:
        # Получаем подписки
        category_subs = await get_user_category_subscriptions(user_id)
        channel_subs = await get_user_channel_subscriptions(user_id)
        
        text = "🎯 **МОИ ПОДПИСКИ**\n\n"
        
        # Категории
        if category_subs and category_subs.get('subscribed_categories'):
            text += "📁 **Категории:**\n"
            for cat in category_subs['subscribed_categories']:
                text += f"• {cat['name']}\n"
        else:
            text += "📁 **Категории:** нет подписок\n"
        
        text += "\n"
        
        # Каналы
        if channel_subs and channel_subs.get('subscribed_channels'):
            text += "📺 **Каналы:**\n"
            for ch in channel_subs['subscribed_channels']:
                title = ch.get('title', ch.get('channel_name', 'Канал'))
                text += f"• {title}\n"
        else:
            text += "📺 **Каналы:** нет подписок\n"
        
        await update.effective_message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении подписок: {e}")
        await update.effective_message.reply_text(
            "❌ Не удалось загрузить подписки. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

# =============================================================================
# ОБРАБОТЧИК CALLBACK ЗАПРОСОВ (КНОПКИ)
# =============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех callback запросов от inline-кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        # Главное меню
        if data == "back_to_menu":
            await query.edit_message_text(
                "🏠 **ГЛАВНОЕ МЕНЮ**\n\nВыберите действие:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard()
            )
        
        elif data == "categories":
            await categories_command_callback(query)
            
        elif data == "channels":
            await channels_command_callback(query)
            
        elif data == "my_subscriptions":
            await subscriptions_command_callback(query)
            
        elif data == "digest":
            await digest_command_callback(query)
            
        elif data == "help":
            await help_command_callback(query)
            
        elif data == "settings":
            await query.edit_message_text(
                "🔧 **НАСТРОЙКИ**\n\n"
                "В данной версии настройки управляются через админ-панель.\n"
                "Скоро будут добавлены пользовательские настройки!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]])
            )
        
        # Переключение категорий
        elif data.startswith("toggle_category_"):
            category_id = int(data.split("_")[-1])
            await toggle_category_subscription(query, user_id, category_id)
            
        # Переключение каналов  
        elif data.startswith("toggle_channel_"):
            channel_id = int(data.split("_")[-1])
            await toggle_channel_subscription(query, user_id, channel_id)
            
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

# Callback-версии команд
async def categories_command_callback(query):
    """Callback-версия команды categories"""
    keyboard = await get_categories_keyboard(query.from_user.id)
    if not keyboard:
        await query.edit_message_text(
            "❌ Не удалось загрузить категории.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await query.edit_message_text(
        "📁 **УПРАВЛЕНИЕ КАТЕГОРИЯМИ**\n\n"
        "Выберите категории, которые вас интересуют:\n"
        "✅ - подписан\n"
        "⭕ - не подписан",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def channels_command_callback(query):
    """Callback-версия команды channels"""
    keyboard = await get_channels_keyboard(query.from_user.id)
    if not keyboard:
        await query.edit_message_text(
            "❌ Не удалось загрузить каналы.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await query.edit_message_text(
        "📺 **УПРАВЛЕНИЕ КАНАЛАМИ**\n\n"
        "Выберите каналы-источники, которые вас интересуют:\n"
        "✅ - подписан\n"
        "⭕ - не подписан",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def subscriptions_command_callback(query):
    """Callback-версия команды subscriptions"""
    user_id = query.from_user.id
    
    try:
        category_subs = await get_user_category_subscriptions(user_id)
        channel_subs = await get_user_channel_subscriptions(user_id)
        
        text = "🎯 **МОИ ПОДПИСКИ**\n\n"
        
        if category_subs and category_subs.get('subscribed_categories'):
            text += "📁 **Категории:**\n"
            for cat in category_subs['subscribed_categories']:
                text += f"• {cat['name']}\n"
        else:
            text += "📁 **Категории:** нет подписок\n"
        
        text += "\n"
        
        if channel_subs and channel_subs.get('subscribed_channels'):
            text += "📺 **Каналы:**\n"
            for ch in channel_subs['subscribed_channels']:
                title = ch.get('title', ch.get('channel_name', 'Канал'))
                text += f"• {title}\n"
        else:
            text += "📺 **Каналы:** нет подписок\n"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]])
        )
        
    except Exception as e:
        logger.error(f"Ошибка при получении подписок: {e}")
        await query.edit_message_text(
            "❌ Не удалось загрузить подписки.",
            reply_markup=get_main_menu_keyboard()
        )

async def digest_command_callback(query):
    """Callback-версия команды digest"""
    # Создаем временный Update объект для совместимости
    temp_update = Update(
        update_id=0,
        message=query.message,
        callback_query=query
    )
    temp_update.effective_message = query.message
    temp_update.effective_user = query.from_user
    
    # Вызываем основную функцию
    await digest_command(temp_update, None)

async def help_command_callback(query):
    """Callback-версия команды help"""
    help_text = """
📖 **СПРАВКА ПО БОТУ**

**🎯 Основная логика:**
Дайджест формируется по принципу двойной фильтрации:
1️⃣ Берутся посты только из ваших **подписанных каналов**
2️⃣ Из них выбираются только посты по **подписанным категориям**

**📱 Доступные команды:**
/start - запуск и главное меню
/categories - управление подписками на категории  
/channels - управление подписками на каналы
/digest - получить персональный дайджест
/subscriptions - просмотр всех подписок
/help - эта справка

**💡 Совет:**
Подпишитесь на несколько интересных каналов и категорий для получения релевантного контента!
"""
    
    await query.edit_message_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]])
    )

# =============================================================================
# ФУНКЦИИ ПЕРЕКЛЮЧЕНИЯ ПОДПИСОК
# =============================================================================

async def toggle_category_subscription(query, user_id, category_id):
    """Переключить подписку на категорию"""
    try:
        # Получаем текущие подписки
        current_subs = await get_user_category_subscriptions(user_id)
        subscribed_ids = []
        
        if current_subs and 'subscribed_categories' in current_subs:
            subscribed_ids = [cat['id'] for cat in current_subs['subscribed_categories']]
        
        # Переключаем подписку
        if category_id in subscribed_ids:
            subscribed_ids.remove(category_id)
        else:
            subscribed_ids.append(category_id)
        
        # Обновляем подписки
        result = await update_user_category_subscriptions(user_id, subscribed_ids)
        
        if result:
            # Обновляем клавиатуру
            keyboard = await get_categories_keyboard(user_id)
            await query.edit_message_reply_markup(reply_markup=keyboard)
        else:
            await query.answer("❌ Ошибка при обновлении подписки", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка при переключении категории: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)

async def toggle_channel_subscription(query, user_id, channel_id):
    """Переключить подписку на канал"""
    try:
        # Получаем текущие подписки
        current_subs = await get_user_channel_subscriptions(user_id)
        subscribed_ids = []
        
        if current_subs and 'subscribed_channels' in current_subs:
            subscribed_ids = [ch['id'] for ch in current_subs['subscribed_channels']]
        
        # Переключаем подписку
        if channel_id in subscribed_ids:
            subscribed_ids.remove(channel_id)
        else:
            subscribed_ids.append(channel_id)
        
        # Обновляем подписки
        result = await update_user_channel_subscriptions(user_id, subscribed_ids)
        
        if result:
            # Обновляем клавиатуру
            keyboard = await get_channels_keyboard(user_id)
            await query.edit_message_reply_markup(reply_markup=keyboard)
        else:
            await query.answer("❌ Ошибка при обновлении подписки", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка при переключении канала: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)

# =============================================================================
# НАСТРОЙКА КОМАНД БОТА
# =============================================================================

async def setup_bot_commands(application):
    """Настройка команд бота для отображения в меню"""
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("categories", "📁 Управление категориями"),
        BotCommand("channels", "📺 Управление каналами"),
        BotCommand("digest", "📰 Получить дайджест"),
        BotCommand("subscriptions", "🎯 Мои подписки"),
        BotCommand("help", "❓ Справка"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("Команды бота настроены")

# =============================================================================
# ЗАПУСК БОТА
# =============================================================================

async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск Telegram Bot v3.0 - Мультитенантная архитектура")
    
    # Проверяем подключение к Backend API
    bot_data = await get_bot_data()
    if not bot_data:
        logger.error("❌ Не удалось подключиться к Backend API")
        return
    
    logger.info(f"✅ Подключение к Backend API установлено. Бот: {bot_data.get('name')}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем команды меню
    await setup_bot_commands(application)
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("digest", digest_command))
    application.add_handler(CommandHandler("subscriptions", subscriptions_command))
    
    # Обработчик callback запросов (кнопки)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик неизвестных сообщений
    async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤔 Не понимаю эту команду. Воспользуйтесь меню или /help",
            reply_markup=get_main_menu_keyboard()
        )
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))
    
    # Запускаем бота
    logger.info("✅ Бот запущен и готов к работе!")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main()) 