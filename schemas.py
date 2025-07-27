"""
🎯 SCHEMAS.PY - ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ ДЛЯ ВСЕХ СТРУКТУР ДАННЫХ
=================================================================

Этот файл содержит ВСЕ Pydantic модели проекта MorningStarBot3.
ЗАПРЕЩЕНО создавать новые Pydantic модели в других файлах!

Принципы:
1. Единые названия полей по всему проекту
2. Базовые модели + наследование для специализации  
3. Стандартизированные типы данных
4. Решение всех конфликтов из analysis_conflicts.md
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# ==================== ENUM'Ы ====================

class ProcessingStatus(str, Enum):
    """Статусы обработки постов"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class BotStatus(str, Enum):
    """Статусы публичных ботов"""
    SETUP = "setup"
    ACTIVE = "active"
    PAUSED = "paused"
    DEVELOPMENT = "development"

# ==================== БАЗОВЫЕ МОДЕЛИ ====================

class TimestampMixin(BaseModel):
    """Миксин для полей времени"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Category(TimestampMixin):
    """Категория - ЕДИНАЯ схема для всех компонентов"""
    id: Optional[int] = None  # None при создании, int из БД
    name: str = Field(..., min_length=1, max_length=255)  # ВЕЗДЕ name, НЕ category_name!
    description: Optional[str] = None  # НЕ optional - нужно для AI, но может быть None
    emoji: str = Field("📝", max_length=10) 
    is_active: bool = True  # 🔧 ОСТАВЛЯЕМ is_active - для Category это оправдано (просто вкл/выкл)
    ai_prompt: Optional[str] = None
    sort_order: int = 0

class Channel(TimestampMixin):
    """Канал - ЕДИНАЯ схема"""
    id: Optional[int] = None
    channel_name: str = Field(..., min_length=1, max_length=255)  # Основное поле
    username: Optional[str] = None
    telegram_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)  # BigInteger поддержка
    title: Optional[str] = None  # Опционально, основное поле channel_name 
    description: Optional[str] = None
    is_active: bool = True  # 🔧 ОСТАВЛЯЕМ is_active - для Channel это оправдано (просто вкл/выкл)
    last_parsed: Optional[datetime] = None
    error_count: int = 0

# ==================== POST МОДЕЛИ (решение конфликтов №1 и №2) ====================

class PostBase(BaseModel):
    """Базовая модель поста - общие поля"""
    channel_telegram_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)
    telegram_message_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)
    title: Optional[str] = None
    content: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)  # 🔧 РЕШЕНИЕ КОНФЛИКТА №2: стандартизировано
    views: int = 0
    post_date: datetime  # 🔧 ПОДТВЕРЖДЕНО: используем post_date, НЕ published_at
    userbot_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('media_urls', pre=True, always=True)
    def validate_media_urls(cls, v):
        """Унифицированный валидатор для media_urls"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except:
                return []
        return v if isinstance(v, list) else []

class PostRaw(PostBase):
    """Модель для сырых постов от userbot (без AI обработки)"""
    collected_at: datetime
    retention_until: Optional[datetime] = None

class PostDB(PostBase, TimestampMixin):
    """Модель поста для БД (posts_cache)"""
    id: int
    collected_at: datetime
    retention_until: Optional[datetime] = None

class PostForCategorization(PostBase):
    """Модель поста для AI категоризации"""
    id: int
    public_bot_id: int

class PostForSummarization(PostBase):
    """Модель поста для AI суммаризации"""
    id: int  
    public_bot_id: int
    categories: List[str] = Field(default_factory=list)  # Результат категоризации

# ==================== PUBLIC BOT МОДЕЛИ (решение конфликтов №3 и №4) ====================  

