from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Table, Float, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, Any, Union
import json
from urllib.parse import quote_plus

# Загрузка переменных окружения
load_dotenv()

# Конфигурация базы данных
DB_HOST = "127.0.0.1"  # Принудительно IPv4 вместо localhost
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "digest_bot")
DB_USER = os.getenv("DB_USER", "digest_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Demiurg12@")  # Правильный дефолт

# URL кодирование пароля для специальных символов
encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Fallback к SQLite если PostgreSQL недоступен
SQLITE_FALLBACK = f"sqlite:///{os.path.dirname(os.path.abspath(__file__))}/morningstar.db"

# Определяем тип БД для выбора правильных типов данных
USE_POSTGRESQL = False

try:
    test_engine = create_engine(DATABASE_URL, echo=False)
    # Тестируем соединение
    with test_engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("SELECT 1"))
    print(f"✅ Подключен к PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    USE_POSTGRESQL = True
    engine = test_engine
except Exception as e:
    print(f"⚠️ PostgreSQL недоступен: {str(e)[:100]}...")
    print("🔄 Переключаемся на SQLite fallback")
    DATABASE_URL = SQLITE_FALLBACK
    USE_POSTGRESQL = False
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI приложение
app = FastAPI(
    title="MorningStar Admin API",
    description="API для админ-панели MorningStar Bot",
    version="1.0.0"
)

# CORS middleware для админ-панели
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели SQLAlchemy
channel_categories = Table(
    'channel_categories', Base.metadata,
    Column('channel_id', Integer, ForeignKey('channels.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False)  # Изменено: name → category_name
    description = Column(Text)
    # emoji = Column(String, default="📝")  # Убрано: нет в БД
    is_active = Column(Boolean, default=True)
    # ai_prompt = Column(Text)  # Убрано: нет в БД
    # sort_order = Column(Integer, default=0)  # Убрано: нет в БД
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    channels = relationship("Channel", secondary=channel_categories, back_populates="categories")

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String, nullable=False)  # Добавлено поле для совместимости с БД
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    title = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    last_parsed = Column(DateTime)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    categories = relationship("Category", secondary=channel_categories, back_populates="channels")

class ConfigSetting(Base):
    __tablename__ = "config_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String, default="string")  # string, integer, boolean, float, json
    category = Column(String)
    description = Column(Text)
    is_editable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Digest(Base):
    __tablename__ = "digests"
    
    id = Column(Integer, primary_key=True, index=True)
    digest_id = Column(String, unique=True, nullable=False, index=True)  # digest_timestamp от N8N
    total_posts = Column(Integer, default=0)
    channels_processed = Column(Integer, default=0)
    original_posts = Column(Integer, default=0)
    relevant_posts = Column(Integer, default=0)
    avg_importance = Column(Float, default=0.0)
    avg_urgency = Column(Float, default=0.0)
    avg_significance = Column(Float, default=0.0)
    binary_relevance_applied = Column(Boolean, default=False)
    with_metrics = Column(Boolean, default=False)
    digest_data = Column(Text)  # JSON данные полного дайджеста
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Таблица связи пользователей и категорий (подписки)
user_subscriptions = Table(
    'user_subscriptions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    language_code = Column(String, default="ru")
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    # ВРЕМЕННО ОТКЛЮЧЕНО: subscribed_categories = relationship("Category", secondary=user_subscriptions, back_populates="subscribers")

class PublicBot(Base):
    __tablename__ = "public_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="setup")  # setup, active, paused
    
    # Telegram Bot данные
    bot_token = Column(String)
    welcome_message = Column(Text)
    default_language = Column(String, default="ru")
    
    # Digest Settings (базовые)
    max_posts_per_digest = Column(Integer, default=10)
    max_summary_length = Column(Integer, default=150)
    
    # AI Prompts (разделенные по функциям)
    categorization_prompt = Column(Text)
    summarization_prompt = Column(Text)
    
    # СЛОЖНОЕ РАСПИСАНИЕ ДОСТАВКИ
    delivery_schedule = Column(JSONB if USE_POSTGRESQL else Text, default={} if USE_POSTGRESQL else "{}")
    timezone = Column(String, default="Europe/Moscow")
    
    # Legacy поля для совместимости
    digest_generation_time = Column(String, default="09:00")
    digest_schedule = Column(String, default="daily")
    
    # Statistics
    users_count = Column(Integer, default=0)
    digests_count = Column(Integer, default=0)
    channels_count = Column(Integer, default=0)
    topics_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи Many-to-Many
    bot_channels = relationship("BotChannel", back_populates="public_bot", cascade="all, delete-orphan")
    bot_categories = relationship("BotCategory", back_populates="public_bot", cascade="all, delete-orphan")

class BotChannel(Base):
    """Таблица связей бот-канал с дополнительными параметрами"""
    __tablename__ = "bot_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    public_bot_id = Column(Integer, ForeignKey("public_bots.id", ondelete="CASCADE"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Float, default=1.0)  # Приоритет канала для данного бота (0.1-2.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Связи
    public_bot = relationship("PublicBot", back_populates="bot_channels")
    channel = relationship("Channel")
    
    # Уникальность связи бот-канал
    __table_args__ = (UniqueConstraint('public_bot_id', 'channel_id', name='uq_bot_channel'),)

class BotCategory(Base):
    """Таблица связей бот-категория с дополнительными параметрами"""
    __tablename__ = "bot_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    public_bot_id = Column(Integer, ForeignKey("public_bots.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    custom_ai_instructions = Column(Text)  # Специфические AI инструкции для категории в этом боте
    weight = Column(Float, default=1.0)  # Приоритет категории для данного бота
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Связи
    public_bot = relationship("PublicBot", back_populates="bot_categories")
    category = relationship("Category")
    
    # Уникальность связи бот-категория
    __table_args__ = (UniqueConstraint('public_bot_id', 'category_id', name='uq_bot_category'),)

class PostCache(Base):
    __tablename__ = "posts_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_telegram_id = Column(Integer, nullable=False, index=True)
    telegram_message_id = Column(Integer, nullable=False)
    title = Column(Text)
    content = Column(Text)
    # Условные типы данных в зависимости от БД
    media_urls = Column(JSONB if USE_POSTGRESQL else Text, default=[] if USE_POSTGRESQL else "[]")
    views = Column(Integer, default=0)
    post_date = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, default=func.now(), nullable=False)
    userbot_metadata = Column(JSONB if USE_POSTGRESQL else Text, default={} if USE_POSTGRESQL else "{}")
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed

# Обновляем модель Category для связи с пользователями
# ВРЕМЕННО ОТКЛЮЧЕНО ДО ИСПРАВЛЕНИЯ СТРУКТУРЫ ТАБЛИЦЫ user_subscriptions:
# Category.subscribers = relationship("User", secondary=user_subscriptions, back_populates="subscribed_categories")

# ВРЕМЕННО ОТКЛЮЧАЕМ СВЯЗЬ В USER МОДЕЛИ:
# subscribed_categories = relationship("Category", secondary=user_subscriptions, back_populates="subscribers")

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Функция для создания начальных настроек
def create_default_settings():
    """Создать начальные настройки системы"""
    db = SessionLocal()
    try:
        # Получаем список существующих ключей настроек
        existing_keys = {setting.key for setting in db.query(ConfigSetting).all()}
        print(f"Найдено существующих настроек: {len(existing_keys)}")
        print(f"Существующие ключи: {existing_keys}")
        
        default_settings = [
            {
                "key": "CHECK_INTERVAL",
                "value": "30",
                "value_type": "integer",
                "category": "system",
                "description": "Интервал проверки каналов в минутах",
                "is_editable": True
            },
            {
                "key": "MAX_POSTS_PER_DIGEST",
                "value": "10",
                "value_type": "integer",
                "category": "digest",
                "description": "Максимальное количество постов в дайджесте",
                "is_editable": True
            },
            {
                "key": "DIGEST_GENERATION_TIME",
                "value": "09:00",
                "value_type": "string",
                "category": "digest",
                "description": "Время генерации дайджестов",
                "is_editable": True
            },
            {
                "key": "AI_MODEL",
                "value": "gpt-4",
                "value_type": "string",
                "category": "ai",
                "description": "Модель AI для обработки контента",
                "is_editable": True
            },
            {
                "key": "MAX_SUMMARY_LENGTH",
                "value": "150",
                "value_type": "integer",
                "category": "ai",
                "description": "Максимальная длина summary в символах",
                "is_editable": True
            },
            {
                "key": "ENABLE_NOTIFICATIONS",
                "value": "true",
                "value_type": "boolean",
                "category": "system",
                "description": "Включить уведомления администратора",
                "is_editable": True
            },
            {
                "key": "LOG_LEVEL",
                "value": "INFO",
                "value_type": "string",
                "category": "system",
                "description": "Уровень логирования (DEBUG, INFO, WARNING, ERROR)",
                "is_editable": True
            },
            {
                "key": "BACKUP_RETENTION_DAYS",
                "value": "30",
                "value_type": "integer",
                "category": "system",
                "description": "Количество дней хранения резервных копий",
                "is_editable": True
            },
            {
                "key": "COLLECTION_DEPTH_DAYS",
                "value": "3",
                "value_type": "integer",
                "category": "system",
                "description": "Сколько дней назад собирать посты из каналов",
                "is_editable": True
            },
            {
                "key": "MAX_POSTS_PER_CHANNEL",
                "value": "50",
                "value_type": "integer",
                "category": "system",
                "description": "Максимальное количество постов с одного канала",
                "is_editable": True
            },
            {
                "key": "MAX_POSTS_FOR_AI_ANALYSIS",
                "value": "10",
                "value_type": "integer",
                "category": "ai",
                "description": "Максимальное количество постов для AI анализа",
                "is_editable": True
            }
        ]
        
        # Добавляем только отсутствующие настройки
        added_count = 0
        for setting_data in default_settings:
            if setting_data["key"] not in existing_keys:
                db_setting = ConfigSetting(**setting_data)
                db.add(db_setting)
                added_count += 1
                print(f"Добавлена настройка: {setting_data['key']}")
        
        if added_count > 0:
            db.commit()
            print(f"Добавлено {added_count} новых настроек")
        else:
            print("Все настройки уже существуют")
        
    except Exception as e:
        print(f"Ошибка при создании начальных настроек: {e}")
        db.rollback()
    finally:
        db.close()

# Создаем начальные настройки при запуске
create_default_settings()

# Pydantic модели
class CategoryBase(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=255)  # Изменено: name → category_name
    description: Optional[str] = None
    # emoji: str = Field("📝", max_length=10)  # Убрано: нет в БД
    is_active: bool = True
    # ai_prompt: Optional[str] = None  # Убрано: нет в БД
    # sort_order: int = 0  # Убрано: нет в БД

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChannelBase(BaseModel):
    channel_name: str = Field(..., min_length=1, max_length=255)  # Основное поле для БД
    telegram_id: int
    username: Optional[str] = None
    title: Optional[str] = None  # Сделано опциональным, т.к. используем channel_name
    description: Optional[str] = None
    is_active: bool = True

class ChannelCreate(ChannelBase):
    pass

class ChannelUpdate(ChannelBase):
    pass

class ChannelResponse(ChannelBase):
    id: int
    last_parsed: Optional[datetime] = None
    error_count: int = 0
    created_at: datetime
    updated_at: datetime
    categories: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True

class ConfigSettingBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: Optional[str] = None
    value_type: str = Field("string", pattern="^(string|integer|boolean|float|json)$")
    category: Optional[str] = None
    description: Optional[str] = None
    is_editable: bool = True

class ConfigSettingCreate(ConfigSettingBase):
    pass

class ConfigSettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    is_editable: Optional[bool] = None

class ConfigSettingResponse(ConfigSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Pydantic модели для дайджестов
class DigestCreate(BaseModel):
    digest_id: str = Field(..., min_length=1, max_length=255)
    total_posts: int = Field(0, ge=0)
    channels_processed: int = Field(0, ge=0)
    original_posts: int = Field(0, ge=0)
    relevant_posts: int = Field(0, ge=0)
    avg_importance: float = Field(0.0, ge=0.0, le=10.0)
    avg_urgency: float = Field(0.0, ge=0.0, le=10.0)
    avg_significance: float = Field(0.0, ge=0.0, le=10.0)
    binary_relevance_applied: bool = False
    with_metrics: bool = False
    digest_data: Optional[str] = None  # JSON строка
    processed_at: Optional[datetime] = None

class DigestResponse(DigestCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DigestSummary(BaseModel):
    """Краткая информация о дайджесте для списка"""
    id: int
    digest_id: str
    total_posts: int
    relevant_posts: int
    channels_processed: int
    avg_importance: float
    processed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "ru"
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_active: Optional[bool] = None
    last_activity: Optional[datetime] = None

class UserResponse(UserBase):
    id: int
    last_activity: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    subscribed_categories: List['CategoryResponse'] = []
    
    class Config:
        from_attributes = True

class SubscriptionRequest(BaseModel):
    category_ids: List[int] = Field(..., description="Список ID категорий для подписки")

class SubscriptionResponse(BaseModel):
    user_id: int
    subscribed_categories: List['CategoryResponse'] = []
    message: str

class PostCacheBase(BaseModel):
    channel_telegram_id: int
    telegram_message_id: int
    title: Optional[str] = None
    content: Optional[str] = None
    media_urls: Optional[List[str]] = []  # Список URL в виде JSONB массива
    views: int = 0
    post_date: datetime
    userbot_metadata: Optional[Dict[str, Any]] = {}  # JSONB объект
    processing_status: str = "pending"

class PostCacheCreate(PostCacheBase):
    pass

class PostCacheResponse(PostCacheBase):
    id: int
    collected_at: datetime

    class Config:
        from_attributes = True

class PostsBatchCreate(BaseModel):
    """Модель для batch создания posts от userbot"""
    timestamp: datetime
    collection_stats: Dict[str, Union[int, List[str]]]
    posts: List[PostCacheCreate]
    channels_metadata: Dict[str, Dict[str, Any]]

class PublicBotBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field("setup", pattern="^(setup|active|paused)$")
    
    # Telegram Bot данные
    bot_token: Optional[str] = None
    welcome_message: Optional[str] = None
    default_language: str = "ru"
    
    # Digest Settings (базовые)
    max_posts_per_digest: int = Field(10, ge=1, le=100)
    max_summary_length: int = Field(150, ge=50, le=500)
    
    # AI Prompts (разделенные по функциям)
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    
    # СЛОЖНОЕ РАСПИСАНИЕ ДОСТАВКИ
    delivery_schedule: Optional[Dict[str, Any]] = {}
    timezone: str = "Europe/Moscow"
    
    # Legacy поля для совместимости
    digest_generation_time: str = Field("09:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    digest_schedule: str = "daily"

class PublicBotCreate(PublicBotBase):
    pass

class PublicBotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(setup|active|paused)$")
    
    # Telegram Bot данные
    bot_token: Optional[str] = None
    welcome_message: Optional[str] = None
    default_language: Optional[str] = None
    
    # Digest Settings (базовые)
    max_posts_per_digest: Optional[int] = Field(None, ge=1, le=100)
    max_summary_length: Optional[int] = Field(None, ge=50, le=500)
    
    # AI Prompts (разделенные по функциям)
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    
    # СЛОЖНОЕ РАСПИСАНИЕ ДОСТАВКИ
    delivery_schedule: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    
    # Legacy поля для совместимости
    digest_generation_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    digest_schedule: Optional[str] = None

class PublicBotResponse(PublicBotBase):
    id: int
    users_count: int = 0
    digests_count: int = 0
    channels_count: int = 0
    topics_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Bot Templates Models
class BotTemplateSettings(BaseModel):
    """Настройки шаблона для новых ботов"""
    # AI Settings
    default_ai_model: str = "gpt-4o-mini"
    default_max_tokens: int = 4000
    default_temperature: float = 0.7
    default_categorization_prompt: str = """Анализируй посты по следующим категориям:
1. НОВОСТИ - политические события, экономика, общественные новости
2. ТЕХНОЛОГИИ - IT, гаджеты, научные открытия  
3. КУЛЬТУРА - искусство, развлечения, спорт
4. ВОЙНА - военные действия, конфликты, оборона

Определи наиболее подходящую категорию для каждого поста."""
    
    default_summarization_prompt: str = """Создавай краткие резюме постов:
- Максимум 2-3 предложения
- Фокус на ключевых фактах
- Нейтральный тон без эмоций
- Указывай источник если важно"""
    
    # Digest Settings
    default_max_posts_per_digest: int = 10
    default_max_summary_length: int = 150
    default_digest_language: str = "ru"
    default_welcome_message: str = "🤖 Добро пожаловать! Этот бот будет присылать вам персонализированные дайджесты новостей."
    
    # Delivery Settings
    default_delivery_schedule: Dict[str, List[str]] = {
        "monday": ["08:00", "19:00"],
        "tuesday": ["08:00", "19:00"], 
        "wednesday": ["08:00", "19:00"],
        "thursday": ["08:00", "19:00"],
        "friday": ["08:00", "19:00"],
        "saturday": ["10:00"],
        "sunday": ["10:00"]
    }
    default_timezone: str = "Europe/Moscow"

class BotTemplateUpdate(BaseModel):
    """Обновление настроек шаблона"""
    # Все поля опциональные для частичного обновления
    default_ai_model: Optional[str] = None
    default_max_tokens: Optional[int] = None
    default_temperature: Optional[float] = None
    default_categorization_prompt: Optional[str] = None
    default_summarization_prompt: Optional[str] = None
    default_max_posts_per_digest: Optional[int] = None
    default_max_summary_length: Optional[int] = None
    default_digest_language: Optional[str] = None
    default_welcome_message: Optional[str] = None
    default_delivery_schedule: Optional[Dict[str, List[str]]] = None
    default_timezone: Optional[str] = None

# ConfigManager класс
class ConfigManager:
    def __init__(self, db: Session):
        self.db = db
        self.env_vars = dict(os.environ)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение конфигурации из .env или БД"""
        # Сначала проверяем .env (приоритет для секретных данных)
        if key in self.env_vars:
            return self.env_vars[key]
        
        # Затем проверяем БД
        db_setting = self.db.query(ConfigSetting).filter(ConfigSetting.key == key).first()
        if db_setting:
            return self._parse_value(db_setting.value, db_setting.value_type)
        
        return default
    
    def set_db_setting(self, key: str, value: str, value_type: str = "string") -> ConfigSetting:
        """Обновить или создать настройку в БД"""
        db_setting = self.db.query(ConfigSetting).filter(ConfigSetting.key == key).first()
        if db_setting:
            db_setting.value = value
            db_setting.value_type = value_type
            db_setting.updated_at = func.now()
        else:
            db_setting = ConfigSetting(key=key, value=value, value_type=value_type)
            self.db.add(db_setting)
        
        self.db.commit()
        self.db.refresh(db_setting)
        return db_setting
    
    def _parse_value(self, value: str, value_type: str) -> Any:
        """Парсинг значения в соответствии с типом"""
        if value is None:
            return None
        
        try:
            if value_type == "integer":
                return int(value)
            elif value_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif value_type == "float":
                return float(value)
            elif value_type == "json":
                return json.loads(value)
            else:  # string
                return value
        except (ValueError, json.JSONDecodeError):
            return value  # возвращаем как строку если парсинг не удался

# Зависимости
def get_database_size():
    """Получить размер базы данных в МБ"""
    try:
        # Используем прямой SQL запрос для получения размера БД
        db = SessionLocal()
        result = db.execute(text("SELECT pg_size_pretty(pg_database_size('digest_bot'))")).fetchone()
        size_str = result[0] if result and result[0] else "0 MB"
        
        # Извлекаем числовое значение в МБ
        if "GB" in size_str:
            size_mb = float(size_str.split(" ")[0]) * 1024
        elif "MB" in size_str:
            size_mb = float(size_str.split(" ")[0])
        elif "kB" in size_str:
            size_mb = float(size_str.split(" ")[0]) / 1024
        else:
            size_mb = 0.0
            
        db.close()
        return round(size_mb, 2)
    except Exception as e:
        print(f"Error getting database size: {e}")
        return 0.0

def get_filtered_data_size(channel_ids: list = None):
    """Получить размер отфильтрованных данных в МБ"""
    try:
        db = SessionLocal()
        
        # Всегда используем одинаковую логику - размер данных в строках
        if channel_ids:
            # Размер данных для конкретных каналов
            channel_ids_str = ','.join(map(str, channel_ids))
            query = text(f"""
                SELECT pg_size_pretty(
                    sum(pg_column_size(posts_cache.*))::bigint
                ) 
                FROM posts_cache 
                WHERE channel_telegram_id IN ({channel_ids_str})
            """)
        else:
            # Размер данных во всех строках posts_cache (аналогично фильтрованному)
            query = text("""
                SELECT pg_size_pretty(
                    sum(pg_column_size(posts_cache.*))::bigint
                ) 
                FROM posts_cache
            """)
        
        result = db.execute(query).fetchone()
        size_str = result[0] if result and result[0] else "0 bytes"
        
        # Извлекаем числовое значение в МБ
        if "GB" in size_str:
            size_mb = float(size_str.split(" ")[0]) * 1024
        elif "MB" in size_str:
            size_mb = float(size_str.split(" ")[0])
        elif "kB" in size_str:
            size_mb = float(size_str.split(" ")[0]) / 1024
        elif "bytes" in size_str:
            # Для очень маленьких размеров переводим байты в МБ
            bytes_count = float(size_str.split(" ")[0])
            size_mb = bytes_count / (1024 * 1024)
        else:
            size_mb = 0.0
            
        db.close()
        return round(size_mb, 2)
    except Exception as e:
        print(f"Error getting filtered data size: {e}")
        return 0.0

# API Routes для категорий
@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список категорий с возможностью поиска и фильтрации"""
    query = db.query(Category)
    
    if active_only:
        query = query.filter(Category.is_active == True)
    
    if search:
        query = query.filter(Category.category_name.contains(search))
    
    categories = query.order_by(Category.category_name).offset(skip).limit(limit).all()
    return categories

@app.post("/api/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Создать новую категорию"""
    # Проверяем уникальность имени
    existing = db.query(Category).filter(Category.category_name == category.category_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким именем уже существует"
        )
    
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/api/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Получить категорию по ID"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return category

@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate, db: Session = Depends(get_db)):
    """Обновить категорию"""
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем уникальность имени (исключая текущую категорию)
    existing = db.query(Category).filter(
        Category.category_name == category.category_name,
        Category.id != category_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория с таким именем уже существует"
        )
    
    for field, value in category.model_dump().items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Удалить категорию"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    db.delete(category)
    db.commit()
    return {"message": "Категория успешно удалена"}

# API Routes для каналов
@app.get("/api/channels", response_model=List[ChannelResponse])
def get_channels(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список каналов с возможностью поиска и фильтрации"""
    from sqlalchemy.orm import selectinload
    
    query = db.query(Channel).options(selectinload(Channel.categories))
    
    if active_only:
        query = query.filter(Channel.is_active == True)
    
    if search:
        query = query.filter(
            Channel.title.contains(search) | 
            Channel.username.contains(search)
        )
    
    channels = query.order_by(Channel.title).offset(skip).limit(limit).all()
    return channels

@app.post("/api/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
def create_channel(channel: ChannelCreate, db: Session = Depends(get_db)):
    """Создать новый канал"""
    # Проверяем уникальность telegram_id
    existing = db.query(Channel).filter(Channel.telegram_id == channel.telegram_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Канал с таким Telegram ID уже существует"
        )
    
    # Создаем данные для БД с автозаполнением title
    channel_data = channel.model_dump()
    if not channel_data.get('title'):
        channel_data['title'] = channel_data['channel_name']  # Заполняем title из channel_name
    
    db_channel = Channel(**channel_data)
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

@app.get("/api/channels/{channel_id}", response_model=ChannelResponse)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Получить канал по ID"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    return channel

@app.put("/api/channels/{channel_id}", response_model=ChannelResponse)
def update_channel(channel_id: int, channel: ChannelUpdate, db: Session = Depends(get_db)):
    """Обновить канал"""
    db_channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    # Проверяем уникальность telegram_id (исключая текущий канал)
    existing = db.query(Channel).filter(
        Channel.telegram_id == channel.telegram_id,
        Channel.id != channel_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Канал с таким Telegram ID уже существует"
        )
    
    # Обновляем данные с автозаполнением title
    channel_data = channel.model_dump()
    if not channel_data.get('title'):
        channel_data['title'] = channel_data['channel_name']  # Заполняем title из channel_name
    
    for field, value in channel_data.items():
        setattr(db_channel, field, value)
    
    db.commit()
    db.refresh(db_channel)
    return db_channel

@app.delete("/api/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """Удалить канал"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    db.delete(channel)
    db.commit()
    return {"message": "Канал успешно удален"}

@app.post("/api/channels/validate")
async def validate_channel(request: dict):
    """Валидация канала и получение предложений для автозаполнения"""
    try:
        user_input = request.get('channel_input', '').strip()
        if not user_input:
            return {
                'success': False,
                'error': 'Введите username, ссылку или Telegram ID канала',
                'data': None
            }
        
        # Импорт модуля валидации
        from channel_validator import validate_channel_for_api
        
        result = await validate_channel_for_api(user_input)
        
        if result['validation']['valid']:
            suggestions = result['suggestions']
            return {
                'success': True,
                'data': {
                    'title': suggestions.get('title'),
                    'username': suggestions.get('username'),
                    'description': suggestions.get('description'),
                    'telegram_id': suggestions.get('telegram_id'),
                    'subscribers': getattr(result, 'subscribers_count', None)
                },
                'message': 'Канал успешно найден и проверен'
            }
        else:
            warnings = result['validation']['warnings']
            error_message = warnings[0] if warnings else 'Не удалось проверить канал'
            return {
                'success': False,
                'error': error_message,
                'data': None
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Ошибка валидации: {str(e)}',
            'data': None
        }

# Дополнительные endpoints
@app.get("/api/health")
def health_check():
    """Проверка состояния API"""
    return {"status": "ok", "timestamp": datetime.now()}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Получить базовую статистику"""
    categories_count = db.query(Category).count()
    channels_count = db.query(Channel).count()
    active_categories = db.query(Category).filter(Category.is_active == True).count()
    active_channels = db.query(Channel).filter(Channel.is_active == True).count()
    digests_count = db.query(Digest).count()
    posts_total = db.query(PostCache).count()
    posts_pending = db.query(PostCache).filter(PostCache.processing_status == "pending").count()
    posts_processed = db.query(PostCache).filter(PostCache.processing_status == "completed").count()
    
    # Статистика связей
    total_links = db.query(channel_categories).count()
    
    # Размер базы данных
    database_size = get_database_size()
    
    return {
        "total_categories": categories_count,
        "active_categories": active_categories,
        "total_channels": channels_count,
        "active_channels": active_channels,
        "total_digests": digests_count,
        "total_posts": posts_total,
        "posts_pending": posts_pending,
        "posts_processed": posts_processed,
        "channel_category_links": total_links,
        "database_size_mb": database_size
    }

# API для управления связями канал-категория
@app.get("/api/channels/{channel_id}/categories", response_model=List[CategoryResponse])
def get_channel_categories(channel_id: int, db: Session = Depends(get_db)):
    """Получить все категории для конкретного канала"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    return channel.categories

@app.post("/api/channels/{channel_id}/categories/{category_id}")
def add_category_to_channel(channel_id: int, category_id: int, db: Session = Depends(get_db)):
    """Добавить категорию к каналу"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем, что связь еще не существует
    if category in channel.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория уже привязана к этому каналу"
        )
    
    channel.categories.append(category)
    db.commit()
    
    return {"message": "Категория успешно добавлена к каналу"}

@app.delete("/api/channels/{channel_id}/categories/{category_id}")
def remove_category_from_channel(channel_id: int, category_id: int, db: Session = Depends(get_db)):
    """Удалить категорию от канала"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Канал не найден"
        )
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем, что связь существует
    if category not in channel.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Категория не привязана к этому каналу"
        )
    
    channel.categories.remove(category)
    db.commit()
    
    return {"message": "Категория успешно удалена от канала"}

@app.get("/api/categories/{category_id}/channels", response_model=List[ChannelResponse])
def get_category_channels(category_id: int, db: Session = Depends(get_db)):
    """Получить все каналы для конкретной категории"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    return category.channels

# API для настроек системы
@app.get("/api/settings", response_model=List[ConfigSettingResponse])
def get_settings(
    category: Optional[str] = None,
    editable_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список настроек с возможностью фильтрации"""
    query = db.query(ConfigSetting)
    
    if category:
        query = query.filter(ConfigSetting.category == category)
    
    if editable_only:
        query = query.filter(ConfigSetting.is_editable == True)
    
    settings = query.order_by(ConfigSetting.category, ConfigSetting.key).all()
    return settings

@app.get("/api/settings/categories")
def get_setting_categories():
    """Получить список всех категорий настроек"""
    # Временная заглушка с основными категориями
    return {"categories": ["system", "digest", "ai"]}

@app.post("/api/settings", response_model=ConfigSettingResponse, status_code=status.HTTP_201_CREATED)
def create_setting(setting: ConfigSettingCreate, db: Session = Depends(get_db)):
    """Создать новую настройку"""
    # Проверяем уникальность ключа
    existing = db.query(ConfigSetting).filter(ConfigSetting.key == setting.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Настройка с таким ключом уже существует"
        )
    
    db_setting = ConfigSetting(**setting.model_dump())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@app.get("/api/settings/{setting_id}", response_model=ConfigSettingResponse)
def get_setting(setting_id: int, db: Session = Depends(get_db)):
    """Получить настройку по ID"""
    setting = db.query(ConfigSetting).filter(ConfigSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройка не найдена"
        )
    return setting

@app.put("/api/settings/{setting_id}", response_model=ConfigSettingResponse)
def update_setting(setting_id: int, setting: ConfigSettingUpdate, db: Session = Depends(get_db)):
    """Обновить настройку"""
    db_setting = db.query(ConfigSetting).filter(ConfigSetting.id == setting_id).first()
    if not db_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройка не найдена"
        )
    
    # Обновляем только предоставленные поля
    for field, value in setting.model_dump(exclude_unset=True).items():
        setattr(db_setting, field, value)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting

@app.delete("/api/settings/{setting_id}")
def delete_setting(setting_id: int, db: Session = Depends(get_db)):
    """Удалить настройку"""
    setting = db.query(ConfigSetting).filter(ConfigSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройка не найдена"
        )
    
    db.delete(setting)
    db.commit()
    return {"message": "Настройка успешно удалена"}

# Endpoint для получения конфигурации через ConfigManager
@app.get("/api/config/{key}")
def get_config_value(key: str, db: Session = Depends(get_db)):
    """Получить значение конфигурации через ConfigManager"""
    config = ConfigManager(db)
    value = config.get(key)
    
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конфигурация не найдена"
        )
    
    return {"key": key, "value": value}

# API для дайджестов
@app.post("/api/digests", response_model=DigestResponse, status_code=status.HTTP_201_CREATED)
def create_digest(digest: DigestCreate, db: Session = Depends(get_db)):
    """Создать новый дайджест (endpoint для N8N)"""
    # Проверяем уникальность digest_id
    existing = db.query(Digest).filter(Digest.digest_id == digest.digest_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дайджест с таким ID уже существует"
        )
    
    db_digest = Digest(**digest.model_dump())
    db.add(db_digest)
    db.commit()
    db.refresh(db_digest)
    return db_digest

@app.get("/api/digests", response_model=List[DigestSummary])
def get_digests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список дайджестов (краткая информация)"""
    digests = db.query(Digest).order_by(Digest.created_at.desc()).offset(skip).limit(limit).all()
    return digests

@app.get("/api/digests/{digest_id}", response_model=DigestResponse)
def get_digest(digest_id: str, db: Session = Depends(get_db)):
    """Получить полную информацию о дайджесте"""
    digest = db.query(Digest).filter(Digest.digest_id == digest_id).first()
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Дайджест не найден"
        )
    return digest

@app.get("/api/digests/{digest_id}/data")
def get_digest_data(digest_id: str, db: Session = Depends(get_db)):
    """Получить полные данные дайджеста в JSON формате"""
    digest = db.query(Digest).filter(Digest.digest_id == digest_id).first()
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Дайджест не найден"
        )
    
    try:
        if digest.digest_data:
            data = json.loads(digest.digest_data)
            return data
        else:
            return {"error": "Данные дайджеста отсутствуют"}
    except json.JSONDecodeError:
        return {"error": "Ошибка парсинга данных дайджеста"}

@app.delete("/api/digests/{digest_id}")
def delete_digest(digest_id: str, db: Session = Depends(get_db)):
    """Удалить дайджест"""
    digest = db.query(Digest).filter(Digest.digest_id == digest_id).first()
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Дайджест не найден"
        )
    
    db.delete(digest)
    db.commit()
    return {"message": "Дайджест успешно удален"}

@app.get("/api/digests/stats/summary")
def get_digests_stats(db: Session = Depends(get_db)):
    """Получить статистику дайджестов"""
    total_digests = db.query(Digest).count()
    
    if total_digests == 0:
        return {
            "total_digests": 0,
            "avg_posts_per_digest": 0,
            "avg_relevance_rate": 0,
            "total_posts_processed": 0
        }
    
    # Агрегированная статистика
    from sqlalchemy import func as sql_func
    stats = db.query(
        sql_func.avg(Digest.total_posts).label('avg_posts'),
        sql_func.avg(Digest.relevant_posts).label('avg_relevant'),
        sql_func.sum(Digest.total_posts).label('total_posts'),
        sql_func.avg(Digest.avg_importance).label('avg_importance'),
        sql_func.avg(Digest.avg_urgency).label('avg_urgency'),
        sql_func.avg(Digest.avg_significance).label('avg_significance')
    ).first()
    
    return {
        "total_digests": total_digests,
        "avg_posts_per_digest": round(stats.avg_posts or 0, 1),
        "avg_relevance_rate": round((stats.avg_relevant / stats.avg_posts * 100) if stats.avg_posts else 0, 1),
        "total_posts_processed": stats.total_posts or 0,
        "avg_metrics": {
            "importance": round(stats.avg_importance or 0, 1),
            "urgency": round(stats.avg_urgency or 0, 1),
            "significance": round(stats.avg_significance or 0, 1)
        }
    }

# API для пользователей и подписок
@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_user(user: UserCreate, db: Session = Depends(get_db)):
    """Создать нового пользователя или обновить существующего"""
    # Проверяем, существует ли пользователь
    existing_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
    
    if existing_user:
        # Обновляем данные существующего пользователя
        for field, value in user.model_dump().items():
            if hasattr(existing_user, field) and value is not None:
                setattr(existing_user, field, value)
        existing_user.last_activity = func.now()
        db.commit()
        db.refresh(existing_user)
        return existing_user
    else:
        # Создаем нового пользователя
        db_user = User(**user.model_dump())
        db_user.last_activity = func.now()
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

@app.get("/api/users/{telegram_id}", response_model=UserResponse)
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить пользователя по Telegram ID"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

@app.get("/api/users/{telegram_id}/subscriptions", response_model=List[CategoryResponse])
def get_user_subscriptions(telegram_id: int, db: Session = Depends(get_db)):
    """Получить подписки пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user.subscribed_categories

@app.post("/api/users/{telegram_id}/subscriptions", response_model=SubscriptionResponse)
def update_user_subscriptions(telegram_id: int, subscription: SubscriptionRequest, db: Session = Depends(get_db)):
    """Обновить подписки пользователя"""
    # Получаем или создаем пользователя
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден. Сначала создайте пользователя."
        )
    
    # Получаем категории по ID
    categories = db.query(Category).filter(Category.id.in_(subscription.category_ids)).all()
    if len(categories) != len(subscription.category_ids):
        found_ids = [cat.id for cat in categories]
        missing_ids = [cat_id for cat_id in subscription.category_ids if cat_id not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Категории не найдены: {missing_ids}"
        )
    
    # Обновляем подписки
    user.subscribed_categories = categories
    user.last_activity = func.now()
    db.commit()
    db.refresh(user)
    
    return SubscriptionResponse(
        user_id=user.id,
        subscribed_categories=user.subscribed_categories,
        message=f"Подписки обновлены. Выбрано категорий: {len(categories)}"
    )

@app.delete("/api/users/{telegram_id}/subscriptions/{category_id}")
def remove_user_subscription(telegram_id: int, category_id: int, db: Session = Depends(get_db)):
    """Удалить подписку на категорию"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    if category in user.subscribed_categories:
        user.subscribed_categories.remove(category)
        user.last_activity = func.now()
        db.commit()
        return {"message": "Подписка удалена"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не подписан на эту категорию"
        )

# API для posts_cache
@app.post("/api/posts/batch", status_code=status.HTTP_201_CREATED)
def create_posts_batch(batch: PostsBatchCreate, db: Session = Depends(get_db)):
    """Принимает batch постов от userbot и сохраняет в posts_cache"""
    try:
        created_posts = []
        skipped_posts = []
        
        for post_data in batch.posts:
            # Проверяем, не существует ли уже такой пост
            existing_post = db.query(PostCache).filter(
                PostCache.channel_telegram_id == post_data.channel_telegram_id,
                PostCache.telegram_message_id == post_data.telegram_message_id
            ).first()
            
            if existing_post:
                skipped_posts.append({
                    "channel_id": post_data.channel_telegram_id,
                    "message_id": post_data.telegram_message_id,
                    "reason": "already_exists"
                })
                continue
            
            # Создаем новый пост
            post_dict = post_data.model_dump()
            # Добавляем metadata от userbot - ищем по различным ключам
            metadata = {}
            if batch.channels_metadata:
                # Пытаемся найти metadata по различным идентификаторам
                channel_key = None
                for key in batch.channels_metadata.keys():
                    if str(post_data.channel_telegram_id) in key or key == str(post_data.channel_telegram_id):
                        channel_key = key
                        break
                
                if channel_key:
                    metadata = batch.channels_metadata[channel_key]
            
            # JSONB поля теперь сохраняются напрямую как Python объекты
            post_dict["userbot_metadata"] = metadata if metadata else {}
            
            db_post = PostCache(**post_dict)
            db.add(db_post)
            created_posts.append(post_data.telegram_message_id)
        
        db.commit()
        
        return {
            "message": "Batch обработан успешно",
            "timestamp": batch.timestamp,
            "collection_stats": batch.collection_stats,
            "created_posts": len(created_posts),
            "skipped_posts": len(skipped_posts),
            "created_ids": created_posts,
            "skipped_details": skipped_posts
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка сохранения постов: {str(e)}"
        )

@app.get("/api/posts/cache", response_model=List[PostCacheResponse])
def get_posts_cache(
    skip: int = 0,
    limit: int = 100,
    channel_telegram_id: Optional[int] = None,
    processing_status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "collected_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Получить список постов из cache с расширенной фильтрацией"""
    from datetime import datetime
    
    query = db.query(PostCache)
    
    # Фильтр по каналу
    if channel_telegram_id:
        query = query.filter(PostCache.channel_telegram_id == channel_telegram_id)
    
    # Фильтр по статусу обработки
    if processing_status:
        query = query.filter(PostCache.processing_status == processing_status)
    
    # Поиск по содержимому
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            PostCache.content.ilike(search_pattern) |
            PostCache.title.ilike(search_pattern)
        )
    
    # Фильтр по дате
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(PostCache.post_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(PostCache.post_date <= date_to_obj)
        except ValueError:
            pass
    
    # Сортировка
    sort_column = getattr(PostCache, sort_by, PostCache.collected_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    posts = query.offset(skip).limit(limit).all()
    return posts

@app.get("/api/posts/stats")
def get_posts_stats(db: Session = Depends(get_db)):
    """Получить статистику posts_cache"""
    from sqlalchemy import func as sql_func
    
    # Общая статистика
    total_posts = db.query(PostCache).count()
    
    # Статистика по каналам с дополнительной информацией
    channel_stats = db.query(
        PostCache.channel_telegram_id,
        sql_func.count(PostCache.id).label('posts_count'),
        sql_func.max(PostCache.collected_at).label('last_collected'),
        sql_func.avg(PostCache.views).label('avg_views'),
        sql_func.max(PostCache.views).label('max_views')
    ).group_by(
        PostCache.channel_telegram_id
    ).all()
    
    # Статистика по статусам обработки
    status_stats = db.query(
        PostCache.processing_status,
        sql_func.count(PostCache.id).label('count')
    ).group_by(PostCache.processing_status).all()
    
    # Получаем информацию о каналах из основной таблицы
    channel_info = {}
    for stat in channel_stats:
        channel = db.query(Channel).filter(Channel.telegram_id == stat.channel_telegram_id).first()
        if channel:
            channel_info[stat.channel_telegram_id] = {
                "title": channel.title,
                "username": channel.username,
                "categories": [cat.name for cat in channel.categories]
            }
    
    return {
        "total_posts": total_posts,
        "channels": [
            {
                "telegram_id": stat.channel_telegram_id,
                "posts_count": stat.posts_count,
                "last_collected": stat.last_collected,
                "avg_views": round(stat.avg_views or 0, 0),
                "max_views": stat.max_views or 0,
                "title": channel_info.get(stat.channel_telegram_id, {}).get("title", f"Channel {stat.channel_telegram_id}"),
                "username": channel_info.get(stat.channel_telegram_id, {}).get("username"),
                "categories": channel_info.get(stat.channel_telegram_id, {}).get("categories", [])
            }
            for stat in channel_stats
        ],
        "processing_status": [
            {
                "status": stat.processing_status,
                "count": stat.count
            }
            for stat in status_stats
        ]
    }

@app.get("/api/posts/cache/count")
def get_posts_cache_count(
    channel_telegram_id: Optional[int] = None,
    processing_status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить количество постов с фильтрацией (для пагинации)"""
    from datetime import datetime
    
    query = db.query(PostCache)
    
    if channel_telegram_id:
        query = query.filter(PostCache.channel_telegram_id == channel_telegram_id)
    
    if processing_status:
        query = query.filter(PostCache.processing_status == processing_status)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            PostCache.content.ilike(search_pattern) |
            PostCache.title.ilike(search_pattern)
        )
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(PostCache.post_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(PostCache.post_date <= date_to_obj)
        except ValueError:
            pass
    
    total_count = query.count()
    return {"total_count": total_count}

@app.get("/api/posts/cache/size")
def get_posts_cache_size(
    channel_telegram_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить размер posts_cache в МБ (общий или по каналу)"""
    try:
        if channel_telegram_id:
            size_mb = get_filtered_data_size([channel_telegram_id])
        else:
            size_mb = get_filtered_data_size()
        
        # Отладочная информация
        if not channel_telegram_id:
            # Запрос для отладки - прямо в endpoint
            result = db.execute(text("SELECT pg_size_pretty(pg_total_relation_size('posts_cache'))")).fetchone()
            debug_size_str = result[0] if result else "unknown"
            print(f"DEBUG: pg_size_pretty result for posts_cache: '{debug_size_str}'")
        
        return {
            "size_mb": size_mb,
            "channel_telegram_id": channel_telegram_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения размера данных: {str(e)}"
        )

@app.delete("/api/database/clear")
def clear_database(
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """КРИТИЧЕСКОЕ ДЕЙСТВИЕ: Очистить всю базу данных"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для подтверждения критического действия необходимо передать параметр confirm=true"
        )
    
    try:
        # Получаем статистику перед удалением
        posts_count = db.query(PostCache).count()
        digests_count = db.query(Digest).count()
        
        # Удаляем все посты
        db.query(PostCache).delete()
        
        # Удаляем все дайджесты  
        db.query(Digest).delete()
        
        # Сбрасываем связи каналов с категориями (опционально)
        # db.execute(text("TRUNCATE TABLE channel_categories"))
        
        db.commit()
        
        return {
            "message": "База данных успешно очищена",
            "deleted_posts": posts_count,
            "deleted_digests": digests_count,
            "warning": "Это действие необратимо!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка очистки базы данных: {str(e)}"
        )

@app.delete("/api/posts/orphans")
def cleanup_orphan_posts(
    confirm: bool = False,
    db: Session = Depends(get_db)
):
    """Удалить посты от каналов, которых больше нет в системе (orphan cleanup)"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для подтверждения действия необходимо передать параметр confirm=true"
        )
    
    try:
        # Получаем список активных telegram_id каналов
        active_channel_ids = db.query(Channel.telegram_id).filter(Channel.is_active == True).all()
        active_ids_set = {row[0] for row in active_channel_ids}
        
        # Находим посты от несуществующих каналов
        orphan_posts_query = db.query(PostCache).filter(
            ~PostCache.channel_telegram_id.in_(active_ids_set)
        )
        
        # Статистика до удаления
        orphan_count = orphan_posts_query.count()
        
        if orphan_count == 0:
            return {
                "message": "Orphan постов не найдено",
                "deleted_posts": 0,
                "active_channels": len(active_ids_set)
            }
        
        # Получаем детали orphan каналов для отчета
        orphan_channels_stats = db.query(
            PostCache.channel_telegram_id,
            sql_func.count(PostCache.id).label('posts_count')
        ).filter(
            ~PostCache.channel_telegram_id.in_(active_ids_set)
        ).group_by(PostCache.channel_telegram_id).all()
        
        # Удаляем orphan посты
        deleted_count = orphan_posts_query.delete(synchronize_session=False)
        db.commit()
        
        return {
            "message": f"Успешно удалено {deleted_count} orphan постов",
            "deleted_posts": deleted_count,
            "orphan_channels": [
                {
                    "telegram_id": stat.channel_telegram_id,
                    "deleted_posts": stat.posts_count
                }
                for stat in orphan_channels_stats
            ],
            "active_channels": len(active_ids_set)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка очистки orphan постов: {str(e)}"
        )

# ==================== PUBLIC BOTS API ====================

@app.get("/api/public-bots", response_model=List[PublicBotResponse])
def get_public_bots(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить список публичных ботов с фильтрацией"""
    query = db.query(PublicBot)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            PublicBot.name.ilike(search_pattern) |
            PublicBot.description.ilike(search_pattern)
        )
    
    if status_filter:
        query = query.filter(PublicBot.status == status_filter)
    
    bots = query.offset(skip).limit(limit).all()
    return bots

@app.post("/api/public-bots", response_model=PublicBotResponse, status_code=status.HTTP_201_CREATED)
def create_public_bot(bot: PublicBotCreate, db: Session = Depends(get_db)):
    """Создать нового публичного бота с автоприменением шаблонных настроек"""
    try:
        # Проверяем уникальность имени
        existing_bot = db.query(PublicBot).filter(PublicBot.name == bot.name).first()
        if existing_bot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Бот с именем '{bot.name}' уже существует"
            )
        
        # Получаем шаблонные настройки
        template = get_bot_template_settings(db)
        
        # Создаем бота с данными из запроса
        bot_data = bot.dict()
        
        # Применяем шаблонные значения для пустых полей
        if not bot_data.get('categorization_prompt'):
            bot_data['categorization_prompt'] = template.default_categorization_prompt
        
        if not bot_data.get('summarization_prompt'):
            bot_data['summarization_prompt'] = template.default_summarization_prompt
        
        if not bot_data.get('welcome_message'):
            bot_data['welcome_message'] = template.default_welcome_message
        
        if bot_data.get('max_posts_per_digest') == 10:  # значение по умолчанию
            bot_data['max_posts_per_digest'] = template.default_max_posts_per_digest
        
        if bot_data.get('max_summary_length') == 150:  # значение по умолчанию
            bot_data['max_summary_length'] = template.default_max_summary_length
        
        if not bot_data.get('delivery_schedule') or bot_data.get('delivery_schedule') == {}:
            bot_data['delivery_schedule'] = template.default_delivery_schedule
        
        if bot_data.get('default_language') == 'ru' and template.default_digest_language != 'ru':
            bot_data['default_language'] = template.default_digest_language
        
        if bot_data.get('timezone') == 'Europe/Moscow' and template.default_timezone != 'Europe/Moscow':
            bot_data['timezone'] = template.default_timezone
        
        # Создаем нового бота
        db_bot = PublicBot(**bot_data)
        db.add(db_bot)
        db.commit()
        db.refresh(db_bot)
        
        return db_bot
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания бота: {str(e)}"
        )

@app.get("/api/public-bots/{bot_id}", response_model=PublicBotResponse)
def get_public_bot(bot_id: int, db: Session = Depends(get_db)):
    """Получить публичного бота по ID"""
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бот не найден"
        )
    return bot

@app.put("/api/public-bots/{bot_id}", response_model=PublicBotResponse)
def update_public_bot(bot_id: int, bot_update: PublicBotUpdate, db: Session = Depends(get_db)):
    """Обновить публичного бота"""
    try:
        db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not db_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # Проверяем уникальность имени при изменении
        if bot_update.name and bot_update.name != db_bot.name:
            existing_bot = db.query(PublicBot).filter(
                PublicBot.name == bot_update.name,
                PublicBot.id != bot_id
            ).first()
            if existing_bot:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Бот с именем '{bot_update.name}' уже существует"
                )
        
        # Обновляем поля
        update_data = bot_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_bot, field, value)
        
        db.commit()
        db.refresh(db_bot)
        
        return db_bot
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления бота: {str(e)}"
        )

@app.delete("/api/public-bots/{bot_id}")
def delete_public_bot(bot_id: int, db: Session = Depends(get_db)):
    """Удалить публичного бота"""
    try:
        db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not db_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        bot_name = db_bot.name
        db.delete(db_bot)
        db.commit()
        
        return {
            "message": f"Бот '{bot_name}' успешно удален",
            "deleted_bot_id": bot_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления бота: {str(e)}"
        )

@app.post("/api/public-bots/{bot_id}/toggle-status")
def toggle_bot_status(bot_id: int, db: Session = Depends(get_db)):
    """Переключить статус бота (active ↔ paused)"""
    try:
        db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not db_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # Переключаем статус
        if db_bot.status == "active":
            db_bot.status = "paused"
        elif db_bot.status == "paused":
            db_bot.status = "active"
        else:  # setup
            db_bot.status = "active"
        
        db.commit()
        db.refresh(db_bot)
        
        return {
            "message": f"Статус бота '{db_bot.name}' изменен на '{db_bot.status}'",
            "bot_id": bot_id,
            "new_status": db_bot.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка изменения статуса бота: {str(e)}"
        )

# Endpoints для связей Public Bot ↔ Channels
@app.get("/api/public-bots/{bot_id}/channels", response_model=List[ChannelResponse])
def get_bot_channels(bot_id: int, db: Session = Depends(get_db)):
    """Получить все каналы, связанные с ботом"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    # Получаем каналы через связи bot_channels
    bot_channels = db.query(BotChannel).filter(
        BotChannel.public_bot_id == bot_id,
        BotChannel.is_active == True
    ).all()
    
    # Извлекаем каналы из связей
    channels = []
    for bot_channel in bot_channels:
        channel = bot_channel.channel
        if channel and channel.is_active:
            channels.append(channel)
    
    return channels

@app.post("/api/public-bots/{bot_id}/channels")
def add_channels_to_bot(
    bot_id: int, 
    request: dict,  # {"channel_ids": [1, 2, 3]}
    db: Session = Depends(get_db)
):
    """Добавить каналы к боту (bulk операция)"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    channel_ids = request.get("channel_ids", [])
    if not channel_ids:
        raise HTTPException(status_code=400, detail="channel_ids is required")
    
    # Проверяем существование каналов
    channels = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
    if len(channels) != len(channel_ids):
        found_ids = [ch.id for ch in channels]
        missing_ids = [ch_id for ch_id in channel_ids if ch_id not in found_ids]
        raise HTTPException(status_code=404, detail=f"Channels not found: {missing_ids}")
    
    # Добавляем связи в таблицу bot_channels
    added_count = 0
    for channel_id in channel_ids:
        # Проверяем, не существует ли уже связь
        existing = db.query(BotChannel).filter(
            BotChannel.public_bot_id == bot_id,
            BotChannel.channel_id == channel_id
        ).first()
        
        if not existing:
            # Создаем новую связь
            bot_channel = BotChannel(
                public_bot_id=bot_id,
                channel_id=channel_id,
                weight=1.0,
                is_active=True
            )
            db.add(bot_channel)
            added_count += 1
        else:
            # Если связь существует, но неактивна - активируем
            if not existing.is_active:
                existing.is_active = True
                added_count += 1
    
    # Обновляем счетчик каналов в боте
    channels_count = db.query(BotChannel).filter(
        BotChannel.public_bot_id == bot_id,
        BotChannel.is_active == True
    ).count()
    bot.channels_count = channels_count
    
    db.commit()
    return {"message": f"Added {added_count} channels to bot {bot_id}", "channel_ids": channel_ids}

@app.delete("/api/public-bots/{bot_id}/channels/{channel_id}")
def remove_channel_from_bot(bot_id: int, channel_id: int, db: Session = Depends(get_db)):
    """Удалить канал из бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    # Проверяем существование канала
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Ищем связь bot_channel
    bot_channel = db.query(BotChannel).filter(
        BotChannel.public_bot_id == bot_id,
        BotChannel.channel_id == channel_id
    ).first()
    
    if not bot_channel:
        raise HTTPException(status_code=404, detail="Channel is not associated with this bot")
    
    # Удаляем связь
    db.delete(bot_channel)
    
    # Обновляем счетчик каналов в боте
    channels_count = db.query(BotChannel).filter(
        BotChannel.public_bot_id == bot_id,
        BotChannel.is_active == True
    ).count()
    bot.channels_count = channels_count
    
    db.commit()
    return {"message": f"Removed channel {channel_id} from bot {bot_id}"}

# Endpoints для связей Public Bot ↔ Categories
@app.get("/api/public-bots/{bot_id}/categories")
def get_bot_categories(bot_id: int, db: Session = Depends(get_db)):
    """Получить все категории, связанные с ботом, с приоритетами"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    # Получаем категории через связи bot_categories с приоритетами
    bot_categories = db.query(BotCategory).filter(
        BotCategory.public_bot_id == bot_id,
        BotCategory.is_active == True
    ).order_by(BotCategory.weight.desc()).all()
    
    # Формируем ответ с включением приоритетов
    categories_with_priority = []
    for bot_category in bot_categories:
        category = bot_category.category
        if category and category.is_active:
            # Создаем словарь с данными категории + приоритет
            category_dict = {
                "id": category.id,
                "category_name": category.category_name,
                "description": category.description,
                "is_active": category.is_active,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "weight": bot_category.weight,  # Добавляем приоритет из связи
                "priority": bot_category.weight  # Дублируем для совместимости
            }
            categories_with_priority.append(category_dict)
    
    return categories_with_priority

@app.post("/api/public-bots/{bot_id}/categories")
def add_categories_to_bot(
    bot_id: int, 
    request: dict,  # {"category_ids": [1, 2, 3], "priorities": [1, 2, 3]}
    db: Session = Depends(get_db)
):
    """Добавить категории к боту (bulk операция)"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    category_ids = request.get("category_ids", [])
    priorities = request.get("priorities", [])
    
    if not category_ids:
        raise HTTPException(status_code=400, detail="category_ids is required")
    
    # Если приоритеты не указаны, генерируем автоматически
    if not priorities:
        priorities = list(range(1, len(category_ids) + 1))
    
    if len(priorities) != len(category_ids):
        raise HTTPException(status_code=400, detail="priorities length must match category_ids length")
    
    # Проверяем существование категорий
    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    if len(categories) != len(category_ids):
        found_ids = [cat.id for cat in categories]
        missing_ids = [cat_id for cat_id in category_ids if cat_id not in found_ids]
        raise HTTPException(status_code=404, detail=f"Categories not found: {missing_ids}")
    
    # Добавляем связи в таблицу bot_categories с приоритетами
    added_count = 0
    for i, category_id in enumerate(category_ids):
        priority = priorities[i]
        
        # Проверяем, не существует ли уже связь
        existing = db.query(BotCategory).filter(
            BotCategory.public_bot_id == bot_id,
            BotCategory.category_id == category_id
        ).first()
        
        if not existing:
            # Создаем новую связь
            bot_category = BotCategory(
                public_bot_id=bot_id,
                category_id=category_id,
                weight=float(priority),
                is_active=True
            )
            db.add(bot_category)
            added_count += 1
        else:
            # Если связь существует, обновляем приоритет и активируем
            existing.weight = float(priority)
            if not existing.is_active:
                existing.is_active = True
                added_count += 1
    
    # Обновляем счетчик категорий в боте
    categories_count = db.query(BotCategory).filter(
        BotCategory.public_bot_id == bot_id,
        BotCategory.is_active == True
    ).count()
    bot.topics_count = categories_count
    
    db.commit()
    return {
        "message": f"Added {added_count} categories to bot {bot_id}", 
        "category_ids": category_ids,
        "priorities": priorities
    }

@app.delete("/api/public-bots/{bot_id}/categories/{category_id}")
def remove_category_from_bot(bot_id: int, category_id: int, db: Session = Depends(get_db)):
    """Удалить категорию из бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    # Проверяем существование категории
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Ищем связь bot_category
    bot_category = db.query(BotCategory).filter(
        BotCategory.public_bot_id == bot_id,
        BotCategory.category_id == category_id
    ).first()
    
    if not bot_category:
        raise HTTPException(status_code=404, detail="Category is not associated with this bot")
    
    # Удаляем связь
    db.delete(bot_category)
    
    # Обновляем счетчик категорий в боте
    categories_count = db.query(BotCategory).filter(
        BotCategory.public_bot_id == bot_id,
        BotCategory.is_active == True
    ).count()
    bot.topics_count = categories_count
    
    db.commit()
    return {"message": f"Removed category {category_id} from bot {bot_id}"}

@app.put("/api/public-bots/{bot_id}/categories/{category_id}/priority")
def update_category_priority(
    bot_id: int, 
    category_id: int, 
    request: dict,  # {"priority": 5}
    db: Session = Depends(get_db)
):
    """Обновить приоритет категории для бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Public bot not found")
    
    # Проверяем существование категории
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    priority = request.get("priority")
    if priority is None or not isinstance(priority, (int, float)) or priority < 0.1 or priority > 10:
        raise HTTPException(status_code=400, detail="priority must be a number between 0.1 and 10")
    
    # Ищем связь bot_category
    bot_category = db.query(BotCategory).filter(
        BotCategory.public_bot_id == bot_id,
        BotCategory.category_id == category_id
    ).first()
    
    if not bot_category:
        raise HTTPException(status_code=404, detail="Category is not associated with this bot")
    
    # Обновляем приоритет
    bot_category.weight = float(priority)
    
    db.commit()
    return {"message": f"Updated priority for category {category_id} in bot {bot_id} to {priority}"}

# Bot Templates API Endpoints
@app.get("/api/bot-templates", response_model=BotTemplateSettings)
def get_bot_template_settings(db: Session = Depends(get_db)):
    """Получить все шаблонные настройки для новых ботов"""
    config = ConfigManager(db)
    
    # Получаем все настройки с префиксом DEFAULT_
    template_settings = {}
    
    # AI Settings
    template_settings['default_ai_model'] = config.get('DEFAULT_AI_MODEL', 'gpt-4o-mini')
    template_settings['default_max_tokens'] = int(config.get('DEFAULT_MAX_TOKENS', '4000'))
    template_settings['default_temperature'] = float(config.get('DEFAULT_TEMPERATURE', '0.7'))
    template_settings['default_categorization_prompt'] = config.get('DEFAULT_CATEGORIZATION_PROMPT', 
        BotTemplateSettings().default_categorization_prompt)
    template_settings['default_summarization_prompt'] = config.get('DEFAULT_SUMMARIZATION_PROMPT',
        BotTemplateSettings().default_summarization_prompt)
    
    # Digest Settings  
    template_settings['default_max_posts_per_digest'] = int(config.get('DEFAULT_MAX_POSTS_PER_DIGEST', '10'))
    template_settings['default_max_summary_length'] = int(config.get('DEFAULT_MAX_SUMMARY_LENGTH', '150'))
    template_settings['default_digest_language'] = config.get('DEFAULT_DIGEST_LANGUAGE', 'ru')
    template_settings['default_welcome_message'] = config.get('DEFAULT_WELCOME_MESSAGE',
        BotTemplateSettings().default_welcome_message)
    
    # Delivery Settings
    schedule_json = config.get('DEFAULT_DELIVERY_SCHEDULE', '{}')
    try:
        template_settings['default_delivery_schedule'] = json.loads(schedule_json) if schedule_json != '{}' else BotTemplateSettings().default_delivery_schedule
    except:
        template_settings['default_delivery_schedule'] = BotTemplateSettings().default_delivery_schedule
    
    template_settings['default_timezone'] = config.get('DEFAULT_TIMEZONE', 'Europe/Moscow')
    
    return BotTemplateSettings(**template_settings)

@app.put("/api/bot-templates", response_model=BotTemplateSettings)
def update_bot_template_settings(
    template_update: BotTemplateUpdate, 
    db: Session = Depends(get_db)
):
    """Обновить шаблонные настройки для новых ботов (bulk update)"""
    config = ConfigManager(db)
    
    # Обновляем только предоставленные поля
    update_data = template_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        # Преобразуем в формат настроек БД
        setting_key = key.upper()
        
        if key == 'default_delivery_schedule':
            # Специальная обработка для JSON
            config.set_db_setting(setting_key, json.dumps(value), 'json')
        elif isinstance(value, bool):
            config.set_db_setting(setting_key, str(value).lower(), 'boolean')
        elif isinstance(value, int):
            config.set_db_setting(setting_key, str(value), 'integer')
        elif isinstance(value, float):
            config.set_db_setting(setting_key, str(value), 'float')
        else:
            config.set_db_setting(setting_key, str(value), 'string')
    
    # Возвращаем обновленные настройки
    return get_bot_template_settings(db)

@app.get("/api/bot-templates/effective")
def get_effective_bot_settings(bot_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Получить эффективные настройки с 3-уровневым fallback:
    1. Индивидуальные настройки бота (если bot_id указан)
    2. Шаблонные настройки (DEFAULT_*)
    3. Глобальные настройки системы
    """
    config = ConfigManager(db)
    effective_settings = {}
    
    # Получаем шаблонные настройки как базу
    template_settings = get_bot_template_settings(db)
    effective_settings.update(template_settings.model_dump())
    
    # Если указан bot_id, накладываем индивидуальные настройки
    if bot_id:
        bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if bot:
            # Переопределяем настройки индивидуальными значениями бота
            if bot.categorization_prompt:
                effective_settings['categorization_prompt'] = bot.categorization_prompt
            if bot.summarization_prompt:
                effective_settings['summarization_prompt'] = bot.summarization_prompt
            if bot.max_posts_per_digest:
                effective_settings['max_posts_per_digest'] = bot.max_posts_per_digest
            if bot.max_summary_length:
                effective_settings['max_summary_length'] = bot.max_summary_length
            if bot.welcome_message:
                effective_settings['welcome_message'] = bot.welcome_message
            if bot.default_language:
                effective_settings['default_language'] = bot.default_language
            if bot.delivery_schedule:
                effective_settings['delivery_schedule'] = bot.delivery_schedule
            if bot.timezone:
                effective_settings['timezone'] = bot.timezone
    
    return {
        "bot_id": bot_id,
        "settings": effective_settings,
        "fallback_levels": {
            "individual": bot_id is not None,
            "template": True,
            "global": True
        }
    }

@app.post("/api/bot-templates/apply/{bot_id}")
def apply_template_to_bot(bot_id: int, db: Session = Depends(get_db)):
    """Применить текущие шаблонные настройки к существующему боту"""
    # Получаем бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бот не найден"
        )
    
    # Получаем шаблонные настройки
    template = get_bot_template_settings(db)
    
    # Применяем шаблон к боту (только если поля пустые)
    updated_fields = []
    
    if not bot.categorization_prompt:
        bot.categorization_prompt = template.default_categorization_prompt
        updated_fields.append("categorization_prompt")
    
    if not bot.summarization_prompt:
        bot.summarization_prompt = template.default_summarization_prompt
        updated_fields.append("summarization_prompt")
    
    if bot.max_posts_per_digest == 10:  # значение по умолчанию
        bot.max_posts_per_digest = template.default_max_posts_per_digest
        updated_fields.append("max_posts_per_digest")
    
    if bot.max_summary_length == 150:  # значение по умолчанию
        bot.max_summary_length = template.default_max_summary_length
        updated_fields.append("max_summary_length")
    
    if not bot.welcome_message:
        bot.welcome_message = template.default_welcome_message
        updated_fields.append("welcome_message")
    
    if bot.default_language == "ru" and template.default_digest_language != "ru":
        bot.default_language = template.default_digest_language
        updated_fields.append("default_language")
    
    if not bot.delivery_schedule or bot.delivery_schedule == {}:
        bot.delivery_schedule = template.default_delivery_schedule
        updated_fields.append("delivery_schedule")
    
    if bot.timezone == "Europe/Moscow" and template.default_timezone != "Europe/Moscow":
        bot.timezone = template.default_timezone
        updated_fields.append("timezone")
    
    db.commit()
    db.refresh(bot)
    
    return {
        "message": f"Шаблон применен к боту '{bot.name}'",
        "bot_id": bot_id,
        "updated_fields": updated_fields,
        "updated_count": len(updated_fields)
    }

# Создание таблиц БД - выполняется в конце после всех определений
print("🔧 Создание таблиц в базе данных...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно")
except Exception as e:
    print(f"❌ Ошибка создания таблиц: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 