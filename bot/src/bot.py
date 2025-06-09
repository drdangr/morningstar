import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
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
        "/status - Статус системы\n"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - только для админа"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    
    await update.message.reply_text(
        "✅ Бот работает!\n\n"
        "📊 Статус системы:\n"
        "• Userbot: 🟡 В разработке\n"
        "• База данных: 🟡 В разработке\n"
        "• n8n: 🟡 В разработке\n"
    )


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
    application.add_handler(CommandHandler("status", status))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()