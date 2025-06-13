from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from loguru import logger

# Загрузка переменных окружения
load_dotenv()

class AIServiceConfig(BaseModel):
    """Базовая конфигурация для AI сервисов"""
    model_name: str = Field(default="gpt-4")
    max_tokens: int = Field(default=4000)
    temperature: float = Field(default=0.7)
    timeout: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    retry_delay: int = Field(default=5)

class SummarizationConfig(AIServiceConfig):
    """Конфигурация для сервиса суммаризации"""
    max_summary_length: int = Field(default=150)
    min_summary_length: int = Field(default=50)
    language: str = Field(default="ru")
    tone: str = Field(default="neutral")  # neutral, formal, casual
    custom_prompt: Optional[str] = None

class CategorizationConfig(AIServiceConfig):
    """Конфигурация для сервиса категоризации"""
    min_confidence: float = Field(default=0.7)
    max_categories: int = Field(default=3)
    use_binary_relevance: bool = Field(default=True)
    quality_threshold: float = Field(default=0.6)
    custom_prompt: Optional[str] = None

class BotConfig(BaseModel):
    """Конфигурация для отдельного бота"""
    bot_id: int
    name: str
    description: Optional[str] = None
    ai_prompt: Optional[str] = None
    summarization: SummarizationConfig = Field(default_factory=SummarizationConfig)
    categorization: CategorizationConfig = Field(default_factory=CategorizationConfig)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DatabaseConfigManager:
    """Менеджер конфигурации с загрузкой из базы данных через API"""
    
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        self.cache: Dict[int, Dict[str, Any]] = {}
        self.global_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 минут
        self.last_cache_update = {}
    
    async def get_bot_settings(self, bot_id: int) -> Dict[str, Any]:
        """Получение настроек бота из базы через API с кешированием"""
        try:
            # Проверяем кеш
            if self._is_cache_valid(bot_id):
                logger.debug(f"Используем кешированные настройки для бота {bot_id}")
                return self.cache.get(bot_id, {})
            
            # Загружаем из API
            async with aiohttp.ClientSession() as session:
                url = f"{self.backend_url}/api/ai-settings/bot/{bot_id}/parsed"
                async with session.get(url) as response:
                    if response.status == 200:
                        settings = await response.json()
                        self.cache[bot_id] = settings
                        self.last_cache_update[bot_id] = datetime.now()
                        logger.info(f"Загружены настройки для бота {bot_id}: {len(settings)} параметров")
                        return settings
                    else:
                        logger.error(f"Ошибка загрузки настроек для бота {bot_id}: {response.status}")
                        return self._get_fallback_settings()
                        
        except Exception as e:
            logger.error(f"Ошибка при получении настроек бота {bot_id}: {str(e)}")
            return self._get_fallback_settings()
    
    async def get_global_settings(self) -> Dict[str, Any]:
        """Получение глобальных настроек"""
        try:
            # Проверяем кеш
            if self._is_global_cache_valid():
                logger.debug("Используем кешированные глобальные настройки")
                return self.global_cache
            
            # Загружаем из API
            async with aiohttp.ClientSession() as session:
                url = f"{self.backend_url}/api/ai-settings?is_active=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        settings_list = await response.json()
                        
                        # Преобразуем в словарь настроек
                        settings = {}
                        for setting in settings_list:
                            if setting.get('public_bot_id') is None:  # Только глобальные
                                key = setting['setting_key']
                                value = self._parse_setting_value(
                                    setting['setting_value'], 
                                    setting['setting_type']
                                )
                                settings[key] = value
                        
                        self.global_cache = settings
                        self.last_cache_update['global'] = datetime.now()
                        logger.info(f"Загружены глобальные настройки: {len(settings)} параметров")
                        return settings
                    else:
                        logger.error(f"Ошибка загрузки глобальных настроек: {response.status}")
                        return self._get_fallback_settings()
                        
        except Exception as e:
            logger.error(f"Ошибка при получении глобальных настроек: {str(e)}")
            return self._get_fallback_settings()
    
    def _is_cache_valid(self, bot_id: int) -> bool:
        """Проверка валидности кеша для бота"""
        if bot_id not in self.cache or bot_id not in self.last_cache_update:
            return False
        
        time_diff = (datetime.now() - self.last_cache_update[bot_id]).total_seconds()
        return time_diff < self.cache_ttl
    
    def _is_global_cache_valid(self) -> bool:
        """Проверка валидности глобального кеша"""
        if not self.global_cache or 'global' not in self.last_cache_update:
            return False
        
        time_diff = (datetime.now() - self.last_cache_update['global']).total_seconds()
        return time_diff < self.cache_ttl
    
    def _parse_setting_value(self, value: str, setting_type: str) -> Any:
        """Парсинг значения настройки согласно типу"""
        if not value:
            return None
            
        if setting_type == "integer":
            return int(value)
        elif setting_type == "float":
            return float(value)
        elif setting_type == "boolean":
            return value.lower() in ('true', '1', 'yes', 'on')
        elif setting_type == "json":
            import json
            return json.loads(value)
        else:
            return value
    
    def _get_fallback_settings(self) -> Dict[str, Any]:
        """Fallback настройки из переменных окружения"""
        return {
            'ai_model': os.getenv("AI_MODEL", "gpt-4"),
            'max_tokens': int(os.getenv("MAX_TOKENS", "4000")),
            'temperature': float(os.getenv("TEMPERATURE", "0.7")),
            'max_summary_length': int(os.getenv("MAX_SUMMARY_LENGTH", "150")),
            'min_summary_length': int(os.getenv("MIN_SUMMARY_LENGTH", "50")),
            'default_language': os.getenv("DEFAULT_LANGUAGE", "ru"),
            'default_tone': os.getenv("DEFAULT_TONE", "neutral"),
            'min_confidence': float(os.getenv("MIN_CONFIDENCE", "0.7")),
            'quality_threshold': float(os.getenv("QUALITY_THRESHOLD", "0.6")),
            'timeout': int(os.getenv("TIMEOUT", "30")),
            'retry_attempts': int(os.getenv("RETRY_ATTEMPTS", "3")),
            'retry_delay': int(os.getenv("RETRY_DELAY", "5")),
        }
    
    async def create_bot_config(self, bot_id: int) -> BotConfig:
        """Создание конфигурации бота на основе настроек из БД"""
        settings = await self.get_bot_settings(bot_id)
        
        return BotConfig(
            bot_id=bot_id,
            name=f"Bot {bot_id}",
            summarization=SummarizationConfig(
                model_name=settings.get('ai_model', 'gpt-4'),
                max_tokens=settings.get('max_tokens', 4000),
                temperature=settings.get('temperature', 0.7),
                max_summary_length=settings.get('max_summary_length', 150),
                min_summary_length=settings.get('min_summary_length', 50),
                language=settings.get('default_language', 'ru'),
                tone=settings.get('default_tone', 'neutral'),
                timeout=settings.get('timeout', 30),
                retry_attempts=settings.get('retry_attempts', 3),
                retry_delay=settings.get('retry_delay', 5),
                custom_prompt=settings.get('default_summarization_prompt')
            ),
            categorization=CategorizationConfig(
                model_name=settings.get('ai_model', 'gpt-4'),
                max_tokens=settings.get('max_tokens', 4000),
                temperature=settings.get('temperature', 0.7),
                min_confidence=settings.get('min_confidence', 0.7),
                max_categories=settings.get('max_categories', 3),
                use_binary_relevance=settings.get('use_binary_relevance', True),
                quality_threshold=settings.get('quality_threshold', 0.6),
                timeout=settings.get('timeout', 30),
                retry_attempts=settings.get('retry_attempts', 3),
                retry_delay=settings.get('retry_delay', 5),
                custom_prompt=settings.get('default_categorization_prompt')
            )
        )
    
    def invalidate_cache(self, bot_id: Optional[int] = None):
        """Инвалидация кеша"""
        if bot_id:
            self.cache.pop(bot_id, None)
            self.last_cache_update.pop(bot_id, None)
        else:
            self.cache.clear()
            self.last_cache_update.clear()
            self.global_cache.clear()

