#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 TELEGRAM BOT v3.0 - ПРАВИЛЬНАЯ ДВОЙНАЯ ФИЛЬТРАЦИЯ 
Каналы ∩ Категории = Персонализированные дайджесты
"""

print("🔍 Запуск bot_v3_working.py...")
print("Тестовый файл создан")

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

print("📦 Базовые импорты выполнены")

try:
    import aiohttp
    print("✅ aiohttp импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта aiohttp: {e}")
    exit(1)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    from telegram.constants import ParseMode
    print("✅ telegram импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта telegram: {e}")
    exit(1)

# =============================================================================
# КОНФИГУРАЦИЯ
# =============================================================================
BOT_TOKEN = "8124620179:AAHNt4-7ZFg-zz0Cr6mJX483jDuNeARpIdE"
BOT_ID = 4
BACKEND_URL = "http://127.0.0.1:8000"

print(f"⚙️ Конфигурация: BOT_ID={BOT_ID}, BACKEND_URL={BACKEND_URL}")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("📝 Логирование настроено")

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
                    if response.status in [200, 201]:
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
            else:
                return None
                
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return None

async def get_bot_data():
    """Получить данные бота"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}")

async def get_bot_categories():
    """Получить категории бота"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/categories")

async def get_bot_channels():
    """Получить каналы бота"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/channels")

async def get_user_category_subscriptions(telegram_id):
    """Получить подписки на категории"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/subscriptions")

async def get_user_channel_subscriptions(telegram_id):
    """Получить подписки на каналы"""
    return await api_request("GET", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/channel-subscriptions")

async def update_user_category_subscriptions(telegram_id, category_ids):
    """Обновить подписки на категории"""
    return await api_request("POST", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/subscriptions", 
                           {"category_ids": category_ids})

async def update_user_channel_subscriptions(telegram_id, channel_ids):
    """Обновить подписки на каналы"""
    return await api_request("POST", f"/api/public-bots/{BOT_ID}/users/{telegram_id}/channel-subscriptions", 
                           {"channel_ids": channel_ids})

async def get_filtered_posts(subscribed_channel_ids, subscribed_categories, max_posts):
    """🎯 ДВОЙНАЯ ФИЛЬТРАЦИЯ: каналы ∩ категории"""
    try:
        # Получаем посты с AI обработкой
        params = {
            "bot_id": BOT_ID,
            "limit": max_posts * 3,  # Берем больше для фильтрации
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
                logger.warning(f"Не найдено поле с постами. Ключи: {response.keys()}")
                return []
        else:
            posts_data = response

        if not isinstance(posts_data, list):
            logger.error(f"Неожиданная структура: {type(posts_data)}")
            return []

        filtered_posts = []
        
        for post in posts_data:
            # Парсим пост если строка
            if isinstance(post, str):
                try:
                    post = json.loads(post)
                except:
                    continue
            
            if not isinstance(post, dict):
                continue
            
            # ФИЛЬТР 1: Пост из подписанного канала?
            channel_telegram_id = post.get('channel_telegram_id')
            if not channel_telegram_id or channel_telegram_id not in subscribed_channel_ids:
                continue
            
            # ФИЛЬТР 2: Категория поста подписанная?
            ai_categories = post.get('ai_categories')
            if ai_categories:
                if isinstance(ai_categories, str):
                    try:
                        ai_categories = json.loads(ai_categories)
                    except:
                        continue
                
                post_category = None
                if isinstance(ai_categories, dict):
                    post_category = ai_categories.get('category') or ai_categories.get('categories')
                
                # ПОСТ ПРОШЕЛ ОБА ФИЛЬТРА
                if post_category and post_category in subscribed_categories:
                    ai_summaries = post.get('ai_summaries', {})
                    if isinstance(ai_summaries, str):
                        try:
                            ai_summaries = json.loads(ai_summaries)
                        except:
                            ai_summaries = {}
                    
                    summary = ai_summaries.get('summary', 'Описание недоступно')
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
                    
                    if len(filtered_posts) >= max_posts:
                        break
        
        return filtered_posts
        
    except Exception as e:
        logger.error(f"Ошибка при фильтрации постов: {e}")
        return []

async def ensure_auto_subscription(telegram_id):
    """Автоподписка на все категории и каналы"""
    try:
        bot_categories = await get_bot_categories()
        bot_channels = await get_bot_channels()
        
        if not bot_categories or not bot_channels:
            return False
        
        # Получаем текущие подписки
        user_category_subs = await get_user_category_subscriptions(telegram_id)
        user_channel_subs = await get_user_channel_subscriptions(telegram_id)
        
        # ID подписанных
        subscribed_category_ids = []
        if user_category_subs and 'subscribed_categories' in user_category_subs:
            subscribed_category_ids = [cat['id'] for cat in user_category_subs['subscribed_categories']]
        
        subscribed_channel_ids = []
        if user_channel_subs and 'subscribed_channels' in user_channel_subs:
            subscribed_channel_ids = [ch['id'] for ch in user_channel_subs['subscribed_channels']]
        
        # ID всех доступных
        all_category_ids = [cat['id'] for cat in bot_categories]
        all_channel_ids = [ch['id'] for ch in bot_channels]
        
        # Обновляем если нужно
        if set(subscribed_category_ids) != set(all_category_ids):
            logger.info(f"Автоподписка на категории для {telegram_id}")
            await update_user_category_subscriptions(telegram_id, all_category_ids)
        
        if set(subscribed_channel_ids) != set(all_channel_ids):
            logger.info(f"Автоподписка на каналы для {telegram_id}")
            await update_user_channel_subscriptions(telegram_id, all_channel_ids)
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка автоподписки: {e}")
        return False

# =============================================================================
# UI КОМПОНЕНТЫ
# =============================================================================

def get_main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [
            InlineKeyboardButton("📁 Категории", callback_data="categories"),
            InlineKeyboardButton("📺 Каналы", callback_data="channels")
        ],
        [
            InlineKeyboardButton("🎯 Подписки", callback_data="subscriptions"),
            InlineKeyboardButton("📰 Дайджест", callback_data="digest")
        ],
        [
            InlineKeyboardButton("❓ Справка", callback_data="help"),
            InlineKeyboardButton("🔧 Настройки", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_categories_keyboard(telegram_id):
    """Клавиатура категорий"""
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
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(keyboard)

async def get_channels_keyboard(telegram_id):
    """Клавиатура каналов"""
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
        title = ch.get('title', ch.get('channel_name', 'Канал'))
        text = f"{status} {title}"
        callback_data = f"toggle_channel_{ch['id']}"
        keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(keyboard)

# =============================================================================
# КОМАНДЫ
# =============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    # Автоподписка
    await ensure_auto_subscription(user.id)
    
    welcome_text = f"""
