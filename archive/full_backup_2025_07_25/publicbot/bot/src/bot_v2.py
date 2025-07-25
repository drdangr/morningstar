#!/usr/bin/env python3
"""
MorningStar Bot v2 - Мультитенантная версия с AI поддержкой
Использует endpoint /api/posts/cache-with-ai для получения обработанных постов
"""

import os
import logging
import aiohttp
import asyncio
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
PUBLIC_BOT_TOKEN = os.getenv('PUBLIC_BOT_TOKEN')
PUBLIC_BOT_ID = int(os.getenv('PUBLIC_BOT_ID', '4'))  # 🚀 ID бота для мультитенантности
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID') or os.getenv('ADMIN_CHAT_ID', '0'))
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')

# Проверяем обязательные настройки
if not PUBLIC_BOT_TOKEN:
    logger.error("PUBLIC_BOT_TOKEN не найден в переменных окружения!")
    exit(1)

if not PUBLIC_BOT_ID:
    logger.error("PUBLIC_BOT_ID не найден в переменных окружения!")
    exit(1)

logger.info(f"🤖 Запускаем бота для bot_id={PUBLIC_BOT_ID}")


async def check_backend_status():
    """Проверка статуса Backend API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/health", timeout=5) as response:
                if response.status == 200:
                    return "🟢 Работает"
                else:
                    return "🟡 Недоступен"
    except Exception as e:
        logger.error(f"Ошибка проверки Backend: {e}")
        return "🔴 Ошибка"


async def get_system_stats():
    """Получение статистики системы"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/stats", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        return None


async def create_or_update_user(telegram_user):
    """Создание или обновление пользователя в Backend API"""
    try:
        user_data = {
            "telegram_id": telegram_user.id,
            "username": telegram_user.username,
            "first_name": telegram_user.first_name,
            "last_name": telegram_user.last_name,
            "language_code": telegram_user.language_code or "ru",
            "is_active": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BACKEND_URL}/api/users", json=user_data, timeout=5) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    logger.error(f"Ошибка создания пользователя: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка API пользователя: {e}")
        return None