class PublicBotBase(BaseModel):
    """Базовая модель публичного бота"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: BotStatus = BotStatus.SETUP  # 🔧 ENUM для ботов - нужны сложные состояния (setup→active→paused→development)
    default_language: str = "ru"

class PublicBotConfig(PublicBotBase):
    """Конфигурация бота (для Backend API)"""
    # Telegram Bot данные
    bot_token: Optional[str] = None
    welcome_message: Optional[str] = None
    
    # Digest Settings
    max_posts_per_digest: int = Field(10, ge=1, le=100)
    max_summary_length: int = Field(150, ge=50, le=2000)
    
    # AI Prompts
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    
    # Расписание доставки
    delivery_schedule: Dict[str, Any] = Field(default_factory=dict)
    timezone: str = "Europe/Moscow"
    
    # Legacy поля
    digest_generation_time: str = Field("09:00", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    digest_schedule: Dict[str, Any] = Field(default_factory=lambda: {"enabled": False})

class PublicBotDB(PublicBotConfig, TimestampMixin):
    """Модель бота для БД"""
    id: int
    users_count: int = 0
    digests_count: int = 0
    channels_count: int = 0
    topics_count: int = 0

class PublicBotForAI(PublicBotBase):
    """Упрощенная модель бота для AI сервисов"""  
    id: int
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)

# ==================== AI РЕЗУЛЬТАТЫ ====================

class ProcessedData(TimestampMixin):
    """Результаты AI обработки - мультитенантные"""
    id: Optional[int] = None
    post_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)
    public_bot_id: int
    
    # AI результаты
    summaries: Dict[str, str] = Field(default_factory=dict)  # {"ru": "summary", "en": "summary"}
    categories: List[Dict[str, Any]] = Field(default_factory=list)  # [{"name": "Политика", "relevance": 0.95}]
    
    # Метрики
    importance: float = Field(default=0.0, ge=0.0, le=10.0)
    urgency: float = Field(default=0.0, ge=0.0, le=10.0)
    significance: float = Field(default=0.0, ge=0.0, le=10.0)
    tokens_used: int = Field(default=0, ge=0)
    processing_time: float = Field(default=0.0, ge=0.0)
    
    # Статусы и метаданные
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_version: str = "v3.1"
    is_categorized: bool = False
    is_summarized: bool = False
    ai_metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceResult(TimestampMixin):
    """Результат работы отдельного AI сервиса"""
    id: Optional[int] = None
    post_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)
    public_bot_id: int
    service_name: str  # "categorization", "summarization", etc.
    status: ProcessingStatus = ProcessingStatus.PENDING
    payload: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    processed_at: Optional[datetime] = None

# ==================== ПОЛЬЗОВАТЕЛИ И ПОДПИСКИ ====================

class User(TimestampMixin):
    """Пользователь Telegram бота"""
    id: Optional[int] = None
    telegram_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "ru"
    is_active: bool = True  # 🔧 is_active для User - просто заблокирован/разблокирован

class Subscription(TimestampMixin):
    """Подписка пользователя на категорию"""
    id: Optional[int] = None
    user_telegram_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)
    category_id: int
    public_bot_id: int

# ==================== КОНФИГУРАЦИЯ ====================

class ConfigSetting(TimestampMixin):
    """Системная настройка"""
    id: Optional[int] = None
    key: str = Field(..., min_length=1, max_length=255)
    value: Optional[str] = None
    value_type: str = Field("string", pattern=r"^(string|integer|boolean|float|json)$")
    category: Optional[str] = None
    description: Optional[str] = None
    is_editable: bool = True

# ==================== ВАЛИДАТОРЫ ====================
# Все валидаторы перенесены внутрь соответствующих классов
# См. PostBase.validate_media_urls()

# ==================== ПРАВИЛА ИСПОЛЬЗОВАНИЯ ====================
"""
КРИТИЧЕСКИ ВАЖНО:

1. ВСЕ структуры данных описаны в ЭТОМ файле
2. ЗАПРЕЩЕНО создавать новые Pydantic модели в других файлах  
3. Если нужно новое поле - добавь в этот файл
4. Используй наследование схем:
   - PostBase → PostRaw, PostDB, PostForCategorization, PostForSummarization
   - PublicBotBase → PublicBotConfig, PublicBotDB, PublicBotForAI
5. При передаче данных между модулями ВСЕГДА используй .model_dump(mode='json'):
   post.model_dump(mode='json') → в CELERY → Post(**data)

ПРИМЕР ПРАВИЛЬНОГО ИСПОЛЬЗОВАНИЯ:
from schemas import PostForCategorization
post = PostForCategorization(**data)
# Для Celery (КРИТИЧНО mode='json' для datetime → ISO строки!):
celery_data = post.model_dump(mode='json')  # НЕ .dict()!

НЕПРАВИЛЬНО:
class MyPost(BaseModel):  # НЕ создавай новые модели!
    ...
post.dict()  # УСТАРЕЛО в Pydantic v2!

РЕШЕННЫЕ КОНФЛИКТЫ:
✅ Конфликт №1: Объединены PostData и PostCacheBase через наследование
✅ Конфликт №2: Стандартизирован media_urls: List[str] = Field(default_factory=list)  
✅ Конфликт №3: ГИБРИДНЫЙ подход к статусам - enum для ботов (сложные состояния), is_active для Category/Channel (простое вкл/выкл)
✅ Конфликт №4: Объединены PublicBot модели через наследование
""" 