🤖 **Привет, {user.first_name}!**

Персонализированные новостные дайджесты с умной фильтрацией.

**🎯 Как работает двойная фильтрация:**
1️⃣ Выбираете интересные **каналы-источники**
2️⃣ Выбираете интересные **категории тем**
3️⃣ Получаете посты из выбранных каналов по выбранным темам

**📱 Управление через меню или команды:**
/categories - категории тем
/channels - каналы-источники
/digest - получить дайджест
/help - подробная справка
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /digest"""
    user_id = update.effective_user.id
    
    loading_msg = await update.effective_message.reply_text("🔍 Формирую дайджест...")
    
    try:
        # Получаем настройки бота
        bot_data = await get_bot_data()
        max_posts = bot_data.get('max_posts_per_digest', 10) if bot_data else 10
        
        # Получаем подписки
        category_subs = await get_user_category_subscriptions(user_id)
        channel_subs = await get_user_channel_subscriptions(user_id)
        
        if not category_subs or not channel_subs:
            await loading_msg.edit_text(
                "❌ Не удалось загрузить подписки.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Извлекаем подписанные данные
        subscribed_categories = [cat['name'] for cat in category_subs.get('subscribed_categories', [])]
        subscribed_channel_ids = [ch['telegram_id'] for ch in channel_subs.get('subscribed_channels', [])]
        
        if not subscribed_categories or not subscribed_channel_ids:
            await loading_msg.edit_text(
                "⚠️ Нет активных подписок.\n\n"
                "Подпишитесь на категории и каналы для дайджеста.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # ДВОЙНАЯ ФИЛЬТРАЦИЯ
        posts = await get_filtered_posts(subscribed_channel_ids, subscribed_categories, max_posts)
        
        if not posts:
            await loading_msg.edit_text(
                "📭 **Дайджест пуст**\n\n"
                f"По подпискам ({len(subscribed_categories)} категорий, {len(subscribed_channel_ids)} каналов) "
                "релевантных постов не найдено.\n\n"
                "💡 Попробуйте расширить подписки",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Формируем дайджест
        digest_text = f"📰 **ПЕРСОНАЛЬНЫЙ ДАЙДЖЕСТ**\n"
        digest_text += f"🎯 {len(subscribed_categories)} категорий • {len(subscribed_channel_ids)} каналов\n"
        digest_text += f"📊 Найдено {len(posts)} постов\n\n"
        
        # Группируем по категориям
        posts_by_category = {}
        for post in posts:
            category = post['ai_category']
            if category not in posts_by_category:
                posts_by_category[category] = []
            posts_by_category[category].append(post)
        
        # Выводим по категориям
        for category, category_posts in posts_by_category.items():
            digest_text += f"**📁 {category.upper()}**\n"
            for i, post in enumerate(category_posts, 1):
                digest_text += f"{i}. {post['ai_summary']} <a href='{post['post_url']}'>🔗</a>\n"
            digest_text += "\n"
        
        digest_text += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        await loading_msg.edit_text(
            digest_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard(),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка дайджеста: {e}")
        await loading_msg.edit_text(
            "❌ Ошибка при формировании дайджеста.",
            reply_markup=get_main_menu_keyboard()
        )

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /categories"""
    user_id = update.effective_user.id
    keyboard = await get_categories_keyboard(user_id)
    
    if not keyboard:
        await update.effective_message.reply_text(
            "❌ Не удалось загрузить категории.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await update.effective_message.reply_text(
        "📁 **КАТЕГОРИИ ТЕМ**\n\n"
        "Выберите категории новостей:\n"
        "✅ - подписан • ⭕ - не подписан",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /channels"""
    user_id = update.effective_user.id
    keyboard = await get_channels_keyboard(user_id)
    
    if not keyboard:
        await update.effective_message.reply_text(
            "❌ Не удалось загрузить каналы.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await update.effective_message.reply_text(
        "📺 **КАНАЛЫ-ИСТОЧНИКИ**\n\n"
        "Выберите каналы новостей:\n"
        "✅ - подписан • ⭕ - не подписан",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

async def subscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /subscriptions"""
    user_id = update.effective_user.id
    
    try:
        # Получаем подписки
        category_subs = await get_user_category_subscriptions(user_id)
        channel_subs = await get_user_channel_subscriptions(user_id)
        
        subscribed_categories = []
        if category_subs and 'subscribed_categories' in category_subs:
            subscribed_categories = [cat['name'] for cat in category_subs['subscribed_categories']]
        
        subscribed_channels = []
        if channel_subs and 'subscribed_channels' in channel_subs:
            subscribed_channels = [ch.get('title', ch.get('channel_name', 'Канал')) for ch in channel_subs['subscribed_channels']]
        
        subs_text = f"🎯 **ВАШИ ПОДПИСКИ**\n\n"
        subs_text += f"📁 **Категории ({len(subscribed_categories)}):**\n"
        for cat in subscribed_categories:
            subs_text += f"✅ {cat}\n"
        
        subs_text += f"\n📺 **Каналы ({len(subscribed_channels)}):**\n"
        for ch in subscribed_channels:
            subs_text += f"✅ {ch}\n"
        
        subs_text += f"\n💡 **Логика фильтрации:**\n"
        subs_text += f"Дайджест = посты из {len(subscribed_channels)} каналов по {len(subscribed_categories)} категориям"
        
        await update.effective_message.reply_text(
            subs_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка подписок: {e}")
        await update.effective_message.reply_text(
            "❌ Ошибка при загрузке подписок.",
            reply_markup=get_main_menu_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📖 **СПРАВКА**

**🎯 Логика двойной фильтрации:**
Дайджест = (посты из подписанных каналов) ∩ (посты подписанных категорий)

1️⃣ **Каналы-источники** - откуда брать посты
2️⃣ **Категории тем** - какие темы интересны
3️⃣ **Результат** - пересечение: посты из выбранных каналов по выбранным темам

**📱 Команды:**
/start - главное меню
/categories - управление категориями
/channels - управление каналами
/digest - получить дайджест
/subscriptions - просмотр подписок
/help - эта справка

**💡 Пример:**
Подписаны на каналы: CNN, BBC
Подписаны на категории: Технологии, Наука
Результат: технологические и научные новости только из CNN и BBC
"""
    
    await update.effective_message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )

# =============================================================================
# ОБРАБОТЧИК КНОПОК
# =============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        if data == "back_menu":
            await query.edit_message_text(
                "🏠 **ГЛАВНОЕ МЕНЮ**\n\nВыберите действие:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard()
            )
        
        elif data == "categories":
            keyboard = await get_categories_keyboard(user_id)
            if keyboard:
                await query.edit_message_text(
                    "📁 **КАТЕГОРИИ ТЕМ**\n\n"
                    "Выберите категории:\n"
                    "✅ - подписан • ⭕ - не подписан",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        
        elif data == "channels":
            keyboard = await get_channels_keyboard(user_id)
            if keyboard:
                await query.edit_message_text(
                    "📺 **КАНАЛЫ-ИСТОЧНИКИ**\n\n"
                    "Выберите каналы:\n"
                    "✅ - подписан • ⭕ - не подписан",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        
        elif data == "digest":
            temp_update = Update(update_id=0, message=query.message)
            temp_update.effective_message = query.message
            temp_update.effective_user = query.from_user
            await digest_command(temp_update, None)
        
        elif data == "subscriptions":
            temp_update = Update(update_id=0, message=query.message)
            temp_update.effective_message = query.message
            temp_update.effective_user = query.from_user
            await subscriptions_command(temp_update, None)
        
        elif data == "help":
            temp_update = Update(update_id=0, message=query.message)
            temp_update.effective_message = query.message
            temp_update.effective_user = query.from_user
            await help_command(temp_update, None)
        
        elif data == "settings":
            await query.edit_message_text(
                "🔧 **НАСТРОЙКИ**\n\n"
                "Настройки управляются через админ-панель.\n"
                "Персональные настройки будут добавлены в следующих версиях!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_menu")]])
            )
        
        elif data.startswith("toggle_category_"):
            category_id = int(data.split("_")[-1])
            await toggle_category(query, user_id, category_id)
            
        elif data.startswith("toggle_channel_"):
            channel_id = int(data.split("_")[-1])
            await toggle_channel(query, user_id, channel_id)
            
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")
        await query.edit_message_text(
            "❌ Ошибка. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard()
        )

async def toggle_category(query, user_id, category_id):
    """Переключить подписку на категорию"""
    try:
        current_subs = await get_user_category_subscriptions(user_id)
        subscribed_ids = []
        
        if current_subs and 'subscribed_categories' in current_subs:
            subscribed_ids = [cat['id'] for cat in current_subs['subscribed_categories']]
        
        if category_id in subscribed_ids:
            subscribed_ids.remove(category_id)
        else:
            subscribed_ids.append(category_id)
        
        result = await update_user_category_subscriptions(user_id, subscribed_ids)
        
        if result:
            keyboard = await get_categories_keyboard(user_id)
            await query.edit_message_reply_markup(reply_markup=keyboard)
        else:
            await query.answer("❌ Ошибка обновления", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка toggle_category: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)

async def toggle_channel(query, user_id, channel_id):
    """Переключить подписку на канал"""
    try:
        current_subs = await get_user_channel_subscriptions(user_id)
        subscribed_ids = []
        
        if current_subs and 'subscribed_channels' in current_subs:
            subscribed_ids = [ch['id'] for ch in current_subs['subscribed_channels']]
        
        if channel_id in subscribed_ids:
            subscribed_ids.remove(channel_id)
        else:
            subscribed_ids.append(channel_id)
        
        result = await update_user_channel_subscriptions(user_id, subscribed_ids)
        
        if result:
            keyboard = await get_channels_keyboard(user_id)
            await query.edit_message_reply_markup(reply_markup=keyboard)
        else:
            await query.answer("❌ Ошибка обновления", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка toggle_channel: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)

# =============================================================================
# НАСТРОЙКА КОМАНД МЕНЮ
# =============================================================================

async def setup_bot_commands(application):
    """Настройка команд для меню Telegram"""
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("categories", "📁 Категории тем"),
        BotCommand("channels", "📺 Каналы-источники"),
        BotCommand("digest", "📰 Получить дайджест"),
        BotCommand("subscriptions", "🎯 Мои подписки"),
        BotCommand("help", "❓ Справка"),
    ]
    
    await application.bot.set_my_commands(commands)
    logger.info("Команды меню настроены")

# =============================================================================
# ЗАПУСК
# =============================================================================

async def main():
    """Запуск бота"""
    print("🚀 Запуск основной функции...")
    logger.info("🚀 Запуск Telegram Bot v3.0 - Правильная двойная фильтрация")
    
    # Проверяем Backend API
    bot_data = await get_bot_data()
    if not bot_data:
        logger.error("❌ Нет подключения к Backend API")
        print("❌ Нет подключения к Backend API")
        return
    
    logger.info(f"✅ Backend API подключен. Бот: {bot_data.get('name')}")
    print(f"✅ Backend API подключен. Бот: {bot_data.get('name')}")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем команды
    await setup_bot_commands(application)
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("channels", channels_command))
    application.add_handler(CommandHandler("digest", digest_command))
    application.add_handler(CommandHandler("subscriptions", subscriptions_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик неизвестных сообщений
    async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤔 Используйте меню или команды /help",
            reply_markup=get_main_menu_keyboard()
        )
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_handler))
    
    logger.info("✅ Бот запущен и готов!")
    print("✅ Бот запущен и готов!")
    
    # Запускаем бота
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import platform
    
    print(f"💻 Платформа: {platform.system()}")
    
    # Устанавливаем правильную политику event loop для Windows  
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("🔧 Установлена WindowsProactorEventLoopPolicy")
    
    try:
        print("🔄 Запуск asyncio.run(main())...")
        asyncio.run(main())
        print("✅ Программа завершена успешно")
    except KeyboardInterrupt:
        print("🛑 Программа остановлена пользователем")
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc() 