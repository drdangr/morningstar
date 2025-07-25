#!/usr/bin/env python3
"""
🤖 MorningStar Bot v2 - ИСПРАВЛЕННАЯ ВЕРСИЯ с мультитенантными endpoints

ИСПРАВЛЕНИЯ:
- Использует новые мультитенантные endpoints:
  * GET /api/public-bots/{bot_id}/users/{user_id}/subscriptions
  * POST /api/public-bots/{bot_id}/users/{user_id}/subscriptions
- Подписки сохраняются в БД с привязкой к bot_id
- Полная интеграция с Backend API
"""
import asyncio
import json
import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Конфигурация
BACKEND_URL = "http://127.0.0.1:8000"
PUBLIC_BOT_ID = 4
BOT_TOKEN = "8124620179:AAHNt4-7ZFg-zz0Cr6mJX483jDuNeARpIdE"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def create_or_update_user(telegram_id, username, first_name, last_name=None):
    """Создать или обновить пользователя"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/users"
            payload = {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "language_code": "ru",
                "is_active": True
            }
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    logger.info(f"✅ Пользователь {telegram_id} создан/обновлен")
                    return data
                else:
                    logger.error(f"Ошибка создания пользователя: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка запроса создания пользователя: {e}")
        return None

async def get_user_subscriptions(telegram_id):
    """Получить подписки пользователя для бота (мультитенантные)"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}/users/{telegram_id}/subscriptions"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Получены подписки пользователя {telegram_id}: {len(data)} категорий")
                    return data
                elif response.status == 404:
                    logger.info(f"📭 Пользователь {telegram_id} не имеет подписок для бота {PUBLIC_BOT_ID}")
                    return []
                else:
                    logger.error(f"Ошибка получения подписок: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка запроса подписок: {e}")
        return []

async def update_user_subscriptions(telegram_id, category_ids):
    """Обновить подписки пользователя для бота (мультитенантные)"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}/users/{telegram_id}/subscriptions"
            payload = {"category_ids": category_ids}
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Подписки пользователя {telegram_id} обновлены: {len(category_ids)} категорий")
                    return data
                else:
                    logger.error(f"Ошибка обновления подписок: {response.status}")
                    text = await response.text()
                    logger.error(f"Ответ сервера: {text}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка запроса обновления подписок: {e}")
        return None

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
                    
                    # 🔧 ИСПРАВЛЕНО: Правильно извлекаем посты из структуры API
                    if isinstance(data, dict) and 'posts' in data:
                        posts = data['posts']
                        logger.info(f"Получено {len(posts)} AI-обработанных постов")
                        return posts
                    else:
                        logger.error(f"Неправильная структура API ответа: {data}")
                        return []
                else:
                    logger.error(f"Ошибка получения AI постов: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка запроса AI постов: {e}")
        return []

async def get_bot_settings():
    """Получить настройки бота"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Ошибка получения настроек бота: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка запроса настроек бота: {e}")
        return None

def filter_posts_by_subscriptions(posts, subscribed_categories):
    """Фильтровать посты по подпискам"""
    if not subscribed_categories:
        return []
    
    filtered_posts = []
    for post in posts:
        # 🔧 ИСПРАВЛЕНО: Безопасная обработка None значений
        ai_category = str(post.get('ai_category') or '').strip()
        if ai_category:
            # Проверяем, содержит ли AI категория одну из подписанных категорий
            for sub_cat in subscribed_categories:
                cat_name = str(sub_cat.get('name') or '').strip()
                if cat_name and cat_name.lower() in ai_category.lower():
                    filtered_posts.append(post)
                    break
    
    return filtered_posts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем или обновляем пользователя в БД
    await create_or_update_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я MorningStar Bot (v2) - ваш персональный дайджест Telegram каналов.\n\n"
        f"🚀 Новая версия с поддержкой:\n"
        f"• 🤖 AI-категоризация и саммаризация постов\n"
        f"• 🎯 Мультитенантность (bot_id: {PUBLIC_BOT_ID})\n"
        f"• 📊 Умные метрики (важность, срочность, значимость)\n"
        f"• 🎪 Персональные дайджесты по подпискам\n\n"
        f"✅ Исправленная версия: подписки в БД\n\n"
        f"Используйте /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
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

