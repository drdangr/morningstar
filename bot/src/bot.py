import os
import logging
import aiohttp
import asyncio
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
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID') or os.getenv('ADMIN_CHAT_ID', '0'))
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:8000')
N8N_URL = os.getenv('N8N_URL', 'http://127.0.0.1:5678')
BOT_ID = int(os.getenv('BOT_ID', '1'))

# Утилиты безопасного редактирования, чтобы избежать ошибок и подвисаний UI
async def safe_edit_message_text(message, text, **kwargs):
    try:
        await asyncio.sleep(0.05)
        await message.edit_text(text, **kwargs)
    except Exception as e:
        if 'Message is not modified' in str(e):
            return
        logger.error(f"Ошибка edit_text: {e}")

async def safe_query_edit_text(query, text, **kwargs):
    try:
        await asyncio.sleep(0.05)
        await query.edit_message_text(text, **kwargs)
    except Exception as e:
        if 'Message is not modified' in str(e):
            return
        logger.error(f"Ошибка edit_message_text: {e}")


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


async def check_n8n_status():
    """Проверка статуса N8N"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{N8N_URL}/healthz", timeout=5) as response:
                if response.status == 200:
                    return "🟢 Работает"
                else:
                    return "🟡 Недоступен"
    except Exception as e:
        logger.error(f"Ошибка проверки N8N: {e}")
        return "🔴 Ошибка"


async def check_userbot_status():
    """Проверка статуса Userbot (через Backend API)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/stats", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    # Если есть каналы в базе и последние 24 часа были активности
                    if data.get('total_channels', 0) > 0:
                        return "🟢 Работает"
                    else:
                        return "🟡 Нет активности"
                else:
                    return "🟡 Недоступен"
    except Exception as e:
        logger.error(f"Ошибка проверки статуса через Backend: {e}")
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


async def get_categories():
    """Получение списка категорий, привязанных к текущему публичному боту"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/public-bots/{BOT_ID}/categories", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения категорий: {e}")
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
    """Получение подписок пользователя (мультитенантно для конкретного бота)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BACKEND_URL}/api/public-bots/{BOT_ID}/users/{telegram_id}/subscriptions",
                timeout=5,
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return []
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return None


async def update_user_subscriptions(telegram_id, category_ids):
    """Обновление подписок пользователя (мультитенантно для конкретного бота)"""
    try:
        subscription_data = {"category_ids": category_ids}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/public-bots/{BOT_ID}/users/{telegram_id}/subscriptions",
                json=subscription_data,
                timeout=5,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка обновления подписок: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка API подписок: {e}")
        return None

# === Подписки на каналы (мультитенантно) ===
async def get_bot_channels():
    """Получить каналы, привязанные к текущему публичному боту"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/public-bots/{BOT_ID}/channels", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ошибка получения каналов бота: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка API каналов: {e}")
        return []

async def get_user_channel_subscriptions(telegram_id):
    """Получить подписанные пользователем каналы для текущего бота"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BACKEND_URL}/api/public-bots/{BOT_ID}/users/{telegram_id}/channel-subscriptions",
                timeout=10,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("subscribed_channels", []) if isinstance(data, dict) else []
                elif response.status == 404:
                    return []
                else:
                    logger.error(f"Ошибка получения подписок на каналы: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Ошибка API подписок каналов: {e}")
        return []

async def update_user_channel_subscriptions(telegram_id, channel_ids):
    """Сохранить подписки пользователя на каналы для текущего бота"""
    try:
        payload = {"channel_ids": channel_ids}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BACKEND_URL}/api/public-bots/{BOT_ID}/users/{telegram_id}/channel-subscriptions",
                json=payload,
                timeout=10,
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    txt = await response.text()
                    logger.error(f"Ошибка сохранения подписок каналов: {response.status} {txt}")
                    return None
    except Exception as e:
        logger.error(f"Ошибка API сохранения подписок каналов: {e}")
        return None


async def get_recent_digests(limit=10):
    """Получение последних дайджестов"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/digests?limit={limit}", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения дайджестов: {e}")
        return None


async def get_digest_data(digest_id):
    """Получение полных данных дайджеста"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/digests/{digest_id}/data", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения данных дайджеста: {e}")
        return None