# Создаем глобальный экземпляр менеджера конфигурации
config_manager = DatabaseConfigManager()

# Старый менеджер конфигурации для совместимости
class ConfigManager:
    """DEPRECATED: Используйте DatabaseConfigManager"""
    
    def __init__(self):
        self.bots: Dict[int, BotConfig] = {}
        self.default_config = BotConfig(
            bot_id=0,
            name="default",
            description="Default configuration for all bots"
        )
    
    def get_bot_config(self, bot_id: int) -> BotConfig:
        """Получение конфигурации для конкретного бота"""
        return self.bots.get(bot_id, self.default_config)
    
    def update_bot_config(self, bot_config: BotConfig) -> None:
        """Обновление конфигурации бота"""
        self.bots[bot_config.bot_id] = bot_config
        bot_config.updated_at = datetime.now()
    
    def delete_bot_config(self, bot_id: int) -> None:
        """Удаление конфигурации бота"""
        if bot_id in self.bots:
            del self.bots[bot_id]
    
    def get_all_bots(self) -> Dict[int, BotConfig]:
        """Получение конфигураций всех ботов"""
        return self.bots.copy()

# Функция для получения секретов из .env (только для секретных данных)
def get_secret(key: str, default: str = None) -> str:
    """Получение секретных данных из .env файла"""
    value = os.getenv(key, default)
    if not value and not default:
        raise ValueError(f"Secret '{key}' not found in environment variables")
    return value 