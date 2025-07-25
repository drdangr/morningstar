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
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
N8N_URL = os.getenv('N8N_URL', 'http://127.0.0.1:5678')


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
    """Получение подписок пользователя"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/api/users/{telegram_id}/subscriptions", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return []  # Пользователь не найден или нет подписок
                else:
                    return None
    except Exception as e:
        logger.error(f"Ошибка получения подписок: {e}")
        return None


async def update_user_subscriptions(telegram_id, category_ids):
    """Обновление подписок пользователя"""
    try:
        subscription_data = {"category_ids": category_ids}
        
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
        await loading_message.edit_text(
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
        name = category.get('name', 'Без названия')
        description = category.get('description', '')
        
        categories_text += f"{emoji} <b>{name}</b>\n"
        if description:
            categories_text += f"   <i>{description}</i>\n"
        categories_text += "\n"
    
    categories_text += "💡 <i>Используйте /subscribe для подписки на категории</i>"
    
    # Обновляем сообщение
    await loading_message.edit_text(categories_text, parse_mode='HTML')


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
        await loading_message.edit_text(
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
        f"🎯 Управление подписками\n\n"
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
        categories_data = await get_categories()
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
            f"🎯 Управление подписками\n\n"
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
                f"✅ Подписки успешно сохранены!\n\n"
                f"{result.get('message', '')}\n\n"
                f"Теперь вы будете получать дайджесты по выбранным категориям."
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
    
    # Создаем или обновляем пользователя
    await create_or_update_user(user)
    
    # Отправляем уведомление о загрузке
    loading_message = await update.message.reply_text("🔄 Генерирую ваш персональный дайджест...")
    
    # Получаем подписки пользователя
    user_subscriptions = await get_user_subscriptions(user.id)
    
    if not user_subscriptions:
        await loading_message.edit_text(
            "📝 У вас пока нет подписок на категории.\n\n"
            "Используйте команду /subscribe для выбора интересующих категорий, "
            "а затем повторите запрос дайджеста."
        )
        return
    
    # Получаем последние дайджесты
    recent_digests = await get_recent_digests(5)
    
    if not recent_digests:
        await loading_message.edit_text(
            "❌ Не удалось загрузить дайджесты.\n"
            "Возможно, система еще не сгенерировала дайджесты или произошла ошибка."
        )
        return
    
    # Ищем подходящий дайджест для пользователя
    personal_digest = None
    for digest_summary in recent_digests:
        digest_id = digest_summary.get('digest_id')
        if not digest_id:
            continue
            
        # Получаем полные данные дайджеста
        digest_data = await get_digest_data(digest_id)
        if not digest_data:
            continue
        
        # Фильтруем по подписанным категориям
        filtered_digest = await filter_digest_by_subscriptions(digest_data, user_subscriptions)
        if filtered_digest:
            personal_digest = filtered_digest
            personal_digest['digest_info'] = digest_summary
            break
    
    if not personal_digest:
        # Показываем список подписок и предложение ждать
        subscribed_names = [sub.get('name') for sub in user_subscriptions]
        categories_text = ", ".join([f"{sub.get('emoji', '📝')} {sub.get('name')}" for sub in user_subscriptions])
        
        await loading_message.edit_text(
            f"📭 Персональный дайджест временно недоступен\n\n"
            f"Ваши подписки: {categories_text}\n\n"
            f"В последних дайджестах не найдено постов по вашим категориям. "
            f"Попробуйте позже или добавьте дополнительные подписки через /subscribe."
        )
        return
    
    # Формируем красивый дайджест
    digest_text = f"📰 Ваш персональный дайджест\n\n"
    
    # Информация о дайджесте
    digest_info = personal_digest.get('digest_info', {})
    created_at = digest_info.get('created_at', 'Неизвестно')
    if 'T' in created_at:
        created_at = created_at.split('T')[0]  # Берем только дату
    
    digest_text += f"🗓 Создан: {created_at}\n"
    
    # Показываем статистику фильтрации
    total_posts = personal_digest.get('original_posts_count', 0)
    filtered_posts = personal_digest.get('filtered_posts_count', 0)
    relevant_channels = personal_digest.get('relevant_channels', 0)
    
    digest_text += f"📊 Найдено {filtered_posts} из {total_posts} постов из {relevant_channels} каналов\n\n"
    
    # Добавляем посты с новой группировкой Тема → Канал → Посты
    summary_data = personal_digest.get('summary', {})
    if isinstance(summary_data, dict):
        posts = summary_data.get('posts', [])
        
        # Группируем по темам и каналам
        theme_channel_posts = {}
        for post in posts:
            category = post.get('category', 'Без категории')
            channel_title = post.get('channel_title', 'Неизвестный канал')
            
            if category not in theme_channel_posts:
                theme_channel_posts[category] = {}
            if channel_title not in theme_channel_posts[category]:
                theme_channel_posts[category][channel_title] = []
            
            theme_channel_posts[category][channel_title].append(post)
        
        # Сортируем темы по количеству постов
        sorted_themes = sorted(theme_channel_posts.items(), 
                              key=lambda x: sum(len(posts) for posts in x[1].values()), 
                              reverse=True)
        
        posts_added = 0
        max_posts_total = 15
        
        for theme_name, channels in sorted_themes:
            if posts_added >= max_posts_total:
                break
                
            # Находим эмодзи темы из подписок пользователя
            theme_emoji = "📝"  # По умолчанию
            for sub in user_subscriptions:
                if sub.get('name', '').lower() == theme_name.lower():
                    theme_emoji = sub.get('emoji', '📝')
                    break
            
            digest_text += f"\n{theme_emoji} <b>{theme_name.upper()}</b>\n"
            
            # Сортируем каналы по количеству постов
            sorted_channels = sorted(channels.items(), 
                                   key=lambda x: len(x[1]), 
                                   reverse=True)
            
            for channel_name, channel_posts in sorted_channels:
                if posts_added >= max_posts_total:
                    break
                    
                digest_text += f"\n📺 <b>{channel_name}</b>\n"
                
                # Сортируем посты по важности
                channel_posts.sort(key=lambda p: (
                    p.get('importance', 0) * 3 + 
                    p.get('urgency', 0) * 2 + 
                    p.get('significance', 0) * 2
                ), reverse=True)
                
                posts_in_channel = 0
                max_posts_per_channel = 8
                
                for post in channel_posts:
                    if posts_added >= max_posts_total or posts_in_channel >= max_posts_per_channel:
                        break
                    
                    title = post.get('title', 'Без заголовка')
                    summary = post.get('summary', post.get('ai_summary', ''))
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
                        short_title = title[:80] + "..." if len(title) > 80 else title
                        digest_text += f"🔗 {url} <i>{short_title}</i>\n"
                    
                    # Метрики + просмотры
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
                    posts_in_channel += 1
    
    # Добавляем информацию о подписках
    subscribed_names = [f"{sub.get('emoji', '📝')} {sub.get('name')}" for sub in user_subscriptions]
    digest_text += f"🎯 Ваши подписки: {', '.join(subscribed_names)}\n\n"
    digest_text += "💡 Используйте /subscribe для изменения подписок"
    
    # Проверяем длину сообщения (Telegram лимит ~4096 символов)
    if len(digest_text) > 4000:
        # Обрезаем до безопасной длины
        digest_text = digest_text[:3900] + "\n\n... (сообщение обрезано)\n\n💡 Используйте /subscribe для изменения подписок"
    
    await loading_message.edit_text(digest_text, parse_mode='HTML')


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
    subscribed_names = {cat.get('name', '').lower() for cat in (user_subscriptions or [])}
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
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("digest", digest))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("debug_digest", debug_digest))
    application.add_handler(CommandHandler("debug_filter", debug_filter))
    
    # Регистрируем обработчик callback для кнопок подписок
    application.add_handler(CallbackQueryHandler(subscription_callback))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()