async def filter_digest_by_subscriptions(digest_data, subscribed_categories):
    """
    Фильтрует дайджест по подпискам пользователя с индивидуальной категоризацией постов v7.3
    
    Args:
        digest_data: Полные данные дайджеста
        subscribed_categories: Список подписанных категорий пользователя
    
    Returns:
        Отфильтрованный дайджест или None если нет релевантных постов
    """
    if not digest_data or not subscribed_categories:
        return None
    
    # Получаем названия подписанных категорий
    subscribed_names = {cat.get('name', '').lower() for cat in subscribed_categories}
    
    if not subscribed_names:
        return None
    
    # Проверяем наличие каналов
    if 'channels' not in digest_data or not isinstance(digest_data['channels'], list):
        return None
    
    filtered_posts = []
    relevant_channels_set = set()
    total_posts = 0
    
    # v7.3 ПРОРЫВ: Фильтруем по индивидуальным категориям постов, а не каналов
    for channel in digest_data['channels']:
        # Считаем общее количество постов
        channel_posts = channel.get('posts', [])
        if isinstance(channel_posts, list):
            total_posts += len(channel_posts)
        
        # v7.3: Проходим по каждому посту и проверяем его индивидуальную категорию
        for post in channel_posts:
            # Получаем индивидуальную категорию поста от AI
            post_category = post.get('post_category', post.get('ai_assigned_category', ''))
            
            # СТРОГАЯ ПРОВЕРКА: если AI не определил категорию, пост считается нерелевантным
            if not post_category or post_category in ['NULL', 'null', '', 'Unknown', 'Без категории']:
                # Пропускаем пост - AI не смог определить релевантную категорию
                continue
            
            # Проверяем совпадение индивидуальной категории поста с подписками
            post_category_lower = str(post_category).lower()
            matched_category = None
            
            for subscribed_name in subscribed_names:
                if subscribed_name in post_category_lower or post_category_lower in subscribed_name:
                    matched_category = post_category  # Используем индивидуальную категорию поста
                    break
            
            # Если пост релевантен по своей индивидуальной категории
            if matched_category:
                relevant_channels_set.add(channel.get('title', 'Неизвестный канал'))
                
                # Добавляем информацию о канале к посту
                enhanced_post = post.copy()
                enhanced_post['channel_title'] = channel.get('title', 'Неизвестный канал')
                enhanced_post['channel_username'] = channel.get('username', '')
                enhanced_post['channel_categories'] = channel.get('categories', [])
                
                # Переименовываем поля для совместимости
                enhanced_post['importance'] = post.get('ai_importance', 0)
                enhanced_post['urgency'] = post.get('ai_urgency', 0)
                enhanced_post['significance'] = post.get('ai_significance', 0)
                
                # v7.3 ПРОРЫВ: Используем ИНДИВИДУАЛЬНУЮ категорию поста вместо категории канала
                enhanced_post['category'] = matched_category
                enhanced_post['individual_categorization'] = True
                
                # Добавляем отладочную информацию для прозрачности
                enhanced_post['original_post_category'] = post_category
                enhanced_post['ai_assigned_category'] = post.get('ai_assigned_category', '')
                enhanced_post['category_is_valid'] = post.get('category_is_valid', False)
                enhanced_post['filtering_method'] = 'strict_ai_categorization_v7.3'  # Без fallback
                
                filtered_posts.append(enhanced_post)
    
    # Если нашли релевантные посты, создаем персональный дайджест
    if filtered_posts:
        personal_digest = digest_data.copy()
        
        # Создаем новую структуру summary с постами
        personal_digest['summary'] = {
            'posts': filtered_posts,
            'channels_processed': len(relevant_channels_set),
            'original_posts': total_posts,
            'relevant_posts': len(filtered_posts)
        }
        
        personal_digest['filtered'] = True
        personal_digest['individual_post_categorization'] = True
        personal_digest['original_posts_count'] = total_posts
        personal_digest['filtered_posts_count'] = len(filtered_posts)
        personal_digest['relevant_channels'] = len(relevant_channels_set)
        personal_digest['filtering_version'] = 'v7.3_individual_post_categorization'
        
        return personal_digest
    
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    # Создаем или обновляем пользователя в системе
    await create_or_update_user(user)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я MorningStar Bot - твой персональный дайджест Telegram каналов.\n\n"
        "Пока я в разработке, но скоро смогу:\n"
        "• 📰 Собирать новости из выбранных каналов\n"
        "• 🤖 Создавать умные саммари с помощью AI\n"
        "• 📬 Отправлять персональные дайджесты\n\n"
        "Используй /help для списка команд."
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
        "/status - Статус системы (только для админа)\n"
    )


