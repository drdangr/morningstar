#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MultiBotManager - мультитенантный менеджер для управления множественными Telegram ботами

Архитектура:
- Получает активных ботов из Backend API
- Запускает отдельный экземпляр бота для каждого токена
- Управляет жизненным циклом ботов (start/stop/restart)
- Обеспечивает изоляцию и мультитенантность
- Реагирует на изменения конфигурации через webhooks

Основные компоненты:
- BotInstance: отдельный экземпляр бота с уникальным токеном
- MultiBotManager: оркестратор для управления всеми ботами
- WebhookServer: HTTP сервер для приема уведомлений об изменениях
"""

import asyncio
import logging
import time
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import json
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, Unauthorized, ApiIdInvalid
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
import uvicorn
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multibot_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Конфигурация бота из Backend API"""
    bot_id: int
    name: str
    bot_token: str
    status: str  # active, paused, development
    welcome_message: str
    categorization_prompt: str
    summarization_prompt: str
    max_posts_per_digest: int
    max_summary_length: int
    created_at: str
    updated_at: str

class BotInstance:
    """Отдельный экземпляр Telegram бота"""
    
    def __init__(self, config: BotConfig, backend_api_url: str):
        self.config = config
        self.backend_api_url = backend_api_url
        self.client: Optional[Client] = None
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.message_count = 0
        self.error_count = 0
        
        # Уникальная session для каждого бота
        self.session_name = f"bot_{config.bot_id}_{config.name.replace(' ', '_')}"
        
        logger.info(f"Создан BotInstance для бота {config.bot_id}: {config.name}")
    
    async def start(self) -> bool:
        """Запуск экземпляра бота"""
        try:
            if self.is_running:
                logger.warning(f"Бот {self.config.bot_id} уже запущен")
                return True
            
            # Создание Pyrogram Client
            self.client = Client(
                name=self.session_name,
                bot_token=self.config.bot_token,
                session_string=None,  # Будет использоваться session файл
                workdir="session/"
            )
            
            # Регистрация обработчиков
            self._register_handlers()
            
            # Запуск бота
            await self.client.start()
            self.is_running = True
            self.start_time = datetime.now()
            
            # Получение информации о боте
            me = await self.client.get_me()
            logger.info(f"✅ Запущен бот {self.config.bot_id}: {me.first_name} (@{me.username})")
            
            return True
            
        except Unauthorized:
            logger.error(f"❌ Неверный токен для бота {self.config.bot_id}: {self.config.name}")
            self.error_count += 1
            return False
        except ApiIdInvalid:
            logger.error(f"❌ Неверный API ID для бота {self.config.bot_id}: {self.config.name}")
            self.error_count += 1
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота {self.config.bot_id}: {e}")
            logger.error(traceback.format_exc())
            self.error_count += 1
            return False
    
    async def stop(self):
        """Остановка экземпляра бота"""
        try:
            if not self.is_running:
                logger.warning(f"Бот {self.config.bot_id} уже остановлен")
                return
            
            if self.client:
                await self.client.stop()
                
            self.is_running = False
            self.start_time = None
            
            logger.info(f"🛑 Остановлен бот {self.config.bot_id}: {self.config.name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота {self.config.bot_id}: {e}")
            logger.error(traceback.format_exc())
    
    def _register_handlers(self):
        """Регистрация обработчиков команд"""
        if not self.client:
            return
        
        # Обработчик команды /start
        @self.client.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            self.message_count += 1
            await message.reply_text(
                self.config.welcome_message or f"Привет! Я {self.config.name}. Добро пожаловать!",
                reply_markup=None
            )
            logger.info(f"📨 Бот {self.config.bot_id} обработал команду /start от {message.from_user.id}")
        
        # Обработчик команды /help
        @self.client.on_message(filters.command("help") & filters.private)
        async def help_handler(client, message: Message):
            self.message_count += 1
            help_text = f"""
🤖 **{self.config.name}**

📋 **Доступные команды:**
/start - Начать работу с ботом
/help - Показать эту справку
/status - Статус бота
/categories - Доступные категории

ℹ️ **Информация:**
• Бот ID: {self.config.bot_id}
• Статус: {self.config.status}
• Максимум постов в дайджесте: {self.config.max_posts_per_digest}
"""
            await message.reply_text(help_text)
            logger.info(f"📨 Бот {self.config.bot_id} обработал команду /help от {message.from_user.id}")
        
        # Обработчик команды /status
        @self.client.on_message(filters.command("status") & filters.private)
        async def status_handler(client, message: Message):
            self.message_count += 1
            uptime = datetime.now() - self.start_time if self.start_time else None
            status_text = f"""
📊 **Статус бота {self.config.name}**

🟢 **Работает с** {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'N/A'}
📈 **Uptime:** {str(uptime).split('.')[0] if uptime else 'N/A'}
📨 **Обработано сообщений:** {self.message_count}
❌ **Ошибок:** {self.error_count}
🔧 **Режим:** {self.config.status}
"""
            await message.reply_text(status_text)
            logger.info(f"📨 Бот {self.config.bot_id} обработал команду /status от {message.from_user.id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики экземпляра бота"""
        uptime = datetime.now() - self.start_time if self.start_time else None
        return {
            "bot_id": self.config.bot_id,
            "name": self.config.name,
            "status": self.config.status,
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": uptime.total_seconds() if uptime else 0,
            "message_count": self.message_count,
            "error_count": self.error_count
        }

# Добавляем недостающие импорты
from fastapi import FastAPI, HTTPException
import uvicorn
import threading

# === WEBHOOK SERVER ===

class WebhookServer:
    """HTTP сервер для приема webhook уведомлений от Backend API"""
    
    def __init__(self, manager: 'MultiBotManager', port: int = 8001):
        self.manager = manager
        self.port = port
        self.app = FastAPI(title="MultiBotManager Webhook Server", version="1.0.0")
        self.server_task = None
        self.is_running = False
        
        # Настройка routes
        self.setup_routes()
        
    def setup_routes(self):
        """Настройка HTTP routes"""
        
        @self.app.post("/reload")
        async def reload_bot_config(request: dict):
            """Перезагрузка конфигурации бота"""
            try:
                bot_id = request.get("bot_id")
                action = request.get("action", "updated")
                
                logger.info(f"🔄 Получен webhook: bot_id={bot_id}, action={action}")
                
                if not bot_id:
                    raise HTTPException(status_code=400, detail="bot_id is required")
                
                # Асинхронно обновляем конфигурацию
                asyncio.create_task(self.manager.handle_bot_change(bot_id, action))
                
                return {
                    "status": "success",
                    "message": f"Bot {bot_id} configuration reload requested",
                    "action": action
                }
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки webhook: {e}")
                raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
        
        @self.app.get("/status")
        async def get_manager_status():
            """Получение статуса менеджера"""
            return self.manager.get_stats()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "manager_running": self.manager.is_running,
                "total_bots": len(self.manager.bots),
                "running_bots": len([b for b in self.manager.bots.values() if b.is_running])
            }
    
    async def start(self):
        """Запуск webhook сервера"""
        if self.is_running:
            return
            
        try:
            config = uvicorn.Config(
                self.app,
                host="0.0.0.0",
                port=self.port,
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            
            # Запуск в отдельном потоке
            def run_server():
                asyncio.run(server.serve())
            
            self.server_task = threading.Thread(target=run_server, daemon=True)
            self.server_task.start()
            self.is_running = True
            
            logger.info(f"🌐 Webhook сервер запущен на порту {self.port}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска webhook сервера: {e}")
            raise
    
    async def stop(self):
        """Остановка webhook сервера"""
        if not self.is_running:
            return
            
        try:
            # Остановка сервера
            if self.server_task and self.server_task.is_alive():
                self.server_task.join(timeout=5)
            
            self.is_running = False
            logger.info("🛑 Webhook сервер остановлен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки webhook сервера: {e}")

# === ОБНОВЛЕННЫЙ MULTIBOTMANAGER ===

class MultiBotManager:
    """Менеджер для управления множественными ботами"""
    
    def __init__(self, backend_api_url: str = "http://localhost:8000", webhook_port: int = 8001):
        self.backend_api_url = backend_api_url
        self.bots: Dict[int, BotInstance] = {}
        self.is_running = False
        self.last_config_check = 0
        self.config_check_interval = 60  # Проверка каждые 60 секунд
        
        # Создание директорий
        os.makedirs("logs", exist_ok=True)
        os.makedirs("session", exist_ok=True)
        
        # Инициализация webhook сервера
        self.webhook_server = WebhookServer(self, webhook_port)
        
        logger.info(f"🚀 Инициализирован MultiBotManager с Backend API: {backend_api_url}")
        logger.info(f"🌐 Webhook сервер будет запущен на порту {webhook_port}")
    
    async def get_active_bots(self) -> List[BotConfig]:
        """Получение активных ботов из Backend API с retry логикой"""
        for attempt in range(3):  # Retry 3 раза
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.backend_api_url}/api/public-bots",
                        params={"status": "active"}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            bots = []
                            for bot_data in data:
                                bot_config = BotConfig(
                                    bot_id=bot_data["id"],
                                    name=bot_data["name"],
                                    bot_token=bot_data["bot_token"],
                                    status=bot_data["status"],
                                    welcome_message=bot_data.get("welcome_message", ""),
                                    categorization_prompt=bot_data.get("categorization_prompt", ""),
                                    summarization_prompt=bot_data.get("summarization_prompt", ""),
                                    max_posts_per_digest=bot_data.get("max_posts_per_digest", 15),
                                    max_summary_length=bot_data.get("max_summary_length", 200),
                                    created_at=bot_data.get("created_at", ""),
                                    updated_at=bot_data.get("updated_at", "")
                                )
                                bots.append(bot_config)
                            
                            logger.info(f"📋 Получено {len(bots)} активных ботов из Backend API")
                            return bots
                        else:
                            logger.error(f"❌ Ошибка API: {response.status}")
                            
            except Exception as e:
                logger.error(f"❌ Попытка {attempt + 1}/3 получения ботов: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("❌ Не удалось получить список активных ботов")
        return []
    
    async def start_bot(self, config: BotConfig) -> bool:
        """Запуск отдельного бота"""
        try:
            if config.bot_id in self.bots:
                logger.warning(f"⚠️ Бот {config.bot_id} уже существует")
                return False
            
            # Создание экземпляра бота
            bot_instance = BotInstance(config, self.backend_api_url)
            
            # Запуск бота
            success = await bot_instance.start()
            if success:
                self.bots[config.bot_id] = bot_instance
                logger.info(f"✅ Запущен бот {config.bot_id}: {config.name}")
                return True
            else:
                logger.error(f"❌ Не удалось запустить бот {config.bot_id}: {config.name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота {config.bot_id}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def stop_bot(self, bot_id: int):
        """Остановка конкретного бота"""
        try:
            if bot_id not in self.bots:
                logger.warning(f"⚠️ Бот {bot_id} не найден")
                return
            
            bot_instance = self.bots[bot_id]
            await bot_instance.stop()
            del self.bots[bot_id]
            
            logger.info(f"🛑 Остановлен бот {bot_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота {bot_id}: {e}")
            logger.error(traceback.format_exc())
    
    async def restart_bot(self, bot_id: int):
        """Перезапуск конкретного бота"""
        logger.info(f"🔄 Перезапуск бота {bot_id}")
        
        # Остановка
        await self.stop_bot(bot_id)
        
        # Получение свежей конфигурации и запуск
        bots = await self.get_active_bots()
        for bot_config in bots:
            if bot_config.bot_id == bot_id:
                await self.start_bot(bot_config)
                break
    
    async def sync_bots(self):
        """Синхронизация ботов с Backend API"""
        try:
            active_bots = await self.get_active_bots()
            active_bot_ids = {bot.bot_id for bot in active_bots}
            current_bot_ids = set(self.bots.keys())
            
            # Останавливаем боты, которые больше не активны
            for bot_id in current_bot_ids - active_bot_ids:
                logger.info(f"🛑 Останавливаем неактивный бот {bot_id}")
                await self.stop_bot(bot_id)
            
            # Запускаем новые боты
            for bot_config in active_bots:
                if bot_config.bot_id not in current_bot_ids:
                    logger.info(f"🚀 Запускаем новый бот {bot_config.bot_id}: {bot_config.name}")
                    await self.start_bot(bot_config)
            
            logger.info(f"🔄 Синхронизация завершена: {len(self.bots)} активных ботов")
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации ботов: {e}")
            logger.error(traceback.format_exc())
    
    async def start_all(self):
        """Запуск всех активных ботов"""
        logger.info("🚀 Запуск MultiBotManager...")
        
        self.is_running = True
        
        # Запуск webhook сервера
        await self.webhook_server.start()
        
        # Получение и запуск всех активных ботов
        await self.sync_bots()
        
        # Запуск фонового мониторинга
        asyncio.create_task(self._background_monitor())
        
        logger.info(f"✅ MultiBotManager запущен с {len(self.bots)} ботами")
    
    async def stop_all(self):
        """Остановка всех ботов"""
        logger.info("🛑 Остановка MultiBotManager...")
        
        self.is_running = False
        
        # Остановка webhook сервера
        await self.webhook_server.stop()
        
        # Остановка всех ботов
        for bot_id in list(self.bots.keys()):
            await self.stop_bot(bot_id)
        
        logger.info("✅ MultiBotManager остановлен")

    async def handle_bot_change(self, bot_id: int, action: str):
        """Обработка изменения конфигурации бота (вызывается вебхуком/планово)."""
        try:
            logger.info(f"🔄 Обработка изменения бота {bot_id}: {action}")
            if action == "deleted":
                await self.stop_bot(bot_id)
                logger.info(f"🗑️ Бот {bot_id} удален")
            elif action in ["created", "updated", "status_changed"]:
                await self.sync_bots()
                logger.info(f"🔄 Конфигурация бота {bot_id} обновлена")
            else:
                logger.warning(f"⚠️ Неизвестное действие: {action}")
        except Exception as e:
            logger.error(f"❌ Ошибка обработки изменения бота {bot_id}: {e}")
    
    async def _background_monitor(self):
        """Фоновый мониторинг и синхронизация"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config_check_interval)
                
                if time.time() - self.last_config_check > self.config_check_interval:
                    await self.sync_bots()
                    self.last_config_check = time.time()
                    
            except Exception as e:
                logger.error(f"❌ Ошибка фонового мониторинга: {e}")
                await asyncio.sleep(10)  # Короткая пауза при ошибке
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение общей статистики"""
        stats = {
            "manager_running": self.is_running,
            "total_bots": len(self.bots),
            "running_bots": sum(1 for bot in self.bots.values() if bot.is_running),
            "total_messages": sum(bot.message_count for bot in self.bots.values()),
            "total_errors": sum(bot.error_count for bot in self.bots.values()),
            "bots": [bot.get_stats() for bot in self.bots.values()]
        }
        return stats
    
    def print_status(self):
        """Вывод статуса всех ботов"""
        stats = self.get_stats()
        
        print("\n" + "="*50)
        print("📊 СТАТУС MULTIBOTMANAGER")
        print("="*50)
        print(f"🔄 Менеджер запущен: {'✅' if stats['manager_running'] else '❌'}")
        print(f"🤖 Всего ботов: {stats['total_bots']}")
        print(f"🟢 Активных ботов: {stats['running_bots']}")
        print(f"📨 Всего сообщений: {stats['total_messages']}")
        print(f"❌ Всего ошибок: {stats['total_errors']}")
        print()
        
        for bot_stats in stats['bots']:
            status_icon = "🟢" if bot_stats['is_running'] else "🔴"
            uptime = f"{bot_stats['uptime_seconds']:.0f}s" if bot_stats['uptime_seconds'] > 0 else "N/A"
            print(f"{status_icon} ID {bot_stats['bot_id']}: {bot_stats['name']} | "
                  f"Uptime: {uptime} | "
                  f"Messages: {bot_stats['message_count']} | "
                  f"Errors: {bot_stats['error_count']}")
        
        print("="*50)

# Пример использования
async def main():
    """Основная функция для тестирования"""
    # Определяем адрес Backend из переменных окружения (по умолчанию docker service name)
    backend_api_url = os.getenv("BACKEND_API_URL", "http://backend:8000")
    manager = MultiBotManager(backend_api_url=backend_api_url)
    
    try:
        # Запуск всех ботов
        await manager.start_all()
        
        # Ожидание и периодический вывод статуса
        while True:
            await asyncio.sleep(30)
            manager.print_status()
            
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    finally:
        await manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main()) 