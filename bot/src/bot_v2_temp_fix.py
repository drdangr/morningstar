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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Конфигурация
BACKEND_URL = "http://127.0.0.1:8000"
PUBLIC_BOT_ID = 4
BOT_TOKEN = "8124620179:AAHNt4-7ZFg-zz0Cr6mJX483jDuNeARpIdE"

# 🔧 ЛОКАЛЬНОЕ ХРАНЕНИЕ ПОДПИСОК (временное решение)
user_subscriptions = {}  # {user_id: [category_ids]}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
                    return data
                else:
                    logger.error(f"Ошибка получения AI постов: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка запроса AI постов: {e}")
        return []

def save_user_subscriptions(user_id, category_ids):
    """Сохранить подписки пользователя (локально)"""
    user_subscriptions[user_id] = category_ids
    logger.info(f"💾 Локально сохранены подписки пользователя {user_id}: {category_ids}")

def get_user_subscriptions(user_id):
    """Получить подписки пользователя (локально)"""
    return user_subscriptions.get(user_id, [])

def filter_posts_by_subscriptions(posts, subscribed_categories):
    """Фильтровать посты по подпискам"""
    if not subscribed_categories:
        return []
    
    filtered_posts = []
    for post in posts:
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
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я MorningStar Bot (v2) - ваш персональный дайджест Telegram каналов.\n\n"
        f"🚀 Новая версия с поддержкой:\n"
        f"• 🤖 AI-категоризация и саммаризация постов\n"
        f"• 🎯 Мультитенантность (bot_id: {PUBLIC_BOT_ID})\n"
        f"• 📊 Умные метрики (важность, срочность, значимость)\n"
        f"• 🎪 Персональные дайджесты по подпискам\n\n"
        f"⚡ Временное решение: локальное хранение подписок\n\n"
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

💡 <b>Особенности v2:</b>
• Использует endpoint /api/posts/cache-with-ai?bot_id=4
• Локальное хранение подписок (временно)
• Фильтрация постов по AI категориям
• Умная сортировка по метрикам
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
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎯 <b>Управление подписками для бота {PUBLIC_BOT_ID}</b>\n\n"
    text += f"📊 Текущие подписки: {len(current_subscriptions)}\n\n"
    text += "Выберите категории для подписки:"
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("toggle_"):
        category_id = int(data.split("_")[1])
        current_subscriptions = get_user_subscriptions(user_id)
        
        if category_id in current_subscriptions:
            current_subscriptions.remove(category_id)
        else:
            current_subscriptions.append(category_id)
        
        save_user_subscriptions(user_id, current_subscriptions)
        
        # Обновляем сообщение
        await subscribe_command(update, context)
        
    elif data == "save_subscriptions":
        current_subscriptions = get_user_subscriptions(user_id)
        await query.edit_message_text(
            f"✅ Подписки для бота {PUBLIC_BOT_ID} сохранены!\n\n"
            f"Подписки обновлены. Выбрано категорий: {len(current_subscriptions)}\n\n"
            f"Теперь вы будете получать персональные дайджесты по выбранным категориям."
        )

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Получить персональный дайджест"""
    user_id = update.effective_user.id
    subscribed_category_ids = get_user_subscriptions(user_id)
    
    if not subscribed_category_ids:
        await update.message.reply_text(
            f"📭 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            f"Используйте команду /subscribe для выбора интересующих категорий, "
            f"а затем повторите запрос дайджеста."
        )
        return
    
    # Получаем категории для понимания названий
    categories = await get_bot_categories()
    category_names = {cat['id']: cat['name'] for cat in categories}
    subscribed_names = [category_names.get(cat_id, f"Категория {cat_id}") for cat_id in subscribed_category_ids]
    
    # Получаем AI посты
    posts = await get_ai_posts(limit=20)
    
    if not posts:
        await update.message.reply_text("❌ Не удалось получить посты. Попробуйте позже.")
        return
    
    # Фильтруем посты по подпискам
    filtered_posts = filter_posts_by_subscriptions(posts, subscribed_names)
    
    if not filtered_posts:
        await update.message.reply_text(
            f"📭 Нет новых постов по вашим подпискам.\n\n"
            f"🎯 Ваши подписки: {', '.join(subscribed_names)}\n\n"
            f"Попробуйте позже или измените подписки командой /subscribe."
        )
        return
    
    # Сортируем посты по метрикам (важность×3 + срочность×2 + значимость×2)
    def calculate_score(post):
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        return importance * 3 + urgency * 2 + significance * 2
    
    filtered_posts.sort(key=calculate_score, reverse=True)
    
    # Ограничиваем количество постов
    max_posts = 10
    filtered_posts = filtered_posts[:max_posts]
    
    # Формируем дайджест
    text = f"📰 <b>Персональный дайджест</b>\n"
    text += f"🎯 Подписки: {', '.join(subscribed_names)}\n"
    text += f"📊 Найдено постов: {len(filtered_posts)}\n\n"
    
    for i, post in enumerate(filtered_posts, 1):
        title = post.get('title', 'Без заголовка')[:50]
        ai_summary = post.get('ai_summary', 'Нет описания')[:100]
        ai_category = post.get('ai_category', 'Нет категории')
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        
        text += f"<b>{i}. {title}</b>\n"
        text += f"📝 {ai_summary}\n"
        text += f"🏷️ {ai_category}\n"
        text += f"📊 Важность: {importance:.1f}, Срочность: {urgency:.1f}, Значимость: {significance:.1f}\n\n"
    
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
        title = post.get('title', 'Без заголовка')[:30]
        ai_category = post.get('ai_category', 'Нет категории')
        importance = post.get('ai_importance', 0)
        urgency = post.get('ai_urgency', 0)
        significance = post.get('ai_significance', 0)
        
        text += f"<b>{i}. {title}</b>\n"
        text += f"🏷️ {ai_category}\n"
        text += f"📊 {importance:.1f}/{urgency:.1f}/{significance:.1f}\n\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отладочная информация"""
    user_id = update.effective_user.id
    subscriptions = get_user_subscriptions(user_id)
    
    text = f"🔧 <b>Отладочная информация</b>\n\n"
    text += f"👤 User ID: {user_id}\n"
    text += f"🤖 Bot ID: {PUBLIC_BOT_ID}\n"
    text += f"🔗 Backend URL: {BACKEND_URL}\n"
    text += f"📊 Локальные подписки: {subscriptions}\n"
    text += f"📝 Всего пользователей в памяти: {len(user_subscriptions)}\n\n"
    text += f"⚡ Режим: Локальное хранение подписок\n"
    text += f"🎯 Endpoint: /api/posts/cache-with-ai?bot_id={PUBLIC_BOT_ID}"
    
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
    print(f"🚀 Запуск MorningStar Bot v2 (Временное решение)")
    print(f"🤖 Bot ID: {PUBLIC_BOT_ID}")
    print(f"💾 Режим: Локальное хранение подписок")
    
    application.run_polling()

if __name__ == '__main__':
    main() 