async def categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /categories - показать доступные категории"""
    # Отправляем уведомление о загрузке
    loading_message = await update.message.reply_text("🔄 Загружаю список категорий...")
    
    # Получаем категории из Backend API
    categories_data = await get_categories()
    
    if not categories_data:
        await safe_edit_message_text(
            loading_message,
            "❌ Не удалось загрузить категории.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        return
    
    if not categories_data:
        await loading_message.edit_text(
            "📝 Категории пока не настроены.\n"
            "Обратитесь к администратору для добавления категорий."
        )
        return
    
    # Формируем красивый список категорий
    categories_text = "📚 Доступные категории для подписки:\n\n"
    
    for i, category in enumerate(categories_data, 1):
        emoji = category.get('emoji', '📝')
        name = category.get('name') or category.get('category_name', 'Без названия')
        description = category.get('description', '')
        
        categories_text += f"{emoji} <b>{name}</b>\n"
        if description:
            categories_text += f"   <i>{description}</i>\n"
        categories_text += "\n"
    
    categories_text += "💡 <i>Используйте /subscribe для подписки на категории</i>"
    
    # Обновляем сообщение
    await safe_edit_message_text(loading_message, categories_text, parse_mode='HTML')


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /subscribe - управление подписками"""
    user = update.effective_user
    
    # Создаем или обновляем пользователя
    await create_or_update_user(user)
    
    # Отправляем уведомление о загрузке
    loading_message = await update.message.reply_text("🔄 Загружаю категории и ваши подписки...")
    
    # Получаем категории и текущие подписки параллельно
    categories_data, user_subscriptions = await asyncio.gather(
        get_categories(),
        get_user_subscriptions(user.id)
    )
    
    if not categories_data:
        await safe_edit_message_text(
            loading_message,
            "❌ Не удалось загрузить категории.\n"
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
        name = category.get('name') or category.get('category_name', 'Без названия')
        
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
        f"🎯 Управление подписками\n\n"
        f"Выберите интересующие вас категории:\n"
        f"✅ - подписан, ❌ - не подписан\n\n"
        f"Текущих подписок: {subscribed_count}\n\n"
        f"Нажмите на категории для изменения, затем 'Сохранить'"
    )
    
    await safe_edit_message_text(loading_message, message_text, reply_markup=reply_markup)