✅ <b>Исправления v2:</b>
• Мультитенантные endpoints Backend API
• Подписки сохраняются в БД (user_category_subscriptions)
• Привязка к bot_id для изоляции данных
• Полная интеграция с Backend API
• Управление количеством постов через настройки бота
"""
    await update.message.reply_text(help_text, parse_mode='HTML')

async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать доступные категории"""
    categories = await get_bot_categories()
    
    if not categories:
        await update.message.reply_text("❌ Не удалось получить категории. Попробуйте позже.")
        return
    
    text = f"📁 <b>Доступные категории для бота {PUBLIC_BOT_ID}:</b>\n\n"
    for cat in categories:
        status = "✅" if cat['is_active'] else "❌"
        text += f"{status} <b>{cat['name']}</b> (ID: {cat['id']})\n"
        if cat['description']:
            text += f"   📝 {cat['description']}\n"
        text += "\n"
    
    text += f"💡 Всего категорий: {len(categories)}"
    await update.message.reply_text(text, parse_mode='HTML')

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Управление подписками"""
    user_id = update.effective_user.id
    categories = await get_bot_categories()
    
    if not categories:
        await update.message.reply_text("❌ Не удалось получить категории.")
        return
    
    current_subscriptions = await get_user_subscriptions(user_id)
    current_subscription_ids = [sub.get('id') for sub in current_subscriptions]
    
    # Создаем inline клавиатуру
    keyboard = []
    for cat in categories:
        if cat['is_active']:
            is_subscribed = cat['id'] in current_subscription_ids
            emoji = "✅" if is_subscribed else "⬜"
            text = f"{emoji} {cat['name']}"
            callback_data = f"toggle_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎯 <b>Управление подписками для бота {PUBLIC_BOT_ID}</b>\n\n"
    text += f"📊 Текущие подписки: {len(current_subscriptions)}\n\n"
    text += "Выберите категории для подписки:"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

# Временная переменная для хранения изменений до сохранения
temp_subscription_changes = {}

async def update_subscription_keyboard(query, user_id):
    """Обновить inline клавиатуру с подписками"""
    categories = await get_bot_categories()
    
    if not categories:
        await query.edit_message_text("❌ Не удалось получить категории.")
        return
    
    # Получаем текущее состояние подписок
    if user_id in temp_subscription_changes:
        current_subscription_ids = temp_subscription_changes[user_id]
    else:
        current_subscriptions = await get_user_subscriptions(user_id)
        current_subscription_ids = [sub.get('id') for sub in current_subscriptions]
        temp_subscription_changes[user_id] = current_subscription_ids
    
    # Создаем inline клавиатуру
    keyboard = []
    for cat in categories:
        if cat['is_active']:
            is_subscribed = cat['id'] in current_subscription_ids
            emoji = "✅" if is_subscribed else "⬜"
            text = f"{emoji} {cat['name']}"
            callback_data = f"toggle_{cat['id']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("💾 Сохранить", callback_data="save_subscriptions")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎯 <b>Управление подписками для бота {PUBLIC_BOT_ID}</b>\n\n"
    text += f"📊 Выбрано категорий: {len(current_subscription_ids)}\n\n"
    text += "Выберите категории для подписки:"
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("toggle_"):
        category_id = int(data.split("_")[1])
        
        # Получаем текущие подписки из БД
        if user_id not in temp_subscription_changes:
            current_subscriptions = await get_user_subscriptions(user_id)
            temp_subscription_changes[user_id] = [sub.get('id') for sub in current_subscriptions]
        
        # Переключаем подписку
        if category_id in temp_subscription_changes[user_id]:
            temp_subscription_changes[user_id].remove(category_id)
        else:
            temp_subscription_changes[user_id].append(category_id)
        
        # Обновляем inline клавиатуру
        await update_subscription_keyboard(query, user_id)
        
    elif data == "save_subscriptions":
        if user_id in temp_subscription_changes:
            category_ids = temp_subscription_changes[user_id]
        else:
            current_subscriptions = await get_user_subscriptions(user_id)
            category_ids = [sub.get('id') for sub in current_subscriptions]
        
        # Сохраняем в БД
        result = await update_user_subscriptions(user_id, category_ids)
        
        if result:
            await query.edit_message_text(
                f"✅ Подписки для бота {PUBLIC_BOT_ID} сохранены!\n\n"
                f"Подписки обновлены. Выбрано категорий: {len(category_ids)}\n\n"
                f"Теперь вы будете получать персональные дайджесты по выбранным категориям."
            )
            # Очищаем временные изменения
            if user_id in temp_subscription_changes:
                del temp_subscription_changes[user_id]
        else:
            await query.edit_message_text(
                f"❌ Ошибка сохранения подписок!\n\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получить персональный дайджест"""
    user_id = update.effective_user.id
    subscribed_categories = await get_user_subscriptions(user_id)
    
    if not subscribed_categories:
        await update.message.reply_text(
            f"📭 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            f"Используйте команду /subscribe для выбора интересующих категорий, "
            f"а затем повторите запрос дайджеста."
        )
        return
    
    # 🔧 ИСПРАВЛЕНО: Безопасная обработка None значений
    subscribed_names = [str(cat.get('name') or f"Категория {cat.get('id')}") for cat in subscribed_categories]
    
    # Получаем AI посты с увеличенным лимитом (чтобы после фильтрации осталось достаточно)
    posts = await get_ai_posts(limit=50)
    
    if not posts:
        await update.message.reply_text("❌ Не удалось получить посты. Попробуйте позже.")
        return
    
    # Фильтруем посты по подпискам
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_categories)
    
    if not filtered_posts:
        await update.message.reply_text(
            f"📭 Нет новых постов по вашим подпискам.\n\n"
            f"🎯 Ваши подписки: {', '.join(subscribed_names)}\n\n"
            f"Попробуйте позже или измените подписки командой /subscribe."
        )
        return
    
    # Сортируем посты по метрикам (важность×3 + срочность×2 + значимость×2)
    def calculate_score(post):
        # 🔧 ИСПРАВЛЕНО: Безопасная обработка None значений
        importance = float(post.get('ai_importance') or 0)
        urgency = float(post.get('ai_urgency') or 0)
        significance = float(post.get('ai_significance') or 0)
        return importance * 3 + urgency * 2 + significance * 2
    
    filtered_posts.sort(key=calculate_score, reverse=True)
    
    # Получаем настройки бота для лимита постов
    bot_settings = await get_bot_settings()
    max_posts = bot_settings.get('max_posts_per_digest', 10) if bot_settings else 10
    
    # Ограничиваем количество постов настройкой бота
    filtered_posts = filtered_posts[:max_posts]
    
    # Группируем посты по категориям
    posts_by_category = {}
    for post in filtered_posts:
        category = str(post.get('ai_category') or 'Нет категории')
        if category not in posts_by_category:
            posts_by_category[category] = []
        posts_by_category[category].append(post)
    
    # Формируем компактный дайджест
    text = f"📰 <b>Персональный дайджест</b>\n"
    text += f"🎯 Подписки: {', '.join(subscribed_names)}\n"
    text += f"📊 Найдено постов: {len(filtered_posts)}"
    if max_posts < len(filtered_posts):
        text += f" (показаны лучшие {max_posts})"
    text += f"\n\n"
    
    for category, posts in posts_by_category.items():
        text += f"<b>{category.upper()}</b>\n"
        
        for i, post in enumerate(posts, 1):
            # 🔧 ИСПРАВЛЕНО: Безопасная обработка None значений
            ai_summary = str(post.get('ai_summary') or 'Нет описания')
            
            # Получаем ссылку на пост
            media_urls = post.get('media_urls', [])
            if media_urls and isinstance(media_urls, list) and len(media_urls) > 0:
                post_url = media_urls[0]
                text += f"{i}. {ai_summary} <a href='{post_url}'>🔗</a>\n"
            else:
                text += f"{i}. {ai_summary}\n"
        
        text += "\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Тестовая команда для отладки"""
    posts = await get_ai_posts(limit=10)
    
    if not posts:
        await update.message.reply_text("❌ Не удалось получить тестовые посты.")
        return
    
    text = f"🧪 <b>Тест AI постов (bot_id: {PUBLIC_BOT_ID})</b>\n\n"
    text += f"📊 Получено постов: {len(posts)}\n\n"
    
    for i, post in enumerate(posts[:5], 1):
        # 🔧 ИСПРАВЛЕНО: Безопасная обработка None значений
        ai_category = str(post.get('ai_category') or 'Нет категории')
        importance = float(post.get('ai_importance') or 0)
        urgency = float(post.get('ai_urgency') or 0)
        significance = float(post.get('ai_significance') or 0)
        
        text += f"<b>{i}.</b>\n"
        text += f"🏷️ {ai_category}\n"
        text += f"📊 {importance:.1f}/{urgency:.1f}/{significance:.1f}\n\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отладочная информация"""
    user_id = update.effective_user.id
    subscriptions = await get_user_subscriptions(user_id)
    bot_settings = await get_bot_settings()
    
    text = f"🔧 <b>Отладочная информация</b>\n\n"
    text += f"👤 User ID: {user_id}\n"
    text += f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
    text += f"🔗 Backend URL: {BACKEND_URL}\n"
    text += f"📊 Подписки в БД: {len(subscriptions)}\n"
    for sub in subscriptions:
        text += f"   - {sub.get('name', 'Без имени')} (ID: {sub.get('id')})\n"
    
    # Настройки бота
    if bot_settings:
        max_posts = bot_settings.get('max_posts_per_digest', 10)
        text += f"\n⚙️ Настройки бота:\n"
        text += f"   - Максимум постов в дайджесте: {max_posts}\n"
        text += f"   - Статус бота: {bot_settings.get('status', 'unknown')}\n"
        text += f"   - Всего каналов: {bot_settings.get('channels_count', 0)}\n"
        text += f"   - Всего категорий: {bot_settings.get('topics_count', 0)}\n"
    
    text += f"\n✅ Режим: Мультитенантные endpoints\n"
    text += f"🎯 Endpoints:\n"
    text += f"   - GET /api/public-bots/{PUBLIC_BOT_ID}/users/{user_id}/subscriptions\n"
    text += f"   - POST /api/public-bots/{PUBLIC_BOT_ID}/users/{user_id}/subscriptions"
    
    await update.message.reply_text(text, parse_mode='HTML')

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
    print(f"🚀 Запуск MorningStar Bot v2 (Исправленная версия)")
    print(f"🤖 Bot ID: {PUBLIC_BOT_ID}")
    print(f"💾 Режим: Мультитенантные endpoints Backend API")
    print(f"✅ Подписки сохраняются в БД: user_category_subscriptions")
    
    application.run_polling()

if __name__ == '__main__':
    main() 