async def get_user_subscriptions(telegram_id):
    """Получение подписок пользователя для конкретного бота"""
    try:
        # 🚀 ИСПРАВЛЕНИЕ: добавляем bot_id параметр для мультитенантности
        url = f"{BACKEND_URL}/api/users/{telegram_id}/subscriptions?bot_id={PUBLIC_BOT_ID}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return []  # Пользователь не найден или нет подписок
                else:
                    logger.error(f"Ошибка получения подписок: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return None


async def update_user_subscriptions(telegram_id, category_ids):
    """Обновление подписок пользователя для конкретного бота"""
    try:
        # 🚀 ИСПРАВЛЕНИЕ: добавляем bot_id в payload для мультитенантности
        subscription_data = {
            "category_ids": category_ids,
            "bot_id": PUBLIC_BOT_ID
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/users/{telegram_id}/subscriptions", 
                json=subscription_data, 
                timeout=5
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка обновления подписок: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка API подписок: {e}")
        return None


async def get_categories():
    """Получение списка активных категорий"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/categories?active_only=true", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {e}")
        return None


async def get_bot_categories():
    """Получение категорий конкретного бота"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/public-bots/{PUBLIC_BOT_ID}/categories", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    # Фильтруем активные категории и преобразуем к нужному формату
                    categories = []
                    for cat in data:
                        if cat.get('is_active', True) and cat.get('category_name'):
                            categories.append({
                                'id': cat.get('category_id', cat.get('id')),
                                'name': cat.get('category_name'),
                                'description': cat.get('description', ''),
                                'emoji': '📝'  # Дефолтный emoji
                            })
                    return categories
                else:
                    logger.error(f"Ошибка получения категорий бота: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения категорий бота: {e}")
        return None


async def get_bot_posts_with_ai(limit=50):
    """
    🚀 НОВАЯ ФУНКЦИЯ: Получение AI-обработанных постов для конкретного бота
    Использует мультитенантный endpoint /api/posts/cache-with-ai
    """
    try:
        params = {
            'bot_id': PUBLIC_BOT_ID,  # 🚀 Мультитенантная фильтрация
            'ai_status': 'processed',  # Только обработанные AI постов
            'limit': limit,
            'sort_by': 'post_date',
            'sort_order': 'desc'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{BACKEND_URL}/api/posts/cache-with-ai?{query_string}"
        
        logger.info(f"🔍 Запрашиваем AI посты для бота {PUBLIC_BOT_ID}: {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get('posts', [])
                    logger.info(f"✅ Получено {len(posts)} AI-обработанных постов для бота {PUBLIC_BOT_ID}")
                    return posts
                else:
                    logger.error(f"❌ Ошибка получения AI постов: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ Ошибка API AI постов: {e}")
        return None


async def filter_posts_by_subscriptions(posts, subscribed_categories):
    """
    Фильтрует AI-обработанные посты по подпискам пользователя
    
    Args:
        posts: Список AI-обработанных постов из /api/posts/cache-with-ai
        subscribed_categories: Список подписанных категорий пользователя
    
    Returns:
        Отфильтрованные посты или None если нет релевантных постов
    """
    if not posts or not subscribed_categories:
        return None
    
    # Получаем названия подписанных категорий
    subscribed_names = {cat.get('name', '').lower() for cat in subscribed_categories}
    
    if not subscribed_names:
        return None
    
    filtered_posts = []
    
    logger.info(f"🎯 Фильтруем {len(posts)} постов по подпискам: {subscribed_names}")
    
    for post in posts:
        # 🚀 НОВОЕ: используем ai_category вместо устаревших полей
        ai_category = post.get('ai_category', '')
        
        if not ai_category or ai_category.lower() in ['null', 'none', '', 'нерелевантно']:
            continue
        
        # Проверяем совпадение AI категории с подписками
        ai_category_lower = str(ai_category).lower()
        matched = False
        
        for subscribed_name in subscribed_names:
            if subscribed_name in ai_category_lower or ai_category_lower in subscribed_name:
                matched = True
                break
        
        if matched:
            # Преобразуем данные в формат совместимый со старым кодом
            enhanced_post = {
                'id': post.get('id'),
                'title': post.get('title', 'Без заголовка'),
                'content': post.get('content', ''),
                'date': post.get('post_date'),
                'url': f"https://t.me/c/{abs(post.get('channel_telegram_id', 0))}/{post.get('telegram_message_id', 0)}",
                'views': post.get('views', 0),
                
                # 🚀 НОВЫЕ AI поля (маппинг со старых на новые)
                'summary': post.get('ai_summary', ''),
                'ai_summary': post.get('ai_summary', ''),
                'category': ai_category,
                'ai_category': ai_category,
                'importance': post.get('ai_importance', 0),
                'ai_importance': post.get('ai_importance', 0),
                'urgency': post.get('ai_urgency', 0),
                'ai_urgency': post.get('ai_urgency', 0),
                'significance': post.get('ai_significance', 0),
                'ai_significance': post.get('ai_significance', 0),
                
                # Метаданные канала
                'channel_telegram_id': post.get('channel_telegram_id'),
                'telegram_message_id': post.get('telegram_message_id'),
                'collected_at': post.get('collected_at'),
                'ai_processed_at': post.get('ai_processed_at'),
                
                # Отладочная информация
                'filtering_method': 'multitenant_ai_categorization_v2',
                'bot_id': PUBLIC_BOT_ID
            }
            
            filtered_posts.append(enhanced_post)
    
    logger.info(f"✅ Найдено {len(filtered_posts)} релевантных постов")
    
    if filtered_posts:
        return {
            'posts': filtered_posts,
            'total_posts': len(posts),
            'filtered_posts': len(filtered_posts),
            'filtering_version': 'v2_multitenant',
            'bot_id': PUBLIC_BOT_ID
        }
    
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    # Создаем или обновляем пользователя в системе
    await create_or_update_user(user)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я MorningStar Bot (v2) - ваш персональный дайджест Telegram каналов.\n\n"
        f"🚀 Новая версия с поддержкой:\n"
        f"• 🤖 AI-категоризация и саммаризация постов\n"
        f"• 🎯 Мультитенантность (bot_id: {PUBLIC_BOT_ID})\n"
        f"• 📊 Умные метрики (важность, срочность, значимость)\n"
        f"• 📬 Персональные дайджесты по подпискам\n\n"
        f"Используйте /help для списка команд."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📋 Доступные команды:\n\n"
        "/start - Начало работы\n"
        "/help - Эта справка\n"
        "/categories - Список доступных категорий\n"
        "/subscribe - Управление подписками\n"
        "/digest - Получить персональный дайджест\n"
        "/test - Тест получения AI постов\n"
        "/debug - Отладочная информация\n"
    )


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /categories - показать доступные категории"""
    loading_message = await update.message.reply_text("🔄 Загружаю категории бота...")
    
    # Получаем категории конкретного бота
    categories_data = await get_bot_categories()
    
    if not categories_data:
        await loading_message.edit_text(
            f"❌ Не удалось загрузить категории для бота {PUBLIC_BOT_ID}.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        return
    
    if not categories_data:
        await loading_message.edit_text(
            f"📝 Категории для бота {PUBLIC_BOT_ID} пока не настроены.\n"
            "Обратитесь к администратору для добавления категорий."
        )
        return
    
    # Формируем красивый список категорий
    categories_text = f"📚 Категории бота {PUBLIC_BOT_ID}:\n\n"
    
    for i, category in enumerate(categories_data, 1):
        emoji = category.get('emoji', '📝')
        name = category.get('name', 'Без названия')
        description = category.get('description', '')
        
        categories_text += f"{emoji} <b>{name}</b>\n"
        if description:
            categories_text += f"   <i>{description}</i>\n"
        categories_text += "\n"
    
    categories_text += "💡 <i>Используйте /subscribe для подписки на категории</i>"
    
    await loading_message.edit_text(categories_text, parse_mode='HTML')


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /subscribe - управление подписками"""
    user = update.effective_user
    
    await create_or_update_user(user)
    
    loading_message = await update.message.reply_text("🔄 Загружаю категории и ваши подписки...")
    
    # Получаем категории бота и текущие подписки параллельно
    categories_data, user_subscriptions = await asyncio.gather(
        get_bot_categories(),
        get_user_subscriptions(user.id)
    )
    
    if not categories_data:
        await loading_message.edit_text(
            f"❌ Не удалось загрузить категории для бота {PUBLIC_BOT_ID}.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        return
    
    # Создаем ID подписанных категорий для быстрого поиска
    subscribed_ids = {sub.get('id') for sub in (user_subscriptions or [])}
    
    # Создаем inline клавиатуру с категориями
    keyboard = []
    for category in categories_data:
        category_id = category.get('id')
        emoji = category.get('emoji', '📝')
        name = category.get('name', 'Без названия')
        
        # Добавляем ✅ если пользователь подписан
        if category_id in subscribed_ids:
            button_text = f"✅ {emoji} {name}"
        else:
            button_text = f"❌ {emoji} {name}"
        
        keyboard.append([InlineKeyboardButton(
            button_text, 
            callback_data=f"toggle_category_{category_id}"
        )])
    
    # Добавляем кнопку "Сохранить"
    keyboard.append([InlineKeyboardButton(
        "💾 Сохранить подписки", 
        callback_data="save_subscriptions"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем текст сообщения
    subscribed_count = len(user_subscriptions or [])
    message_text = (
        f"🎯 Управление подписками (Bot {PUBLIC_BOT_ID})\n\n"
        f"Выберите интересующие вас категории:\n"
        f"✅ - подписан, ❌ - не подписан\n\n"
        f"Текущих подписок: {subscribed_count}\n\n"
        f"Нажмите на категории для изменения, затем 'Сохранить'"
    )
    
    await loading_message.edit_text(message_text, reply_markup=reply_markup)


async def subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки подписок"""
    query = update.callback_query
    user = query.from_user
    data = query.data
    
    await query.answer()  # Убираем "loading" на кнопке
    
    if data.startswith("toggle_category_"):
        # Переключение подписки на категорию
        category_id = int(data.split("_")[-1])
        
        # Сохраняем выбор в user_data (временное состояние)
        if 'selected_categories' not in context.user_data:
            # Инициализируем текущими подписками пользователя
            user_subscriptions = await get_user_subscriptions(user.id)
            context.user_data['selected_categories'] = {
                sub.get('id') for sub in (user_subscriptions or [])
            }
        
        # Переключаем выбор категории
        if category_id in context.user_data['selected_categories']:
            context.user_data['selected_categories'].remove(category_id)
        else:
            context.user_data['selected_categories'].add(category_id)
        
        # Обновляем клавиатуру
        categories_data = await get_bot_categories()
        if not categories_data:
            await query.edit_message_text("❌ Ошибка загрузки категорий")
            return
        
        # Пересоздаем клавиатуру с обновленными статусами
        keyboard = []
        selected_ids = context.user_data['selected_categories']
        
        for category in categories_data:
            cat_id = category.get('id')
            emoji = category.get('emoji', '📝')
            name = category.get('name', 'Без названия')
            
            if cat_id in selected_ids:
                button_text = f"✅ {emoji} {name}"
            else:
                button_text = f"❌ {emoji} {name}"
            
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=f"toggle_category_{cat_id}"
            )])
        
        keyboard.append([InlineKeyboardButton(
            "💾 Сохранить подписки", 
            callback_data="save_subscriptions"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        selected_count = len(selected_ids)
        message_text = (
            f"🎯 Управление подписками (Bot {PUBLIC_BOT_ID})\n\n"
            f"Выберите интересующие вас категории:\n"
            f"✅ - подписан, ❌ - не подписан\n\n"
            f"Выбрано категорий: {selected_count}\n\n"
            f"Нажмите на категории для изменения, затем 'Сохранить'"
        )
        
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    
    elif data == "save_subscriptions":
        # Сохранение подписок
        selected_categories = context.user_data.get('selected_categories', set())
        category_ids = list(selected_categories)
        
        # Сохраняем в Backend API
        result = await update_user_subscriptions(user.id, category_ids)
        
        if result:
            success_text = (
                f"✅ Подписки для бота {PUBLIC_BOT_ID} сохранены!\n\n"
                f"{result.get('message', '')}\n\n"
                f"Теперь вы будете получать персональные дайджесты по выбранным категориям."
            )
            await query.edit_message_text(success_text)
        else:
            await query.edit_message_text(
                "❌ Ошибка сохранения подписок.\n"
                "Попробуйте позже или обратитесь к администратору."
            )
        
        # Очищаем временные данные
        context.user_data.pop('selected_categories', None)


async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /digest - получить персональный дайджест"""
    user = update.effective_user
    
    await create_or_update_user(user)
    
    loading_message = await update.message.reply_text(
        f"🔄 Генерирую персональный дайджест для бота {PUBLIC_BOT_ID}..."
    )
    
    # Получаем подписки пользователя
    user_subscriptions = await get_user_subscriptions(user.id)
    
    if not user_subscriptions:
        await loading_message.edit_text(
            f"📝 У вас пока нет подписок для бота {PUBLIC_BOT_ID}.\n\n"
            "Используйте команду /subscribe для выбора интересующих категорий, "
            "а затем повторите запрос дайджеста."
        )
        return
    
    # 🚀 НОВОЕ: Получаем AI-обработанные посты конкретного бота
    bot_posts = await get_bot_posts_with_ai(limit=100)
    
    if not bot_posts:
        await loading_message.edit_text(
            f"❌ Не удалось загрузить AI-обработанные посты для бота {PUBLIC_BOT_ID}.\n"
            "Возможно, бот еще не обработал посты или произошла ошибка."
        )
        return
    
    # Фильтруем посты по подписанным категориям
    filtered_data = await filter_posts_by_subscriptions(bot_posts, user_subscriptions)
    
    if not filtered_data:
        # Показываем список подписок и предложение ждать
        subscribed_names = [sub.get('name') for sub in user_subscriptions]
        categories_text = ", ".join([f"📝 {name}" for name in subscribed_names])
        
        await loading_message.edit_text(
            f"📭 Персональный дайджест временно недоступен\n\n"
            f"🤖 Бот: {PUBLIC_BOT_ID}\n"
            f"🎯 Ваши подписки: {categories_text}\n"
            f"📊 Проанализировано постов: {len(bot_posts)}\n\n"
            f"В последних AI-обработанных постах не найдено контента по вашим категориям. "
            f"Попробуйте позже или добавьте дополнительные подписки через /subscribe."
        )
        return
    
    # Формируем красивый дайджест
    filtered_posts = filtered_data.get('posts', [])
    total_posts = filtered_data.get('total_posts', 0)
    
    digest_text = f"📰 Персональный дайджест (Bot {PUBLIC_BOT_ID})\n\n"
    digest_text += f"📊 Найдено {len(filtered_posts)} из {total_posts} постов\n\n"
    
    # Группируем посты по категориям
    category_posts = {}
    for post in filtered_posts:
        category = post.get('category', 'Без категории')
        if category not in category_posts:
            category_posts[category] = []
        category_posts[category].append(post)
    
    # Сортируем категории по количеству постов
    sorted_categories = sorted(category_posts.items(), 
                              key=lambda x: len(x[1]), 
                              reverse=True)
    
    posts_added = 0
    max_posts_total = 15
    
    for category_name, posts in sorted_categories:
        if posts_added >= max_posts_total:
            break
            
        digest_text += f"\n📝 <b>{category_name.upper()}</b>\n"
        
        # Сортируем посты по комплексной метрике
        posts.sort(key=lambda p: (
            p.get('importance', 0) * 3 + 
            p.get('urgency', 0) * 2 + 
            p.get('significance', 0) * 2
        ), reverse=True)
        
        posts_in_category = 0
        max_posts_per_category = 6
        
        for post in posts:
            if posts_added >= max_posts_total or posts_in_category >= max_posts_per_category:
                break
            
            title = post.get('title', 'Без заголовка')
            summary = post.get('summary', '')
            importance = post.get('importance', 0)
            urgency = post.get('urgency', 0)
            significance = post.get('significance', 0)
            url = post.get('url', '')
            views = post.get('views', 0)
            date = post.get('date', '')
            
            # Дата
            if date:
                try:
                    date_formatted = date.split('T')[0] if 'T' in date else date
                    digest_text += f"📅 {date_formatted}\n"
                except:
                    pass
            
            # Резюме
            if summary:
                digest_text += f"💬 {summary}\n"
            
            # Ссылка + фрагмент оригинала
            if url:
                short_title = title[:60] + "..." if len(title) > 60 else title
                digest_text += f"🔗 {url}\n<i>{short_title}</i>\n"
            
            # AI Метрики + просмотры
            metrics_parts = []
            if importance > 0:
                metrics_parts.append(f"⚡ {importance}")
            if urgency > 0:
                metrics_parts.append(f"🚨 {urgency}")
            if significance > 0:
                metrics_parts.append(f"🎯 {significance}")
            if views > 0:
                metrics_parts.append(f"👁 {views:,}")
            
            if metrics_parts:
                digest_text += f"📊 {' • '.join(metrics_parts)}\n"
            
            digest_text += "\n"
            
            posts_added += 1
            posts_in_category += 1
    
    # Добавляем информацию о подписках и боте
    subscribed_names = [f"📝 {sub.get('name')}" for sub in user_subscriptions]
    digest_text += f"🤖 Бот: {PUBLIC_BOT_ID}\n"
    digest_text += f"🎯 Подписки: {', '.join(subscribed_names)}\n\n"
    digest_text += "💡 /subscribe для изменения подписок"
    
    # Проверяем длину сообщения (Telegram лимит ~4096 символов)
    if len(digest_text) > 4000:
        digest_text = digest_text[:3900] + "\n\n... (сообщение обрезано)\n\n💡 /subscribe для изменения подписок"
    
    await loading_message.edit_text(digest_text, parse_mode='HTML')


async def test_ai_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /test - тест получения AI постов"""
    loading_message = await update.message.reply_text(
        f"🔄 Тестирую получение AI постов для бота {PUBLIC_BOT_ID}..."
    )
    
    # Получаем AI посты
    ai_posts = await get_bot_posts_with_ai(limit=10)
    
    if not ai_posts:
        await loading_message.edit_text(
            f"❌ Не удалось получить AI посты для бота {PUBLIC_BOT_ID}.\n"
            "Возможно, бот еще не обработал посты или произошла ошибка."
        )
        return
    
    # Формируем отчет
    test_text = f"🤖 Тест AI постов для бота {PUBLIC_BOT_ID}\n\n"
    test_text += f"✅ Получено: {len(ai_posts)} постов\n\n"
    
    for i, post in enumerate(ai_posts[:5], 1):  # Показываем первые 5
        ai_category = post.get('ai_category', 'N/A')
        ai_importance = post.get('ai_importance', 0)
        ai_urgency = post.get('ai_urgency', 0)
        ai_significance = post.get('ai_significance', 0)
        channel_id = post.get('channel_telegram_id', 'N/A')
        
        test_text += f"{i}. Категория: {ai_category}\n"
        test_text += f"   Важность: {ai_importance}, Срочность: {ai_urgency}, Значимость: {ai_significance}\n"
        test_text += f"   Канал ID: {channel_id}\n\n"
    
    await loading_message.edit_text(test_text)


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /debug - отладочная информация"""
    loading_message = await update.message.reply_text("🔍 Собираю отладочную информацию...")
    
    # Получаем отладочные данные
    categories = await get_bot_categories()
    ai_posts = await get_bot_posts_with_ai(limit=5)
    
    debug_text = f"🔍 Отладка бота {PUBLIC_BOT_ID}:\n\n"
    
    # Информация о категориях
    if categories:
        debug_text += f"📚 Категории бота ({len(categories)}):\n"
        for cat in categories[:5]:  # Первые 5
            debug_text += f"   • {cat.get('name')} (ID: {cat.get('id')})\n"
        debug_text += "\n"
    else:
        debug_text += "❌ Нет категорий для бота\n\n"
    
    # Информация о AI постах
    if ai_posts:
        debug_text += f"🤖 AI Posts ({len(ai_posts)}):\n"
        for i, post in enumerate(ai_posts[:3], 1):  # Первые 3
            debug_text += f"   {i}. Категория: {post.get('ai_category', 'N/A')}\n"
            debug_text += f"      Важность: {post.get('ai_importance', 0)}\n"
            debug_text += f"      Канал ID: {post.get('channel_telegram_id', 'N/A')}\n"
        debug_text += "\n"
    else:
        debug_text += "❌ Нет AI-обработанных постов\n\n"
    
    # Информация о конфигурации
    debug_text += f"⚙️ Конфигурация:\n"
    debug_text += f"   • Bot ID: {PUBLIC_BOT_ID}\n"
    debug_text += f"   • Backend: {BACKEND_URL}\n"
    debug_text += f"   • Admin ID: {ADMIN_ID}\n"
    
    await loading_message.edit_text(debug_text)


def main():
    """Запуск бота"""
    logger.info(f"🚀 Запуск MorningStar Bot v2 для bot_id={PUBLIC_BOT_ID}")
    
    # Создаем приложение
    application = Application.builder().token(PUBLIC_BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", categories))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("digest", digest))
    application.add_handler(CommandHandler("test", test_ai_posts))
    application.add_handler(CommandHandler("debug", debug))
    
    # Регистрируем обработчик callback для кнопок подписок
    application.add_handler(CallbackQueryHandler(subscription_callback))
    
    # Запускаем бота
    logger.info(f"✅ Бот запущен для bot_id={PUBLIC_BOT_ID}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main() 