async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /channels - управление подписками на каналы"""
    user = update.effective_user
    loading_message = await update.message.reply_text("🔄 Загружаю каналы и ваши подписки...")

    # Получаем каналы бота и текущие подписки пользователя
    async with aiohttp.ClientSession() as session:
        pass
    bot_channels = await get_bot_channels()
    user_channel_subs = await get_user_channel_subscriptions(user.id)

    if not bot_channels:
        await safe_edit_message_text(loading_message, "❌ Не удалось загрузить список каналов.")
        return

    # Текущие подписанные id каналов
    subscribed_channel_ids = {ch.get("id") for ch in (user_channel_subs or [])}

    # Строим inline клавиатуру
    keyboard = []
    for ch in bot_channels:
        ch_id = ch.get("id")
        title = ch.get("title") or ch.get("channel_name") or f"Канал {ch_id}"
        is_sub = ch_id in subscribed_channel_ids
        button_text = f"{'✅' if is_sub else '❌'} {title}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_channel_{ch_id}")])

    keyboard.append([InlineKeyboardButton("💾 Сохранить каналы", callback_data="save_channel_subscriptions")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await safe_edit_message_text(loading_message, "📺 Управление подписками на каналы", reply_markup=reply_markup)


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
        categories_data = await get_categories()
        if not categories_data:
            await safe_query_edit_text(query, "❌ Ошибка загрузки категорий")
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
            f"🎯 Управление подписками\n\n"
            f"Выберите интересующие вас категории:\n"
            f"✅ - подписан, ❌ - не подписан\n\n"
            f"Выбрано категорий: {selected_count}\n\n"
            f"Нажмите на категории для изменения, затем 'Сохранить'"
        )
        
        await safe_query_edit_text(query, message_text, reply_markup=reply_markup)
    
    elif data == "save_subscriptions":
        # Сохранение подписок
        selected_categories = context.user_data.get('selected_categories', set())
        category_ids = list(selected_categories)
        
        # Сохраняем в Backend API
        result = await update_user_subscriptions(user.id, category_ids)
        
        if result:
            success_text = (
                f"✅ Подписки успешно сохранены!\n\n"
                f"{result.get('message', '')}\n\n"
                f"Теперь вы будете получать дайджесты по выбранным категориям."
            )
            await safe_query_edit_text(query, success_text)
        else:
            await safe_query_edit_text(
                "❌ Ошибка сохранения подписок.\n"
                "Попробуйте позже или обратитесь к администратору."
            )
        
        # Очищаем временные данные
        context.user_data.pop('selected_categories', None)

    # === Подписки на каналы ===
    elif data.startswith("toggle_channel_"):
        channel_id = int(data.split("_")[-1])

        # Инициализируем выбранные каналы текущими подписками
        if 'selected_channels' not in context.user_data:
            current_subs = await get_user_channel_subscriptions(user.id)
            context.user_data['selected_channels'] = {ch.get('id') for ch in (current_subs or [])}

        # Переключаем выбор
        if channel_id in context.user_data['selected_channels']:
            context.user_data['selected_channels'].remove(channel_id)
        else:
            context.user_data['selected_channels'].add(channel_id)

        # Перерисовываем клавиатуру
        bot_channels = await get_bot_channels()
        if not bot_channels:
            await safe_query_edit_text(query, "❌ Ошибка загрузки каналов")
            return

        keyboard = []
        selected_ids = context.user_data['selected_channels']
        for ch in bot_channels:
            ch_id = ch.get('id')
            title = ch.get('title') or ch.get('channel_name') or f"Канал {ch_id}"
            is_sub = ch_id in selected_ids
            button_text = f"{'✅' if is_sub else '❌'} {title}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_channel_{ch_id}")])
        keyboard.append([InlineKeyboardButton("💾 Сохранить каналы", callback_data="save_channel_subscriptions")])

        await safe_query_edit_text(query, "📺 Управление подписками на каналы", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "save_channel_subscriptions":
        selected_channels = context.user_data.get('selected_channels', set())
        channel_ids = list(selected_channels)

        result = await update_user_channel_subscriptions(user.id, channel_ids)

        if result:
            await safe_query_edit_text(
                f"✅ Подписки на каналы сохранены!\n\nВыбрано каналов: {len(channel_ids)}"
            )
        else:
            await safe_query_edit_text(query, "❌ Ошибка сохранения подписок на каналы. Попробуйте позже.")

        context.user_data.pop('selected_channels', None)


async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /digest — запрос готового дайджеста от Backend."""
    user = update.effective_user
    await create_or_update_user(user)
    loading_message = await update.message.reply_text("🔄 Генерирую ваш персональный дайджест...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/public-bots/{BOT_ID}/users/{user.id}/digest?limit=15", timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    text = data.get('text') or "❌ Пустой дайджест"
                    await loading_message.edit_text(text, parse_mode='HTML')
                else:
                    await loading_message.edit_text("❌ Не удалось сформировать дайджест. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка /digest: {e}")
        await loading_message.edit_text("❌ Ошибка при запросе дайджеста. Попробуйте позже.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - только для админа"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    
    # Отправляем уведомление о проверке
    status_message = await update.message.reply_text("🔄 Проверяю статус компонентов...")
    
    # Проверяем все компоненты параллельно
    backend_status, n8n_status, userbot_status = await asyncio.gather(
        check_backend_status(),
        check_n8n_status(),
        check_userbot_status()
    )
    
    # Получаем статистику
    stats = await get_system_stats()
    
    # Формируем ответ
    status_text = "📊 Статус системы:\n\n"
    status_text += f"• Backend API: {backend_status}\n"
    status_text += f"• N8N Workflow: {n8n_status}\n"
    status_text += f"• Userbot: {userbot_status}\n\n"
    
    if stats:
        status_text += "📈 Статистика:\n"
        status_text += f"• Каналов: {stats.get('total_channels', 0)}\n"
        status_text += f"• Активных каналов: {stats.get('active_channels', 0)}\n"
        status_text += f"• Категорий: {stats.get('total_categories', 0)}\n"
        status_text += f"• Дайджестов: {stats.get('total_digests', 0)}\n"
    else:
        status_text += "📊 Статистика недоступна"
    
    # Обновляем сообщение
    await status_message.edit_text(status_text)


async def debug_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /debug_filter - отладка фильтрации (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    
    user = update.effective_user
    await create_or_update_user(user)
    
    loading_message = await update.message.reply_text("🔍 Отладка фильтрации...")
    
    # Получаем подписки и дайджест
    user_subscriptions = await get_user_subscriptions(user.id)
    recent_digests = await get_recent_digests(1)
    
    if not recent_digests:
        await loading_message.edit_text("❌ Нет дайджестов")
        return
    
    digest_data = await get_digest_data(recent_digests[0].get('digest_id'))
    if not digest_data:
        await loading_message.edit_text("❌ Нет данных дайджеста")
        return
    
    debug_text = "🔍 Отладка фильтрации:\n\n"
    
    # Показываем подписки
    subscribed_names = {
        (cat.get('name') or cat.get('category_name') or '').lower()
        for cat in (user_subscriptions or [])
    }
    debug_text += f"🎯 Подписки: {subscribed_names}\n\n"
    
    # Показываем каналы и их категории
    for channel in digest_data.get('channels', []):
        channel_title = channel.get('title', 'Без названия')
        channel_categories = channel.get('categories', [])
        
        debug_text += f"📺 {channel_title}:\n"
        debug_text += f"   Категории: {channel_categories}\n"
        
        # Проверяем каждую категорию
        channel_relevant = False
        for cat in channel_categories:
            if isinstance(cat, dict):
                cat_name = cat.get('name', '').lower()
            else:
                cat_name = str(cat).lower()
            
            debug_text += f"   📋 Категория: '{cat_name}'\n"
            
            for sub_name in subscribed_names:
                match = sub_name in cat_name or cat_name in sub_name
                debug_text += f"      vs '{sub_name}': {'✅ MATCH' if match else '❌ NO'}\n"
                if match:
                    channel_relevant = True
        
        debug_text += f"   🏁 Релевантен: {channel_relevant}\n\n"
    
    await loading_message.edit_text(debug_text)


async def debug_digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /debug_digest - отладка структуры дайджеста (только для админа)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    
    loading_message = await update.message.reply_text("🔍 Анализирую структуру последнего дайджеста...")
    
    # Получаем последний дайджест
    recent_digests = await get_recent_digests(1)
    
    if not recent_digests:
        await loading_message.edit_text("❌ Нет доступных дайджестов")
        return
    
    digest_summary = recent_digests[0]
    digest_id = digest_summary.get('digest_id')
    
    # Получаем полные данные
    digest_data = await get_digest_data(digest_id)
    
    if not digest_data:
        await loading_message.edit_text("❌ Не удалось получить данные дайджеста")
        return
    
    # Анализируем структуру
    debug_text = f"🔍 Отладка дайджеста {digest_id}\n\n"
    debug_text += f"📊 Основные ключи: {list(digest_data.keys())}\n\n"
    
    # Показываем содержимое всех основных полей
    for key, value in digest_data.items():
        if key in ['id', 'created_at', 'processed_at']:
            debug_text += f"📝 {key}: {value}\n"
        elif key == 'total_posts':
            debug_text += f"📊 {key}: {value}\n"
        elif key == 'channels' and isinstance(value, list):
            debug_text += f"📺 {key}: {len(value)} каналов\n"
            if len(value) > 0:
                first_channel = value[0]
                debug_text += f"   Ключи первого канала: {list(first_channel.keys())}\n"
                # Проверяем, есть ли посты в каналах
                if 'posts' in first_channel:
                    posts = first_channel['posts']
                    debug_text += f"   📰 Постов в первом канале: {len(posts) if isinstance(posts, list) else 'не список'}\n"
        elif key == 'summary' and isinstance(value, dict):
            debug_text += f"📝 {key}: {list(value.keys())}\n"
        else:
            debug_text += f"🔍 {key}: {type(value)} - {str(value)[:100]}...\n"
    
    debug_text += "\n"
    
    # Если есть каналы с постами, покажем структуру постов
    if 'channels' in digest_data and isinstance(digest_data['channels'], list):
        for i, channel in enumerate(digest_data['channels'][:1]):  # Только первый канал
            if 'posts' in channel and isinstance(channel['posts'], list) and len(channel['posts']) > 0:
                first_post = channel['posts'][0]
                debug_text += f"📰 Структура поста из канала {i+1}:\n"
                debug_text += f"   Ключи: {list(first_post.keys())}\n"
                
                # Ищем поля с категориями
                for key, value in first_post.items():
                    if any(cat_word in key.lower() for cat_word in ['category', 'topic', 'theme', 'subject']):
                        debug_text += f"   🏷 {key}: {value}\n"
                break
    
    # Проверяем длину и отправляем
    if len(debug_text) > 4000:
        debug_text = debug_text[:3900] + "\n... (обрезано)"
    
    await loading_message.edit_text(debug_text)


def main():
    """Запуск бота"""
    # Создаем приложение
    if not PUBLIC_BOT_TOKEN:
        logger.error("PUBLIC_BOT_TOKEN не найден в переменных окружения!")
        return
    
    application = Application.builder().token(PUBLIC_BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", categories))
    application.add_handler(CommandHandler("channels", channels))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("digest", digest))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("debug_digest", debug_digest))
    application.add_handler(CommandHandler("debug_filter", debug_filter))
    
    # Регистрируем обработчик callback для кнопок подписок
    application.add_handler(CallbackQueryHandler(subscription_callback))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == '__main__':
    main()