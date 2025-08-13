from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Table, Float, UniqueConstraint, BigInteger, and_, or_, Index, func, JSON
from sqlalchemy.dialects.postgresql import JSONB, insert
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
import logging
import aiohttp
import asyncio
from celery import Celery

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация базы данных
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # Используем environment variable
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

# Celery client для взаимодействия с AI Services
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_client = Celery(
    "ai_services",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL
)

# CORS middleware для админ-панели (исправленная версия)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://127.0.0.1:5173", 
        "http://127.0.0.1:3000",
        "http://localhost",  # Добавляем для Docker frontend
        "http://127.0.0.1"   # Добавляем для Docker frontend
    ],
    allow_credentials=False,  # Убираем credentials для совместимости
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
    name = Column(String, nullable=False)  # Исправлено: category_name → name
    description = Column(Text)
    emoji = Column(String, default="📝")  # Восстановлено: добавлено в БД
    is_active = Column(Boolean, default=True)
    ai_prompt = Column(Text)  # Восстановлено: нужно для AI обработки
    sort_order = Column(Integer, default=0)  # Восстановлено: добавлено в БД
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    channels = relationship("Channel", secondary=channel_categories, back_populates="categories")

class Channel(Base):
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String, nullable=False)  # Основное поле для имени канала
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    title = Column(String, nullable=False) 
    description = Column(Text)
    last_parsed = Column(DateTime)
    error_count = Column(Integer, default=0)  
    is_active = Column(Boolean, default=True)
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

# 🚀 УДАЛЕНО: Дублирование таблицы user_category_subscriptions (основная определена ниже)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
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
    digest_schedule = Column(JSON, default={"enabled": False})
    
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
    channel_telegram_id = Column(BigInteger, nullable=False, index=True)
    telegram_message_id = Column(BigInteger, nullable=False)
    title = Column(Text)
    content = Column(Text)
    # Условные типы данных в зависимости от БД
    media_urls = Column(JSONB if USE_POSTGRESQL else Text, default=[] if USE_POSTGRESQL else "[]")
    views = Column(Integer, default=0)
    post_date = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, default=func.now(), nullable=False)
    userbot_metadata = Column(JSONB if USE_POSTGRESQL else Text, default={} if USE_POSTGRESQL else "{}")
    # processing_status = Column(String, default="pending")  # УБРАНО: заменено мультитенантными статусами в processed_data

# Обновляем модель Category для связи с пользователями
# 🚀 МУЛЬТИТЕНАНТНАЯ ТАБЛИЦА ПОДПИСОК (заменяет старую user_subscriptions)
user_category_subscriptions = Table(
    'user_category_subscriptions', 
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('user_telegram_id', BigInteger, nullable=False, index=True),  # 🔧 ИСПРАВЛЕНО: BigInteger для больших Telegram ID
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
    Column('public_bot_id', Integer, ForeignKey('public_bots.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
    # Уникальность: один пользователь не может дважды подписаться на одну категорию в одном боте
    UniqueConstraint('user_telegram_id', 'category_id', 'public_bot_id', name='uq_user_category_bot_subscription'),
    # Индексы для быстрого поиска
    Index('idx_user_bot_subscriptions', 'user_telegram_id', 'public_bot_id'),
    Index('idx_bot_category_subscriptions', 'public_bot_id', 'category_id'),
    extend_existing=True  # 🔧 ИСПРАВЛЕНО: позволяет переопределить существующую таблицу
)

# 🚀 МУЛЬТИТЕНАНТНАЯ ТАБЛИЦА ПОДПИСОК НА КАНАЛЫ (новая архитектура)
user_channel_subscriptions = Table(
    'user_channel_subscriptions', 
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('user_telegram_id', BigInteger, nullable=False, index=True),
    Column('channel_id', Integer, ForeignKey('channels.id', ondelete='CASCADE'), nullable=False),
    Column('public_bot_id', Integer, ForeignKey('public_bots.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
    # Уникальность: один пользователь не может дважды подписаться на один канал в одном боте
    UniqueConstraint('user_telegram_id', 'channel_id', 'public_bot_id', name='uq_user_channel_bot_subscription'),
    # Индексы для быстрого поиска
    Index('idx_user_bot_channel_subscriptions', 'user_telegram_id', 'public_bot_id'),
    Index('idx_bot_channel_user_subscriptions', 'public_bot_id', 'channel_id'),
    extend_existing=True
)

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper: сборка текста дайджеста
def _build_digest_text(grouped_posts: dict, subscribed_names: set, created_at: Optional[str] = None) -> str:
    parts = []
    parts.append("📰 Ваш персональный дайджест\n\n")
    if created_at:
        parts.append(f"🗓 Создан: {created_at}\n")

    # Темы оставим в порядке убывания количества постов
    sorted_themes = sorted(grouped_posts.items(), key=lambda t: sum(len(p) for p in t[1].values()), reverse=True)
    for theme_name, channels_map in sorted_themes:
        parts.append(f"\n📝 <b>{str(theme_name).upper()}</b>\n")
        # Каналы внутри темы оставим по количеству постов; сами посты сортируем по дате по убыванию
        for channel_name, posts in sorted(channels_map.items(), key=lambda x: len(x[1]), reverse=True):
            parts.append(f"\n📺 <b>{channel_name}</b>\n")
            posts.sort(key=lambda p: (p.get('post_date') or ''), reverse=True)
            for post in posts:
                summary = post.get('summary') or post.get('ai_summary') or ''
                url = post.get('url') or ''
                title = post.get('title') or ''
                if summary:
                    parts.append(f"💬 {summary}\n")
                if url:
                    short = title[:80] + ("..." if len(title) > 80 else "")
                    parts.append(f"🔗 {url} <i>{short}</i>\n")
                metrics = []
                for k, icon in [("importance","⚡"),("urgency","🚨"),("significance","🎯"),("views","👁")]:
                    v = post.get(k)
                    if v not in (None, 0, "0"):
                        metrics.append(f"{icon} {v}")
                if metrics:
                    parts.append(f"📊 {' • '.join(metrics)}\n")
                parts.append("\n")

    if subscribed_names:
        parts.append(f"🎯 Ваши подписки: {', '.join(sorted(subscribed_names))}\n\n")
    parts.append("💡 Используйте /subscribe для изменения подписок")
    return ''.join(parts)

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
    name: str = Field(..., min_length=1, max_length=255)  # Исправлено: category_name → name
    description: Optional[str] = None
    emoji: str = Field("📝", max_length=10)  # Восстановлено: добавлено в БД
    is_active: bool = True
    ai_prompt: Optional[str] = None  # Восстановлено: нужно для AI обработки
    sort_order: int = 0  # Восстановлено: добавлено в БД

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Больше не нужен алиас - поле называется name
    # name: str = Field(alias="category_name")
    
    class Config:
        from_attributes = True
        populate_by_name = True

class CategoryResponseWithName(BaseModel):
    id: int
    name: str  # Маппим из category_name
    description: Optional[str] = None
    is_active: bool = True
    ai_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_category(cls, category):
        return cls(
            id=category.id,
            name=category.name,  # Исправлено: используем name
            description=category.description,
            is_active=category.is_active,
            ai_prompt=category.ai_prompt,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
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

class PostCacheCreate(PostCacheBase):
    pass

class PostCacheResponse(PostCacheBase):
    id: int
    collected_at: datetime

    class Config:
        from_attributes = True

# Расширенная модель для /api/posts/unprocessed
class PostCacheResponseWithBot(PostCacheResponse):
    bot_id: int

class PostCacheWithAIResponse(PostCacheBase):
    id: int
    collected_at: datetime
    
    # AI результаты (опциональные, если пост не обработан)
    ai_summary: Optional[str] = None
    ai_category: Optional[str] = None
    ai_relevance_score: Optional[float] = None
    ai_importance: Optional[float] = None
    ai_urgency: Optional[float] = None
    ai_significance: Optional[float] = None
    ai_processed_at: Optional[datetime] = None
    ai_processing_version: Optional[str] = None
    
    class Config:
        from_attributes = True

class PostsBatchCreate(BaseModel):
    """Модель для batch создания posts от userbot"""
    timestamp: datetime
    collection_stats: Dict[str, Union[int, List[str]]]
    posts: List[PostCacheCreate]
    channels_metadata: Dict[str, Dict[str, Any]]

class PostsBulkDeleteRequest(BaseModel):
    """Модель для bulk удаления постов"""
    post_ids: List[int] = Field(..., min_items=1, max_items=1000, description="Список ID постов для удаления")
    
    class Config:
        schema_extra = {
            "example": {
                "post_ids": [1, 2, 3, 4, 5]
            }
        }

class PublicBotBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field("setup", pattern="^(setup|active|paused|development)$")  # Добавлен development
    
    # Telegram Bot данные
    bot_token: Optional[str] = None
    welcome_message: Optional[str] = None
    default_language: str = "ru"
    
    # Digest Settings (базовые)
    max_posts_per_digest: int = Field(10, ge=1, le=100)
    max_summary_length: int = Field(150, ge=50, le=2000)
    
    # AI Prompts (разделенные по функциям)
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    
    # СЛОЖНОЕ РАСПИСАНИЕ ДОСТАВКИ
    delivery_schedule: Optional[Dict[str, Any]] = {}
    timezone: str = "Europe/Moscow"
    
    # Legacy поля для совместимости
    digest_generation_time: str = Field("09:00", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    digest_schedule: Dict[str, Any] = Field(default_factory=lambda: {"enabled": False})

class PublicBotCreate(PublicBotBase):
    pass

class PublicBotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(setup|active|paused|development)$")
    
    # Telegram Bot данные
    bot_token: Optional[str] = None
    welcome_message: Optional[str] = None
    default_language: Optional[str] = None
    
    # Digest Settings (базовые)
    max_posts_per_digest: Optional[int] = Field(None, ge=1, le=100)
    max_summary_length: Optional[int] = Field(None, ge=50, le=4000)
    
    # AI Prompts (разделенные по функциям)
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    
    # СЛОЖНОЕ РАСПИСАНИЕ ДОСТАВКИ
    delivery_schedule: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = None
    
    # Legacy поля для совместимости
    digest_generation_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    digest_schedule: Optional[Dict[str, Any]] = None

class PublicBotResponse(PublicBotBase):
    id: int
    users_count: int = 0
    digests_count: int = 0
    channels_count: int = 0
    topics_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    # Вычисляемое поле для совместимости с AI Orchestrator
    is_active: bool = False  # Будет установлено в __init__
    
    def __init__(self, **data):
        super().__init__(**data)
        # Устанавливаем is_active на основе status
        self.is_active = data.get('status') == 'active'

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
    default_digest_schedule: Dict[str, Any] = Field(default_factory=lambda: {"enabled": False})

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
    default_digest_schedule: Optional[Dict[str, Any]] = None

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
@app.get("/api/categories")
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
        query = query.filter(Category.name.contains(search))
    
    categories = query.order_by(Category.name).offset(skip).limit(limit).all()
    
    # Возвращаем данные с правильным маппингом
    result = []
    for cat in categories:
        result.append({
            "id": cat.id,
            "name": cat.name,  # Исправлено: используем name
            "description": cat.description,
            "is_active": cat.is_active,
            "ai_prompt": cat.ai_prompt,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at
        })
    
    return result

@app.post("/api/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """Создать новую категорию"""
    # Проверяем уникальность имени
    existing = db.query(Category).filter(Category.name == category.name).first()
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
    print(f"=== UPDATE CATEGORY DEBUG ===")
    print(f"Category ID: {category_id}")
    print(f"Received data: {category.model_dump()}")
    print(f"====================")
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем уникальность имени (исключая текущую категорию)
    existing = db.query(Category).filter(
        Category.name == category.name,
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
                            Channel.channel_name.contains(search) | 
            Channel.username.contains(search)
        )
    
    channels = query.order_by(Channel.channel_name).offset(skip).limit(limit).all()
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
    """🚀 Получить базовую статистику (МУЛЬТИТЕНАНТНАЯ)"""
    categories_count = db.query(Category).count()
    channels_count = db.query(Channel).count()
    active_categories = db.query(Category).filter(Category.is_active == True).count()
    active_channels = db.query(Channel).filter(Channel.is_active == True).count()
    digests_count = db.query(Digest).count()
    posts_total = db.query(PostCache).count()
    
    # 🚀 МУЛЬТИТЕНАНТНАЯ статистика постов
    # Получаем активные боты для мультитенантной статистики
    active_bots = db.query(PublicBot).filter(
        PublicBot.status.in_(['active', 'development'])
    ).all()
    
    if active_bots:
        active_bot_ids = [bot.id for bot in active_bots]
        
        # Получаем каналы активных ботов
        bot_channels = db.query(BotChannel).filter(
            BotChannel.public_bot_id.in_(active_bot_ids),
            BotChannel.is_active == True
        ).all()
        
        if bot_channels:
            channel_ids = [bc.channel_id for bc in bot_channels]
            channels_info = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
            channel_telegram_ids = [ch.telegram_id for ch in channels_info]
            
            # Мультитенантная статистика по статусам
            posts_pending = db.query(PostCache.id).join(
                ProcessedData, PostCache.id == ProcessedData.post_id
            ).filter(
                ProcessedData.processing_status == 'pending',
                ProcessedData.public_bot_id.in_(active_bot_ids),
                PostCache.channel_telegram_id.in_(channel_telegram_ids)
            ).distinct().count()
            
            posts_processed = db.query(PostCache.id).join(
                ProcessedData, PostCache.id == ProcessedData.post_id
            ).filter(
                ProcessedData.processing_status == 'completed',
                ProcessedData.public_bot_id.in_(active_bot_ids),
                PostCache.channel_telegram_id.in_(channel_telegram_ids)
            ).distinct().count()
        else:
            posts_pending = 0
            posts_processed = 0
    else:
        posts_pending = 0
        posts_processed = 0
    
    # Статистика связей
    total_links = db.query(channel_categories).count()
    
    # Размер базы данных
    database_size = get_database_size()
    
    # 🔧 ИСПРАВЛЕНО: Добавляем статистику активных ботов
    total_bots = db.query(PublicBot).count()
    active_bots_count = len(active_bots)  # Используем уже посчитанных активных ботов
    
    return {
        "total_categories": categories_count,
        "active_categories": active_categories,
        "total_channels": channels_count,
        "active_channels": active_channels,
        "total_digests": digests_count,
        "total_posts": posts_total,
        "posts_pending": posts_pending,  # Теперь мультитенантная статистика
        "posts_processed": posts_processed,  # Теперь мультитенантная статистика
        "channel_category_links": total_links,
        "database_size_mb": database_size,
        # 🚀 НОВЫЕ ПОЛЯ: Статистика ботов
        "total_bots": total_bots,
        "active_bots": active_bots_count
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

# 🚀 МУЛЬТИТЕНАНТНЫЕ ENDPOINTS ДЛЯ ПОДПИСОК
@app.get("/api/public-bots/{bot_id}/users/{telegram_id}/subscriptions")
def get_user_bot_subscriptions(bot_id: int, telegram_id: int, db: Session = Depends(get_db)):
    """Получить подписки пользователя для конкретного бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бот не найден"
        )
    
    # Получаем подписки пользователя для этого бота
    subscriptions_query = db.query(Category).join(
        user_category_subscriptions,
        Category.id == user_category_subscriptions.c.category_id
    ).filter(
        user_category_subscriptions.c.user_telegram_id == telegram_id,
        user_category_subscriptions.c.public_bot_id == bot_id
    )
    
    subscriptions = subscriptions_query.all()
    
    # Преобразуем в формат CategoryResponse
    result = []
    for category in subscriptions:
        result.append({
            'id': category.id,
                    'name': category.name,
        'category_name': category.name,
            'description': category.description,
            'is_active': category.is_active,
            'ai_prompt': category.ai_prompt,
            'created_at': category.created_at,
            'updated_at': category.updated_at
        })
    
    return result


@app.get("/api/public-bots/{bot_id}/users/{telegram_id}/digest")
def get_user_personal_digest(
    bot_id: int,
    telegram_id: int,
    limit: int = Query(15, ge=1, le=50),
    date_from: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Сформировать персональный дайджест на стороне Backend.

    Логика:
    - Получаем подписки пользователя (категории и каналы) для данного бота
    - Берём обработанные AI посты из processed_data по bot_id (JOIN с posts_cache)
    - Фильтруем по индивидуальной категории поста и подпискам пользователя, а также по подписанным каналам
    - Ограничиваем количеством limit или max_posts_per_digest из public_bots
    - Группируем по теме → каналу и собираем готовый текст
    """
    # Проверяем бота и настройки
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")

    max_posts = bot.max_posts_per_digest or limit
    if limit:
        max_posts = min(max_posts, limit)

    # Подписки пользователя
    subs_categories = db.query(Category).join(
        user_category_subscriptions,
        Category.id == user_category_subscriptions.c.category_id
    ).filter(
        user_category_subscriptions.c.user_telegram_id == telegram_id,
        user_category_subscriptions.c.public_bot_id == bot_id
    ).all()

    subs_channels = db.query(Channel).join(
        user_channel_subscriptions,
        user_channel_subscriptions.c.channel_id == Channel.id
    ).filter(
        user_channel_subscriptions.c.user_telegram_id == telegram_id,
        user_channel_subscriptions.c.public_bot_id == bot_id
    ).all()

    subscribed_category_names = {c.name.lower() for c in subs_categories}
    subscribed_channel_ids = {c.id for c in subs_channels}

    # Если нет подписок по категориям, не формируем дайджест
    if not subscribed_category_names:
        try:
            logging.getLogger("main").info(
                f"digest: early-exit no category subs (bot_id={bot_id}, user_id={telegram_id})"
            )
        except Exception:
            pass
        return {
            'text': '❌ У вас нет активных подписок по категориям. Используйте /subscribe для выбора тем.',
            'total_posts': 0,
            'selected_posts': 0,
            'themes': []
        }

    # Если пользователь не подписан ни на один канал — не формируем дайджест
    if not subscribed_channel_ids:
        try:
            logging.getLogger("main").info(
                f"digest: early-exit no channel subs (bot_id={bot_id}, user_id={telegram_id})"
            )
        except Exception:
            pass
        return {
            'text': '❌ У вас нет подписанных каналов. Используйте /channels для выбора.',
            'total_posts': 0,
            'selected_posts': 0,
            'themes': []
        }

    # Посты с AI результатами для bot_id
    q = db.query(
        PostCache.id,
        PostCache.title,
        PostCache.content,
        PostCache.views,
        PostCache.post_date,
        ProcessedData.summaries,
        ProcessedData.categories,
        ProcessedData.metrics,
        ProcessedData.processed_at,
        ProcessedData.public_bot_id,
        Channel.id.label('channel_id'),
        Channel.title.label('channel_title'),
    ).join(
        ProcessedData, PostCache.id == ProcessedData.post_id
    ).join(
        Channel, Channel.telegram_id == PostCache.channel_telegram_id
    ).filter(
        ProcessedData.public_bot_id == bot_id,
        ProcessedData.is_categorized == True
    )
    # Фильтр по подписанным каналам
    if subscribed_channel_ids:
        q = q.filter(Channel.id.in_(list(subscribed_channel_ids)))
    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            q = q.filter(PostCache.post_date >= dt_from)
        except Exception:
            pass

    # Берем самые свежие по дате поста
    rows = q.order_by(PostCache.post_date.desc()).limit(200).all()

    # Фильтрация по подпискам и сбор структуры
    grouped: dict = {}
    selected_posts = 0
    for row in rows:
        # AI category
        category_name = None
        try:
            categories = row.categories if isinstance(row.categories, dict) else json.loads(row.categories)
            category_name = categories.get('category_name') or categories.get('ru') or categories.get('primary')
        except Exception:
            pass
        if not category_name:
            continue

        # Фильтр по подпискам категорий
        if subscribed_category_names and category_name.lower() not in subscribed_category_names:
            continue

        # Фильтр по подписанным каналам (если заданы подписки на каналы)
        # У нас нет прямого channel_id в запросе; в MVP пропускаем контроль channel_id, так как бот подписывает на id из справочника

        # Суммари (обязательно не пустое)
        summary = None
        try:
            summaries = row.summaries if isinstance(row.summaries, dict) else json.loads(row.summaries)
            summary = summaries.get('ru') or summaries.get('summary') or summaries.get('text')
        except Exception:
            pass
        if not summary or not str(summary).strip():
            continue

        # Метрики
        importance = urgency = significance = views = 0
        try:
            metrics = row.metrics if isinstance(row.metrics, dict) else json.loads(row.metrics)
            importance = metrics.get('importance', 0)
            urgency = metrics.get('urgency', 0)
            significance = metrics.get('significance', 0)
        except Exception:
            pass
        views = row.views or 0

        # Группировка: тема → канал
        theme = str(category_name)
        try:
            channel_title = getattr(row, 'channel_title', None) or "Канал"
        except Exception:
            channel_title = "Канал"

        grouped.setdefault(theme, {}).setdefault(channel_title, []).append({
            'title': row.title,
            'summary': summary,
            'importance': importance,
            'urgency': urgency,
            'significance': significance,
            'views': views,
            'post_date': getattr(row, 'post_date', None),
        })

        selected_posts += 1
        if selected_posts >= max_posts:
            break

    subscribed_human = {c.name for c in subs_categories}
    try:
        logging.getLogger("main").info(
            f"digest: bot_id={bot_id}, user_id={telegram_id}, subs_cat={len(subscribed_category_names)}, "
            f"subs_chan={len(subscribed_channel_ids)}, rows={len(rows)}, selected={selected_posts}"
        )
    except Exception:
        pass
    text = _build_digest_text(grouped, subscribed_human)
    return {
        'text': text,
        'total_posts': len(rows),
        'selected_posts': selected_posts,
        'themes': list(grouped.keys()),
    }

@app.post("/api/public-bots/{bot_id}/users/{telegram_id}/subscriptions")
def update_user_bot_subscriptions(
    bot_id: int, 
    telegram_id: int, 
    request: dict,  # {"category_ids": [1, 2, 3]}
    db: Session = Depends(get_db)
):
    """Обновить подписки пользователя для конкретного бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бот не найден"
        )
    
    category_ids = request.get('category_ids', [])
    
    # Проверяем существование всех категорий
    if category_ids:
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        if len(categories) != len(category_ids):
            found_ids = [cat.id for cat in categories]
            missing_ids = [cat_id for cat_id in category_ids if cat_id not in found_ids]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Категории не найдены: {missing_ids}"
            )
    
    # Удаляем все существующие подписки пользователя для этого бота
    db.execute(
        user_category_subscriptions.delete().where(
            and_(
                user_category_subscriptions.c.user_telegram_id == telegram_id,
                user_category_subscriptions.c.public_bot_id == bot_id
            )
        )
    )
    
    # Добавляем новые подписки
    if category_ids:
        for category_id in category_ids:
            db.execute(
                user_category_subscriptions.insert().values(
                    user_telegram_id=telegram_id,
                    category_id=category_id,
                    public_bot_id=bot_id
                )
            )
    
    db.commit()
    
    return {
        "message": f"Подписки для бота {bot_id} сохранены! Выбрано категорий: {len(category_ids)}",
        "user_telegram_id": telegram_id,
        "bot_id": bot_id,
        "subscribed_categories": len(category_ids),
        "category_ids": category_ids
    }

@app.delete("/api/public-bots/{bot_id}/users/{telegram_id}/subscriptions/{category_id}")
def remove_user_bot_subscription(bot_id: int, telegram_id: int, category_id: int, db: Session = Depends(get_db)):
    """Удалить конкретную подписку пользователя для бота"""
    # Проверяем существование подписки
    subscription_exists = db.execute(
        user_category_subscriptions.select().where(
            and_(
                user_category_subscriptions.c.user_telegram_id == telegram_id,
                user_category_subscriptions.c.category_id == category_id,
                user_category_subscriptions.c.public_bot_id == bot_id
            )
        )
    ).first()
    
    if not subscription_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Подписка не найдена"
        )
    
    # Удаляем подписку
    db.execute(
        user_category_subscriptions.delete().where(
            and_(
                user_category_subscriptions.c.user_telegram_id == telegram_id,
                user_category_subscriptions.c.category_id == category_id,
                user_category_subscriptions.c.public_bot_id == bot_id
            )
        )
    )
    
    db.commit()
    
    return {"message": "Подписка удалена"}

# 🚀 API для подписок пользователей на каналы (мультитенантная архитектура)

@app.get("/api/public-bots/{bot_id}/users/{telegram_id}/channel-subscriptions")
def get_user_bot_channel_subscriptions(bot_id: int, telegram_id: int, db: Session = Depends(get_db)):
    """Получить подписки пользователя на каналы для конкретного бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    
    # Получаем подписки пользователя с JOIN к каналам
    subscriptions_query = db.query(Channel).join(
        user_channel_subscriptions,
        user_channel_subscriptions.c.channel_id == Channel.id
    ).filter(
        user_channel_subscriptions.c.user_telegram_id == telegram_id,
        user_channel_subscriptions.c.public_bot_id == bot_id
    )
    
    channels = subscriptions_query.all()
    
    # Преобразуем в формат ответа
    channel_responses = []
    for channel in channels:
        channel_data = {
            "id": channel.id,
            "channel_name": channel.channel_name,
            "telegram_id": channel.telegram_id,
            "username": channel.username,
            "title": channel.title,
            "description": channel.description,
            "is_active": channel.is_active,
            "last_parsed": channel.last_parsed,
            "error_count": channel.error_count,
            "created_at": channel.created_at,
            "updated_at": channel.updated_at,
            "categories": []
        }
        channel_responses.append(channel_data)
    
    return {
        "user_telegram_id": telegram_id,
        "bot_id": bot_id,
        "subscribed_channels": channel_responses,
        "total_subscriptions": len(channel_responses)
    }

@app.post("/api/public-bots/{bot_id}/users/{telegram_id}/channel-subscriptions")
def update_user_bot_channel_subscriptions(
    bot_id: int, 
    telegram_id: int, 
    request: dict,  # {"channel_ids": [1, 2, 3]}
    db: Session = Depends(get_db)
):
    """Обновить подписки пользователя на каналы для конкретного бота"""
    # Проверяем существование бота
    bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Бот не найден")
    
    channel_ids = request.get("channel_ids", [])
    if not isinstance(channel_ids, list):
        raise HTTPException(status_code=400, detail="channel_ids должен быть массивом")
    
    # Проверяем, что все каналы существуют и привязаны к боту
    if channel_ids:
        # Проверяем что каналы существуют
        existing_channels = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
        if len(existing_channels) != len(channel_ids):
            raise HTTPException(status_code=400, detail="Некоторые каналы не найдены")
        
        # Проверяем что каналы привязаны к боту
        bot_channels = db.query(BotChannel).filter(
            BotChannel.public_bot_id == bot_id,
            BotChannel.channel_id.in_(channel_ids)
        ).all()
        
        if len(bot_channels) != len(channel_ids):
            raise HTTPException(status_code=400, detail="Некоторые каналы не привязаны к этому боту")
    
    # Удаляем все существующие подписки пользователя для этого бота
    db.execute(
        user_channel_subscriptions.delete().where(
            and_(
                user_channel_subscriptions.c.user_telegram_id == telegram_id,
                user_channel_subscriptions.c.public_bot_id == bot_id
            )
        )
    )
    
    # Добавляем новые подписки
    if channel_ids:
        for channel_id in channel_ids:
            # Проверяем, не существует ли уже такая подписка
            existing = db.execute(
                user_channel_subscriptions.select().where(
                    and_(
                        user_channel_subscriptions.c.user_telegram_id == telegram_id,
                        user_channel_subscriptions.c.channel_id == channel_id,
                        user_channel_subscriptions.c.public_bot_id == bot_id
                    )
                )
            ).first()
            
            if not existing:
                db.execute(
                    user_channel_subscriptions.insert().values(
                        user_telegram_id=telegram_id,
                        channel_id=channel_id,
                        public_bot_id=bot_id
                    )
                )
    
    db.commit()
    
    return {
        "message": "Подписки на каналы обновлены",
        "user_telegram_id": telegram_id,
        "bot_id": bot_id,
        "subscribed_channel_ids": channel_ids,
        "total_subscriptions": len(channel_ids)
    }

@app.delete("/api/public-bots/{bot_id}/users/{telegram_id}/channel-subscriptions/{channel_id}")
def remove_user_bot_channel_subscription(bot_id: int, telegram_id: int, channel_id: int, db: Session = Depends(get_db)):
    """Удалить конкретную подписку пользователя на канал для бота"""
    # Проверяем существование подписки
    subscription_exists = db.execute(
        user_channel_subscriptions.select().where(
            and_(
                user_channel_subscriptions.c.user_telegram_id == telegram_id,
                user_channel_subscriptions.c.channel_id == channel_id,
                user_channel_subscriptions.c.public_bot_id == bot_id
            )
        )
    ).first()
    
    if not subscription_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Подписка на канал не найдена"
        )
    
    # Удаляем подписку
    db.execute(
        user_channel_subscriptions.delete().where(
            and_(
                user_channel_subscriptions.c.user_telegram_id == telegram_id,
                user_channel_subscriptions.c.channel_id == channel_id,
                user_channel_subscriptions.c.public_bot_id == bot_id
            )
        )
    )
    
    db.commit()
    
    return {"message": "Подписка на канал удалена"}

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
            # Убираем processing_status так как мы убрали глобальные статусы
            post_dict.pop("processing_status", None)
            
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

@app.get("/api/posts/cache-with-ai")
def get_posts_cache_with_ai(
    skip: int = 0,
    limit: int = 100,
    channel_telegram_id: Optional[int] = None,
    processing_status: Optional[str] = None,
    ai_status: Optional[str] = None,  # all, processed, unprocessed
    ai_category: Optional[str] = None,  # фильтр по AI категории
    bot_id: Optional[int] = None,  # 🚀 НОВЫЙ ФИЛЬТР для мультитенантности
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "collected_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Получить список постов из cache с AI результатами (LEFT JOIN с processed_data)"""
    from datetime import datetime
    from sqlalchemy import func as sql_func
    
    # Базовый запрос с LEFT JOIN к processed_data
    query = db.query(
        PostCache.id,
        PostCache.channel_telegram_id,
        PostCache.telegram_message_id,
        PostCache.title,
        PostCache.content,
        PostCache.media_urls,
        PostCache.views,
        PostCache.post_date,
        PostCache.collected_at,
        PostCache.userbot_metadata,
        # AI результаты из processed_data (могут быть NULL)
        ProcessedData.summaries.label('ai_summaries'),
        ProcessedData.categories.label('ai_categories'),
        ProcessedData.metrics.label('ai_metrics'),
        ProcessedData.processed_at.label('ai_processed_at'),
        ProcessedData.processing_version.label('ai_processing_version'),
        ProcessedData.is_categorized.label('ai_is_categorized'),
        ProcessedData.is_summarized.label('ai_is_summarized')
    ).outerjoin(
        ProcessedData, 
        PostCache.id == ProcessedData.post_id
    )
    
    # 🚀 НОВЫЙ ФИЛЬТР: по bot_id (мультитенантность)
    if bot_id:
        logger.info(f"🔍 Фильтрация по bot_id={bot_id}")
        query = query.filter(ProcessedData.public_bot_id == bot_id)
    
    # Фильтр по каналу
    if channel_telegram_id:
        query = query.filter(PostCache.channel_telegram_id == channel_telegram_id)
    
    # Фильтр по статусу обработки постов (УБРАНО: processing_status больше нет в PostCache)
    # if processing_status:
    #     query = query.filter(PostCache.processing_status == processing_status)
    
    # Фильтр по статусу AI обработки
    if ai_status == "processed":
        query = query.filter(ProcessedData.id.isnot(None))
    elif ai_status == "unprocessed":
        query = query.filter(ProcessedData.id.is_(None))
    # ai_status == "all" - без дополнительного фильтра
    
    # Фильтр по AI категории
    if ai_category:
        if USE_POSTGRESQL:
            # PostgreSQL: фильтруем по JSONB полю categories
            query = query.filter(ProcessedData.categories['category_name'].astext == ai_category)
        else:
            # SQLite: фильтруем через JSON_EXTRACT
            query = query.filter(ProcessedData.categories.like(f'%"category_name": "{ai_category}"%'))
    
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
    if sort_by == "ai_processed_at":
        sort_column = ProcessedData.processed_at
    elif sort_by == "ai_importance":
        # Извлекаем importance из JSONB поля metrics
        if USE_POSTGRESQL:
            sort_column = ProcessedData.metrics['importance'].astext.cast(Float)
        else:
            sort_column = PostCache.collected_at  # fallback для SQLite
    else:
        sort_column = getattr(PostCache, sort_by, PostCache.collected_at)
    
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Выполняем запрос
    results = query.offset(skip).limit(limit).all()
    
    logger.info(f"📊 cache-with-ai: Найдено {len(results)} записей для bot_id={bot_id}")
    
    # ИСПРАВЛЕНО: отдельный count запрос для правильной пагинации
    # Создаем count запрос с теми же фильтрами, но без offset/limit
    count_query = db.query(PostCache.id).outerjoin(
        ProcessedData, 
        PostCache.id == ProcessedData.post_id
    )
    
    # Применяем те же фильтры что и к основному запросу
    if bot_id:
        count_query = count_query.filter(ProcessedData.public_bot_id == bot_id)
    
    if channel_telegram_id:
        count_query = count_query.filter(PostCache.channel_telegram_id == channel_telegram_id)
    
    if ai_status == "processed":
        count_query = count_query.filter(ProcessedData.id.isnot(None))
    elif ai_status == "unprocessed":
        count_query = count_query.filter(ProcessedData.id.is_(None))
    
    # Фильтр по AI категории в count запросе
    if ai_category:
        if USE_POSTGRESQL:
            # PostgreSQL: фильтруем по JSONB полю categories
            count_query = count_query.filter(ProcessedData.categories['category_name'].astext == ai_category)
        else:
            # SQLite: фильтруем через JSON_EXTRACT
            count_query = count_query.filter(ProcessedData.categories.like(f'%"category_name": "{ai_category}"%'))
    
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.filter(
            PostCache.content.ilike(search_pattern) |
            PostCache.title.ilike(search_pattern)
        )
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            count_query = count_query.filter(PostCache.post_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            count_query = count_query.filter(PostCache.post_date <= date_to_obj)
        except ValueError:
            pass
    
    # Получаем общее количество записей
    total_count = count_query.count()
    
    # Преобразуем результаты в удобный формат
    posts_with_ai = []
    for row in results:
        # Парсим AI результаты из JSONB
        ai_summary = None
        ai_category = None
        ai_importance = None
        ai_urgency = None
        ai_significance = None
        
        if row.ai_summaries:
            try:
                if USE_POSTGRESQL:
                    summaries = row.ai_summaries if isinstance(row.ai_summaries, dict) else json.loads(row.ai_summaries)
                else:
                    summaries = json.loads(row.ai_summaries)
                # Исправленный парсинг: сначала пробуем ru, потом старые форматы
                ai_summary = summaries.get('ru') or summaries.get('summary') or summaries.get('text')
            except (json.JSONDecodeError, AttributeError):
                pass
        
        if row.ai_categories:
            try:
                if USE_POSTGRESQL:
                    categories = row.ai_categories if isinstance(row.ai_categories, dict) else json.loads(row.ai_categories)
                else:
                    categories = json.loads(row.ai_categories)
                # ИСПРАВЛЕНО: используем правильное поле category_name из реальной структуры БД
                ai_category = categories.get('category_name') or categories.get('ru') or categories.get('primary') or categories.get('category')
                # Дополнительная проверка для "Нерелевантно"
                if not ai_category and categories.get('category_name') == 'Нерелевантно':
                    ai_category = 'Нерелевантно'
                # НОВОЕ: обрабатываем строку "None" как null
                if ai_category == 'None':
                    ai_category = None
            except (json.JSONDecodeError, AttributeError) as e:
                # УЛУЧШЕНО: логируем ошибку и пытаемся извлечь данные как строку
                print(f"DEBUG: Ошибка парсинга ai_categories для post {row.id}: {e}")
                print(f"DEBUG: raw ai_categories: {row.ai_categories}")
                # Попытка извлечь category_name из строки
                if isinstance(row.ai_categories, str) and 'category_name' in row.ai_categories:
                    try:
                        import re
                        match = re.search(r'"category_name":\s*"([^"]+)"', row.ai_categories)
                        if match:
                            ai_category = match.group(1)
                    except Exception:
                        pass
        
        if row.ai_metrics:
            try:
                if USE_POSTGRESQL:
                    metrics = row.ai_metrics if isinstance(row.ai_metrics, dict) else json.loads(row.ai_metrics)
                else:
                    metrics = json.loads(row.ai_metrics)
                ai_importance = metrics.get('importance')
                ai_urgency = metrics.get('urgency')
                ai_significance = metrics.get('significance')
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # ДОПОЛНИТЕЛЬНО: если метрики не найдены в metrics, попробуем взять из categories
        if not ai_importance and row.ai_categories:
            try:
                if USE_POSTGRESQL:
                    categories = row.ai_categories if isinstance(row.ai_categories, dict) else json.loads(row.ai_categories)
                else:
                    categories = json.loads(row.ai_categories)
                ai_importance = categories.get('importance')
                ai_urgency = categories.get('urgency')
                ai_significance = categories.get('significance')
            except (json.JSONDecodeError, AttributeError):
                pass
        
        post_data = {
            "id": row.id,
            "channel_telegram_id": row.channel_telegram_id,
            "telegram_message_id": row.telegram_message_id,
            "title": row.title,
            "content": row.content,
            "media_urls": row.media_urls if USE_POSTGRESQL else (json.loads(row.media_urls) if row.media_urls else []),
            "views": row.views,
            "post_date": row.post_date,
            "collected_at": row.collected_at,
            "userbot_metadata": row.userbot_metadata if USE_POSTGRESQL else (json.loads(row.userbot_metadata) if row.userbot_metadata else {}),
            # УБРАНО: "processing_status": row.processing_status,  # Заменено мультитенантными статусами
            # AI результаты
            "ai_summary": ai_summary,
            "ai_category": ai_category,
            "ai_importance": ai_importance,
            "ai_urgency": ai_urgency,
            "ai_significance": ai_significance,
            "ai_processed_at": row.ai_processed_at,
            "ai_processing_version": row.ai_processing_version,
            "ai_is_categorized": row.ai_is_categorized,
            "ai_is_summarized": row.ai_is_summarized
        }
        posts_with_ai.append(post_data)
    
    return {
        "posts": posts_with_ai,
        "total_count": total_count,  # ИСПРАВЛЕНО: правильный count запрос для пагинации
        "has_ai_results": any(post["ai_summary"] is not None for post in posts_with_ai)
    }

@app.get("/api/posts/stats")
def get_posts_stats(db: Session = Depends(get_db)):
    """Получить статистику posts_cache"""
    from sqlalchemy import func as sql_func
    
    # Общая статистика
    total_posts = db.query(PostCache).count()
    
    # Размер всей базы данных (включая posts_cache, processed_data и все остальные таблицы)
    total_size_mb = get_database_size()
    
    # Последнее обновление - максимальное время collected_at
    last_updated = db.query(sql_func.max(PostCache.collected_at)).scalar()
    
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
    
    # Статистика по статусам обработки (убрано для двухтабной архитектуры)
    # status_stats = db.query(
    #     PostCache.processing_status,
    #     sql_func.count(PostCache.id).label('count')
    # ).group_by(PostCache.processing_status).all()
    status_stats = []  # Пустой список для совместимости
    
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
        "total_size_mb": total_size_mb,  # Полный размер БД в МБ
        "last_updated": last_updated,    # Время последнего обновления
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
            # Убрано для двухтабной архитектуры - статусы теперь в processed_data
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

@app.put("/api/posts/cache/batch-status")
def update_posts_status_batch(
    request: dict,  # {"post_ids": [1, 2, 3], "status": "processing", "updated_at": "2025-06-24T10:00:00Z"}
    db: Session = Depends(get_db)
):
    """🔧 НОВОЕ: Батчевое обновление статусов постов для оптимизации AI Orchestrator"""
    post_ids = request.get("post_ids", [])
    new_status = request.get("status")
    
    if not post_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле 'post_ids' обязательно и не может быть пустым"
        )
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле 'status' обязательно"
        )
    
    # Валидация статуса
    valid_statuses = ["pending", "processing", "completed", "failed"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Допустимые: {valid_statuses}"
        )
    
    # Валидация количества постов
    if len(post_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимальное количество постов в батче: 100"
        )
    
    try:
        # Получаем посты для обновления
        posts = db.query(PostCache).filter(PostCache.id.in_(post_ids)).all()
        found_post_ids = {post.id for post in posts}
        missing_post_ids = set(post_ids) - found_post_ids
        
        if missing_post_ids:
            logger.warning(f"Не найдены посты с ID: {missing_post_ids}")
        
        # Обновляем статус найденных постов
        if posts:
            update_count = db.query(PostCache).filter(
                PostCache.id.in_([post.id for post in posts])
            ).update({
                "processing_status": new_status
            }, synchronize_session=False)
            
            db.commit()
            
            logger.info(f"✅ Батчево обновлено {update_count} постов на статус '{new_status}'")
            
            return {
                "message": f"Батчево обновлено {update_count} постов на статус '{new_status}'",
                "updated_count": update_count,
                "requested_count": len(post_ids),
                "found_count": len(posts),
                "missing_post_ids": list(missing_post_ids) if missing_post_ids else [],
                "status": new_status
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ни один из запрошенных постов не найден: {post_ids}"
            )
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка батчевого обновления статусов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка батчевого обновления статусов: {str(e)}"
        )

@app.get("/api/posts/cache/{post_id}", response_model=PostCacheResponse)
def get_post_by_id(post_id: int, db: Session = Depends(get_db)):
    """Получить конкретный пост по ID"""
    post = db.query(PostCache).filter(PostCache.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пост с ID {post_id} не найден"
        )
    return post

@app.put("/api/posts/cache/{post_id}/status")
def update_post_status(
    post_id: int, 
    request: dict,  # {"status": "processing"}
    db: Session = Depends(get_db)
):
    """Обновить статус обработки поста"""
    post = db.query(PostCache).filter(PostCache.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пост с ID {post_id} не найден"
        )
    
    new_status = request.get("status")
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле 'status' обязательно"
        )
    
    # Валидация статуса
    valid_statuses = ["pending", "processing", "completed", "failed"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Допустимые: {valid_statuses}"
        )
    
    post.processing_status = new_status
    db.commit()
    db.refresh(post)
    
    return {
        "message": f"Статус поста {post_id} обновлен на '{new_status}'",
        "post_id": post_id,
        "old_status": post.processing_status,
        "new_status": new_status
    }

@app.delete("/api/posts/cache/bulk-delete", response_model=dict)
def bulk_delete_posts(
    request: PostsBulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """Удалить посты по их ID"""
    try:
        post_ids = request.post_ids
        
        # Получаем посты для удаления
        posts = db.query(PostCache).filter(PostCache.id.in_(post_ids)).all()
        found_post_ids = {post.id for post in posts}
        missing_post_ids = set(post_ids) - found_post_ids
        
        if missing_post_ids:
            logger.warning(f"Не найдены посты с ID: {missing_post_ids}")
        
        # Удаляем найденные посты
        if posts:
            post_ids_list = [post.id for post in posts]
            
            # 📊 ПОДСЧЕТ СВЯЗАННЫХ ДАННЫХ ДЛЯ ОТЧЕТНОСТИ
            # Считаем записи в processed_data перед удалением
            processed_data_count = db.query(ProcessedData).filter(
                ProcessedData.post_id.in_(post_ids_list)
            ).count()
            
            # Считаем записи в processed_service_results перед удалением  
            service_results_count = db.query(ProcessedServiceResult).filter(
                ProcessedServiceResult.post_id.in_(post_ids_list)
            ).count()
            
            # 🗑️ УДАЛЕНИЕ СВЯЗАННЫХ AI ДАННЫХ (согласно Data_Structure.md)
            # 1. Удаляем из processed_data (основная таблица AI результатов)
            deleted_processed_data = db.query(ProcessedData).filter(
                ProcessedData.post_id.in_(post_ids_list)
            ).delete(synchronize_session=False)
            
            # 2. Удаляем из processed_service_results (журнальная таблица AI сервисов)
            deleted_service_results = db.query(ProcessedServiceResult).filter(
                ProcessedServiceResult.post_id.in_(post_ids_list)
            ).delete(synchronize_session=False)
            
            # 3. Удаляем основные посты из posts_cache
            deleted_posts = db.query(PostCache).filter(
                PostCache.id.in_(post_ids_list)
            ).delete(synchronize_session=False)
            
            db.commit()
            
            logger.info(f"✅ Bulk delete завершен: {deleted_posts} постов, {deleted_processed_data} processed_data, {deleted_service_results} service_results")
            
            return {
                "message": f"Удалено {deleted_posts} постов с полной очисткой AI данных",
                "deleted_count": deleted_posts,
                "deleted_processed_data": deleted_processed_data,
                "deleted_service_results": deleted_service_results,
                "requested_count": len(post_ids),
                "found_count": len(posts),
                "missing_post_ids": list(missing_post_ids) if missing_post_ids else [],
                "cleanup_summary": {
                    "posts_cache": deleted_posts,
                    "processed_data": deleted_processed_data, 
                    "processed_service_results": deleted_service_results,
                    "total_ai_records_cleaned": deleted_processed_data + deleted_service_results
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ни один из запрошенных постов не найден: {post_ids}"
            )
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка удаления постов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления постов: {str(e)}"
        )

@app.delete("/api/posts/cache/{post_id}")
def delete_post_by_id(post_id: int, db: Session = Depends(get_db)):
    """🔧 НОВЫЙ ЭНДПОИНТ: Удалить конкретный пост и все связанные AI результаты"""
    try:
        # Проверяем существование поста
        post = db.query(PostCache).filter(PostCache.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пост с ID {post_id} не найден"
            )
        
        # Удаляем связанные AI результаты из processed_data
        processed_data_count = db.query(ProcessedData).filter(
            ProcessedData.post_id == post_id
        ).count()
        
        db.query(ProcessedData).filter(
            ProcessedData.post_id == post_id
        ).delete(synchronize_session=False)
        
        # Удаляем связанные записи из processed_service_results
        service_results_count = db.query(ProcessedServiceResult).filter(
            ProcessedServiceResult.post_id == post_id
        ).count()
        
        db.query(ProcessedServiceResult).filter(
            ProcessedServiceResult.post_id == post_id
        ).delete(synchronize_session=False)
        
        # Удаляем сам пост
        db.query(PostCache).filter(PostCache.id == post_id).delete()
        
        db.commit()
        
        logger.info(f"✅ Удален пост {post_id} с {processed_data_count} AI результатами и {service_results_count} сервисными записями")
        
        return {
            "message": f"Пост {post_id} и все связанные данные успешно удалены",
            "post_id": post_id,
            "deleted_processed_data": processed_data_count,
            "deleted_service_results": service_results_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка удаления поста {post_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления поста: {str(e)}"
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

@app.delete("/api/ai/results/bulk-delete", response_model=dict)
def bulk_delete_ai_results(
    request: PostsBulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """🧠 УДАЛИТЬ ТОЛЬКО AI РЕЗУЛЬТАТЫ (НЕ ТРОГАЯ ОРИГИНАЛЬНЫЕ ПОСТЫ)
    
    Специально для AI RESULTS таба - удаляет только AI данные из:
    - processed_data (основная таблица AI результатов)
    - processed_service_results (журнальная таблица AI сервисов)
    
    НЕ ТРОГАЕТ posts_cache - оригинальные посты остаются в системе!
    """
    try:
        post_ids = request.post_ids
        
        # Проверяем существование постов (но НЕ удаляем их)
        existing_posts = db.query(PostCache).filter(PostCache.id.in_(post_ids)).all()
        found_post_ids = {post.id for post in existing_posts}
        missing_post_ids = set(post_ids) - found_post_ids
        
        if missing_post_ids:
            logger.warning(f"Не найдены посты с ID: {missing_post_ids}")
        
        # Подсчитываем AI данные перед удалением
        processed_data_count = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(post_ids)
        ).count()
        
        service_results_count = db.query(ProcessedServiceResult).filter(
            ProcessedServiceResult.post_id.in_(post_ids)
        ).count()
        
        # 🗑️ УДАЛЯЕМ ТОЛЬКО AI ДАННЫЕ (посты остаются!)
        # 1. Удаляем из processed_data (основная таблица AI результатов)
        deleted_processed_data = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(post_ids)
        ).delete(synchronize_session=False)
        
        # 2. Удаляем из processed_service_results (журнальная таблица AI сервисов)
        deleted_service_results = db.query(ProcessedServiceResult).filter(
            ProcessedServiceResult.post_id.in_(post_ids)
        ).delete(synchronize_session=False)
        
        # ✅ posts_cache НЕ ТРОГАЕМ - посты остаются в системе!
        
        db.commit()
        
        logger.info(f"✅ Удалены только AI результаты: {deleted_processed_data} processed_data, {deleted_service_results} service_results. Посты сохранены!")
        
        return {
            "message": f"Удалены AI результаты для {len(found_post_ids)} постов (посты сохранены)",
            "deleted_ai_results": deleted_processed_data + deleted_service_results,
            "deleted_processed_data": deleted_processed_data,
            "deleted_service_results": deleted_service_results,
            "posts_preserved": len(found_post_ids),  # Количество сохраненных постов
            "requested_count": len(post_ids),
            "found_post_ids": list(found_post_ids),
            "missing_post_ids": list(missing_post_ids) if missing_post_ids else [],
            "cleanup_summary": {
                "posts_cache": 0,  # Посты НЕ удалены!
                "processed_data": deleted_processed_data,
                "processed_service_results": deleted_service_results,
                "total_ai_records_cleaned": deleted_processed_data + deleted_service_results,
                "posts_preserved": len(found_post_ids)
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка удаления AI результатов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления AI результатов: {str(e)}"
        )

# ==================== USERBOT API ====================

@app.post("/api/userbot/run")
async def run_userbot_manual(db: Session = Depends(get_db)):
    """Запуск userbot для однократного сбора постов"""
    try:
        import subprocess
        import asyncio
        
        # Получаем статистику до запуска
        stats_before = db.query(PostCache).count()
        
        logger.info("🚀 Запуск userbot для сбора постов...")
        
        # Запускаем userbot перезапуск через docker-compose
        try:
            # Выполняем команду перезапуска userbot контейнера
            result = subprocess.run(
                ["docker-compose", "restart", "userbot"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker-compose restart failed: {result.stderr}")
                
            logger.info("✅ Userbot контейнер перезапущен")
            
        except subprocess.TimeoutExpired:
            raise Exception("Timeout при перезапуске userbot")
        except FileNotFoundError:
            # Fallback: если docker-compose не найден, используем docker напрямую
            result = subprocess.run(
                ["docker", "restart", "morningstar_userbot"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Docker restart failed: {result.stderr}")
        
        # Ждем немного для завершения сбора
        await asyncio.sleep(15)
        
        # Получаем статистику после запуска
        stats_after = db.query(PostCache).count()
        posts_collected = stats_after - stats_before
        
        # Получаем активные каналы для статистики
        active_channels = db.query(Channel).filter(Channel.is_active == True).count()
        
        logger.info(f"✅ Userbot запущен. Собрано новых постов: {posts_collected}")
        
        return {
            "success": True,
            "message": "Userbot успешно запущен",
            "posts_collected": posts_collected,
            "active_channels": active_channels,
            "container_status": "restarted"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска userbot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка запуска userbot: {str(e)}"
        )

@app.get("/api/userbot/status")
def get_userbot_status(db: Session = Depends(get_db)):
    """Получить статус userbot контейнера"""
    try:
        import subprocess
        
        # Проверяем статус userbot контейнера
        try:
            result = subprocess.run(
                ["docker", "inspect", "morningstar_userbot", "--format", "{{.State.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            container_status = result.stdout.strip() if result.returncode == 0 else "unknown"
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            container_status = "unknown"
        
        # Получаем статистику
        total_posts = db.query(PostCache).count()
        active_channels = db.query(Channel).filter(Channel.is_active == True).count()
        
        # Считаем посты за сегодня
        today = datetime.now().date()
        today_posts = db.query(PostCache).filter(
            func.date(PostCache.created_at) == today
        ).count()
        
        return {
            "container_status": container_status,
            "total_posts": total_posts,
            "today_posts": today_posts,
            "active_channels": active_channels,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса userbot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения статуса: {str(e)}"
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
        bot_data = bot.model_dump()
        
        # Применяем шаблонные значения для пустых полей
        if not bot_data.get('categorization_prompt'):
            bot_data['categorization_prompt'] = template.default_categorization_prompt
        
        if not bot_data.get('summarization_prompt'):
            bot_data['summarization_prompt'] = template.default_summarization_prompt
        
        if not bot_data.get('welcome_message'):
            bot_data['welcome_message'] = template.default_welcome_message
        
        # Исправленная логика для integer полей - проверяем на пустые значения и значения по умолчанию
        if not bot_data.get('max_posts_per_digest') or bot_data.get('max_posts_per_digest') == 10:
            bot_data['max_posts_per_digest'] = template.default_max_posts_per_digest
        
        # КРИТИЧНО: проверяем на пустую строку, None и значение по умолчанию
        max_summary = bot_data.get('max_summary_length')
        if not max_summary or max_summary == "" or max_summary == 150:
            bot_data['max_summary_length'] = template.default_max_summary_length
        
        if not bot_data.get('delivery_schedule') or bot_data.get('delivery_schedule') == {}:
            bot_data['delivery_schedule'] = template.default_delivery_schedule
        
        if not bot_data.get('digest_schedule') or bot_data.get('digest_schedule') == {"enabled": False}:
            bot_data['digest_schedule'] = template.default_digest_schedule
        
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
    db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бот не найден"
        )
    return db_bot

@app.post("/api/telegram-bot/validate-token")
async def validate_telegram_bot_token(request: dict):
    """Валидация токена Telegram бота и получение информации о боте"""
    bot_token = request.get("bot_token")
    if not bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле bot_token обязательно"
        )
    
    # Проверяем формат токена
    if not bot_token or len(bot_token.split(':')) != 2:
        return {
            "valid": False,
            "error": "Неверный формат токена. Ожидается формат: BOT_ID:TOKEN"
        }
    
    try:
        # Делаем запрос к Telegram Bot API
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(telegram_api_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok") and "result" in data:
                        bot_info = data["result"]
                        
                        return {
                            "valid": True,
                            "bot_info": {
                                "id": bot_info.get("id"),
                                "username": bot_info.get("username"),
                                "first_name": bot_info.get("first_name"),
                                "is_bot": bot_info.get("is_bot"),
                                "can_join_groups": bot_info.get("can_join_groups"),
                                "can_read_all_group_messages": bot_info.get("can_read_all_group_messages"),
                                "supports_inline_queries": bot_info.get("supports_inline_queries")
                            }
                        }
                    else:
                        return {
                            "valid": False,
                            "error": "Telegram API вернул ошибку"
                        }
                elif response.status == 401:
                    return {
                        "valid": False,
                        "error": "Неверный токен бота"
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Ошибка Telegram API: {response.status}"
                    }
                    
    except asyncio.TimeoutError:
        return {
            "valid": False,
            "error": "Превышено время ожидания ответа от Telegram API"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Ошибка при валидации токена: {str(e)}"
        }

@app.post("/api/public-bots/{bot_id}/sync-telegram-data")
async def sync_bot_telegram_data(bot_id: int, request: dict, db: Session = Depends(get_db)):
    """Синхронизация данных бота с Telegram API"""
    bot_token = request.get("bot_token")
    if not bot_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле bot_token обязательно"
        )
    
    # Проверяем существование бота
    db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
    if not db_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Бот не найден"
        )
    
    try:
        # Валидируем токен и получаем данные бота
        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(telegram_api_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok") and "result" in data:
                        bot_info = data["result"]
                        
                        # Обновляем имя бота и токен
                        old_name = db_bot.name
                        new_name = bot_info.get("first_name", "")
                        
                        if new_name:
                            db_bot.name = new_name
                        db_bot.bot_token = bot_token
                        
                        db.commit()
                        db.refresh(db_bot)
                        
                        return {
                            "success": True,
                            "message": f"Данные бота обновлены",
                            "old_name": old_name,
                            "new_name": new_name,
                            "bot_info": {
                                "id": bot_info.get("id"),
                                "username": bot_info.get("username"),
                                "first_name": bot_info.get("first_name"),
                                "is_bot": bot_info.get("is_bot")
                            }
                        }
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Telegram API вернул ошибку"
                        )
                elif response.status == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Неверный токен бота"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ошибка Telegram API: {response.status}"
                    )
                    
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Превышено время ожидания ответа от Telegram API"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при синхронизации данных бота: {str(e)}"
        )

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
    """Переключить статус бота (active ↔ paused ↔ development)"""
    try:
        db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not db_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # Циклическое переключение статусов: setup → active → paused → development → active
        if db_bot.status == "setup":
            db_bot.status = "active"
        elif db_bot.status == "active":
            db_bot.status = "paused"
        elif db_bot.status == "paused":
            db_bot.status = "development"
        elif db_bot.status == "development":
            db_bot.status = "active"
        else:  # fallback для неизвестных статусов
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

@app.post("/api/public-bots/{bot_id}/set-status")
def set_bot_status(bot_id: int, request: dict, db: Session = Depends(get_db)):
    """Установить конкретный статус бота"""
    try:
        new_status = request.get("status")
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Поле 'status' обязательно"
            )
        
        # Валидация статуса
        valid_statuses = ["setup", "active", "paused", "development"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый статус. Допустимые: {', '.join(valid_statuses)}"
            )
        
        db_bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not db_bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        old_status = db_bot.status
        db_bot.status = new_status
        
        db.commit()
        db.refresh(db_bot)
        
        return {
            "message": f"Статус бота '{db_bot.name}' изменен с '{old_status}' на '{new_status}'",
            "bot_id": bot_id,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка установки статуса бота: {str(e)}"
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
@app.get("/api/public-bots/{bot_id}/digest-data")
def get_bot_digest_data(
    bot_id: int, 
    limit: int = 15,
    importance_min: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Получить AI-обработанные посты для дайджеста конкретного бота
    """
    try:
        # Получаем каналы бота
        bot_channels = db.query(BotChannel).filter(
            BotChannel.public_bot_id == bot_id,
            BotChannel.is_active == True
        ).all()
        
        if not bot_channels:
            return {"posts": [], "total": 0, "bot_id": bot_id}
        
        channel_ids = [bc.channel_id for bc in bot_channels]
        
        # Получаем telegram_id каналов
        channels = db.query(Channel).filter(
            Channel.id.in_(channel_ids),
            Channel.is_active == True
        ).all()
        
        channel_telegram_ids = [ch.telegram_id for ch in channels]
        
        # Основной запрос постов с AI результатами
        query = db.query(
            PostCache,
            ProcessedData.summaries,
            ProcessedData.categories,
            ProcessedData.metrics,
            ProcessedData.processed_at
        ).outerjoin(
            ProcessedData,
            and_(
                PostCache.id == ProcessedData.post_id,
                ProcessedData.public_bot_id == bot_id
            )
        ).filter(
            PostCache.channel_telegram_id.in_(channel_telegram_ids),
            ProcessedData.processing_status.in_(['completed', 'categorized', 'summarized']),  # Более мягкие фильтры
            ProcessedData.is_categorized == True  # Хотя бы категоризировано
        )
        
        # Фильтр по важности
        if importance_min is not None:
            # Извлекаем importance из JSON metrics с защитой от NULL
            query = query.filter(
                text(f"COALESCE(CAST(processed_data.metrics->>'importance' AS FLOAT), 0) >= {importance_min}")
            )
        
        # Сортировка по важности (умная сортировка) - только если есть данные
        query = query.order_by(
            text("COALESCE(CAST(processed_data.metrics->>'importance' AS FLOAT), 0) * 3 + COALESCE(CAST(processed_data.metrics->>'urgency' AS FLOAT), 0) * 2 + COALESCE(CAST(processed_data.metrics->>'significance' AS FLOAT), 0) * 2 DESC")
        )
        
        # Применяем лимит
        results = query.limit(limit).all()
        
        # Формируем ответ
        posts = []
        for post_cache, summaries, categories, metrics, processed_at in results:
            # Парсим JSON поля
            try:
                summaries_data = json.loads(summaries) if summaries else {}
                categories_data = json.loads(categories) if categories else {}
                metrics_data = json.loads(metrics) if metrics else {}
            except:
                summaries_data = {}
                categories_data = {}
                metrics_data = {}
            
            post_data = {
                "id": post_cache.id,
                "channel_telegram_id": post_cache.channel_telegram_id,
                "telegram_message_id": post_cache.telegram_message_id,
                "title": post_cache.title,
                "content": post_cache.content,
                "views": post_cache.views,
                "post_date": post_cache.post_date.isoformat(),
                "collected_at": post_cache.collected_at.isoformat(),
                
                # AI результаты
                "ai_summary": summaries_data.get('summary', ''),
                "ai_category": categories_data.get('primary_category', ''),
                "importance": metrics_data.get('importance', 0),
                "urgency": metrics_data.get('urgency', 0),
                "significance": metrics_data.get('significance', 0),
                "ai_processed_at": processed_at.isoformat() if processed_at else None,
                
                # Дополнительные поля
                "category": categories_data.get('primary_category', ''),
                "summary": summaries_data.get('summary', ''),
                "media_urls": json.loads(post_cache.media_urls) if post_cache.media_urls else []
            }
            
            posts.append(post_data)
        
        return {
            "posts": posts,
            "total": len(posts),
            "bot_id": bot_id,
            "importance_min": importance_min,
            "limit": limit
        }
        
    except Exception as e:
        print(f"Ошибка получения digest data: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

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
                "name": category.name,  # основное имя по Data_Structure.md
                "category_name": category.name,  # alias для обратной совместимости
                "description": category.description,
                "emoji": getattr(category, "emoji", None),
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
    
    # Digest Schedule Settings
    digest_schedule_json = config.get('DEFAULT_DIGEST_SCHEDULE', '{"enabled": false}')
    try:
        template_settings['default_digest_schedule'] = json.loads(digest_schedule_json) if digest_schedule_json != '{"enabled": false}' else BotTemplateSettings().default_digest_schedule
    except:
        template_settings['default_digest_schedule'] = BotTemplateSettings().default_digest_schedule
    
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

# === AI PROCESSED DATA MODEL ===
class ProcessedData(Base):
    __tablename__ = "processed_data"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(BigInteger, nullable=False)  # Изменено: BigInteger без FK
    public_bot_id = Column(Integer, nullable=False)  # Убран FK из-за партиционирования
    summaries = Column(JSONB if USE_POSTGRESQL else Text, nullable=False)
    categories = Column(JSONB if USE_POSTGRESQL else Text, nullable=False)
    metrics = Column(JSONB if USE_POSTGRESQL else Text, nullable=False)
    processed_at = Column(DateTime, default=func.now())
    processing_version = Column(String, default="v3.1")
    processing_status = Column(String, default="pending", nullable=False)  # Итоговый агрегированный статус
    is_categorized = Column(Boolean, default=False, nullable=False)
    is_summarized = Column(Boolean, default=False, nullable=False)
    __table_args__ = (UniqueConstraint('post_id', 'public_bot_id', name='uq_processed_post_bot'),)

# НОВАЯ ТАБЛИЦА ДЛЯ РАСШИРЯЕМЫХ РЕЗУЛЬТАТОВ СЕРВИСОВ
class ProcessedServiceResult(Base):
    __tablename__ = "processed_service_results"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(BigInteger, nullable=False)
    public_bot_id = Column(Integer, nullable=False)
    service_name = Column(String(64), nullable=False)
    status = Column(String(32), default="success")
    payload = Column(JSONB if USE_POSTGRESQL else Text, nullable=False, default={})
    metrics = Column(JSONB if USE_POSTGRESQL else Text, nullable=False, default={})
    processed_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('post_id', 'public_bot_id', 'service_name', name='uq_psr_post_bot_service'),
        Index('idx_psr_post_bot_service', 'post_id', 'public_bot_id', 'service_name'),
    )

# Создание таблиц БД - выполняется в конце после всех определений
print("🔧 Создание таблиц в базе данных...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно")
except Exception as e:
    print(f"❌ Ошибка создания таблиц: {e}")


# === Pydantic схемы ===
class AIResultCreate(BaseModel):
    post_id: int
    public_bot_id: int
    summaries: Dict[str, Any]
    categories: Dict[str, Any]
    metrics: Dict[str, Any]
    processing_version: str = "v3.1"

class AIResultResponse(AIResultCreate):
    id: int
    processed_at: datetime
    class Config:
        from_attributes = True

# Pydantic модели для новой архитектуры
class ProcessedServiceResultCreate(BaseModel):
    post_id: int
    public_bot_id: int
    service_name: str
    status: str = "success"
    payload: Dict[str, Any]
    metrics: Dict[str, Any] = {}

class ServiceResultsBatch(BaseModel):
    service: str
    results: List[ProcessedServiceResultCreate]

# === Новый запрос для синхронизации статусов ===
class SyncStatusRequest(BaseModel):
    post_ids: List[int]
    bot_id: int
    service: str  # 'categorizer' | 'summarizer'

# === API ENDPOINTS ДЛЯ AI SERVICE ===
@app.post("/api/ai/results", response_model=AIResultResponse, status_code=status.HTTP_201_CREATED)
def create_ai_result(result: AIResultCreate, db: Session = Depends(get_db)):
    existing = db.query(ProcessedData).filter_by(post_id=result.post_id, public_bot_id=result.public_bot_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Result already exists")
    
    # Определяем флаги на основе содержимого
    # Проверяем, что categories содержит реальные данные
    has_valid_categories = False
    if result.categories:
        for key, value in result.categories.items():
            if value and str(value).strip():
                has_valid_categories = True
                break
    
    # Проверяем, что summaries содержит реальные данные
    has_valid_summaries = False
    if result.summaries:
        for key, value in result.summaries.items():
            if value and str(value).strip():
                has_valid_summaries = True
                break
    
    is_categorized = has_valid_categories
    is_summarized = has_valid_summaries
    
    # Пересчитываем статус на основе флагов
    if not is_categorized and not is_summarized:
        processing_status = "pending"
    elif is_categorized and is_summarized:
        processing_status = "completed"
    else:
        processing_status = "processing"
    
    record = ProcessedData(
        post_id=result.post_id,
        public_bot_id=result.public_bot_id,
        summaries=result.summaries if USE_POSTGRESQL else json.dumps(result.summaries, ensure_ascii=False),
        categories=result.categories if USE_POSTGRESQL else json.dumps(result.categories, ensure_ascii=False),
        metrics=result.metrics if USE_POSTGRESQL else json.dumps(result.metrics, ensure_ascii=False),
        processing_version=result.processing_version,
        is_categorized=is_categorized,
        is_summarized=is_summarized,
        processing_status=processing_status
    )
    db.add(record)
    # Больше не трогаем глобальный статус в posts_cache (мультитенантность)
    db.commit()
    db.refresh(record)
    return record

@app.post("/api/ai/results/batch", response_model=List[AIResultResponse], status_code=status.HTTP_201_CREATED)
def create_ai_results_batch(results: List[AIResultCreate], db: Session = Depends(get_db)):
    created_records = []
    updated_records = []
    
    for res in results:
        # Проверяем существующую запись
        existing_record = db.query(ProcessedData).filter_by(post_id=res.post_id, public_bot_id=res.public_bot_id).first()
        
        # Определяем флаги на основе содержимого
        # Проверяем, что categories содержит реальные данные
        has_valid_categories = False
        if res.categories:
            # Проверяем наличие хотя бы одной непустой категории
            for key, value in res.categories.items():
                if value and str(value).strip():
                    has_valid_categories = True
                    break
        
        # Проверяем, что summaries содержит реальные данные
        has_valid_summaries = False
        if res.summaries:
            # Проверяем наличие хотя бы одного непустого summary
            for key, value in res.summaries.items():
                if value and str(value).strip():
                    has_valid_summaries = True
                    break
        
        is_categorized = has_valid_categories
        is_summarized = has_valid_summaries
        
        # Пересчитываем статус на основе флагов
        if not is_categorized and not is_summarized:
            processing_status = "pending"
        elif is_categorized and is_summarized:
            processing_status = "completed"
        else:
            processing_status = "processing"
        
        if existing_record:
            # ОБНОВЛЯЕМ существующую запись
            existing_record.summaries = res.summaries if USE_POSTGRESQL else json.dumps(res.summaries, ensure_ascii=False)
            existing_record.categories = res.categories if USE_POSTGRESQL else json.dumps(res.categories, ensure_ascii=False)
            existing_record.metrics = res.metrics if USE_POSTGRESQL else json.dumps(res.metrics, ensure_ascii=False)
            existing_record.processing_version = res.processing_version
            existing_record.is_categorized = is_categorized
            existing_record.is_summarized = is_summarized
            existing_record.processing_status = processing_status
            existing_record.processed_at = func.now()
            updated_records.append(existing_record)
        else:
            # СОЗДАЕМ новую запись
            r = ProcessedData(
                post_id=res.post_id,
                public_bot_id=res.public_bot_id,
                summaries=res.summaries if USE_POSTGRESQL else json.dumps(res.summaries, ensure_ascii=False),
                categories=res.categories if USE_POSTGRESQL else json.dumps(res.categories, ensure_ascii=False),
                metrics=res.metrics if USE_POSTGRESQL else json.dumps(res.metrics, ensure_ascii=False),
                processing_version=res.processing_version,
                is_categorized=is_categorized,
                is_summarized=is_summarized,
                processing_status=processing_status
            )
            db.add(r)
            created_records.append(r)
        
        # Больше не трогаем глобальный статус в posts_cache (мультитенантность)
    
    db.commit()
    
    # Обновляем записи после commit
    for r in created_records + updated_records:
        db.refresh(r)
    
    logger.info(f"✅ Batch AI results: создано {len(created_records)}, обновлено {len(updated_records)}")
    return created_records + updated_records

@app.get("/api/ai/results", response_model=List[AIResultResponse])
def get_ai_results(
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    bot_id: Optional[int] = None,
    post_id: Optional[int] = None,
    processing_version: Optional[str] = None,
    sort_by: str = "processed_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Получение AI результатов с фильтрацией"""
    query = db.query(ProcessedData)
    
    # Фильтры
    if bot_id:
        query = query.filter(ProcessedData.public_bot_id == bot_id)
    if post_id:
        query = query.filter(ProcessedData.post_id == post_id)
    if processing_version:
        query = query.filter(ProcessedData.processing_version == processing_version)
    
    # Сортировка
    if sort_by == "processed_at":
        if sort_order == "desc":
            query = query.order_by(ProcessedData.processed_at.desc())
        else:
            query = query.order_by(ProcessedData.processed_at.asc())
    elif sort_by == "post_id":
        if sort_order == "desc":
            query = query.order_by(ProcessedData.post_id.desc())
        else:
            query = query.order_by(ProcessedData.post_id.asc())
    
    return query.offset(skip).limit(limit).all()

@app.get("/api/posts/unprocessed", response_model=List[PostCacheResponseWithBot])
def get_unprocessed_posts(
    bot_id: int = Query(..., description="Bot ID for filtering processed posts - REQUIRED"),
    limit: int = Query(500, ge=1, le=1000), # Увеличен лимит по умолчанию
    channel_telegram_ids: Optional[str] = Query(None, description="Comma-separated list of channel telegram IDs"),
    require_categorization: Optional[bool] = Query(None, description="Only posts that need categorization"),
    require_summarization: Optional[bool] = Query(None, description="Only posts that need summarization"),
    db: Session = Depends(get_db)
):
    """✅ УНИВЕРСАЛЬНЫЙ ENDPOINT для v4 и v5: Поддержка фильтрации для параллельной архитектуры"""
    
    # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Фильтрация по каналам бота
    # Получаем каналы бота
    bot_channels = db.query(BotChannel).filter(
        BotChannel.public_bot_id == bot_id,
        BotChannel.is_active == True
    ).all()
    
    if not bot_channels:
        return []  # У бота нет каналов - нет постов для обработки
    
    channel_ids = [bc.channel_id for bc in bot_channels]
    
    # Получаем telegram_id каналов
    channels = db.query(Channel).filter(
        Channel.id.in_(channel_ids),
        Channel.is_active == True
    ).all()
    
    bot_channel_telegram_ids = [ch.telegram_id for ch in channels]
    
    if not bot_channel_telegram_ids:
        return []  # У бота нет активных каналов
    
    # Базовый запрос с фильтрацией по каналам бота
    query = db.query(PostCache).filter(
        PostCache.channel_telegram_id.in_(bot_channel_telegram_ids)
    )
    
    # Фильтр по каналам (если передан Query параметр channel_telegram_ids)
    if channel_telegram_ids:
        try:
            channel_ids_list = [int(cid.strip()) for cid in channel_telegram_ids.split(',') if cid.strip()]
            if channel_ids_list:
                query = query.filter(PostCache.channel_telegram_id.in_(channel_ids_list))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некорректные channel_telegram_ids"
            )
    
    # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Умная дедупликация по сервисам
    # Не добавляем общую дедупликацию здесь - она будет специфична для каждого сервиса ниже
    
    # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Фильтрация по processed_service_results
    if require_categorization or require_summarization:
        if require_categorization:
            # 🎯 УМНАЯ ДЕДУПЛИКАЦИЯ: Исключаем посты уже обрабатываемые или готовые по категоризации
            # ИСКЛЮЧАЕМ: 1) processing статус, 2) success БЕЗ payload.error (реальные результаты)
            # НЕ ИСКЛЮЧАЕМ: success С payload.error (fallback результаты)
            
            # Подзапрос: посты в processing (точно исключаем)
            processing_posts = db.query(ProcessedServiceResult.post_id).filter(
                ProcessedServiceResult.public_bot_id == bot_id,
                ProcessedServiceResult.service_name == 'categorization',
                ProcessedServiceResult.status == 'processing'
            ).subquery()
            
            # Подзапрос: посты с completed статусом БЕЗ payload.error (реальные успешные результаты)
            if USE_POSTGRESQL:
                real_success_posts = db.query(ProcessedServiceResult.post_id).filter(
                    ProcessedServiceResult.public_bot_id == bot_id,
                    ProcessedServiceResult.service_name == 'categorization',
                    ProcessedServiceResult.status == 'completed',
                    ~ProcessedServiceResult.payload.has_key('error')  # PostgreSQL: нет ключа 'error'
                ).subquery()
            else:
                # SQLite fallback: проверяем что payload не содержит "error"
                real_success_posts = db.query(ProcessedServiceResult.post_id).filter(
                    ProcessedServiceResult.public_bot_id == bot_id,
                    ProcessedServiceResult.service_name == 'categorization',
                    ProcessedServiceResult.status == 'completed',
                    ~ProcessedServiceResult.payload.like('%"error"%')
                ).subquery()
            
            # Исключаем обе группы постов
            query = query.filter(
                ~PostCache.id.in_(processing_posts),
                ~PostCache.id.in_(real_success_posts)
            )
            
            logger.info(f"🛡️ Умная дедупликация категоризации: исключены processing + success без payload.error для бота {bot_id}")
        
        elif require_summarization:
            # 🎯 Дедупликация для саммаризации: НЕ брать уже обрабатываемые/готовые саммари
            # Зависимость от успешной категоризации временно снята для параллельной отладки

            # Подзапрос: посты в processing по саммаризации
            processing_summarization = db.query(ProcessedServiceResult.post_id).filter(
                ProcessedServiceResult.public_bot_id == bot_id,
                ProcessedServiceResult.service_name == 'summarization', 
                ProcessedServiceResult.status == 'processing'
            ).subquery()

            # Подзапрос: посты с РЕАЛЬНОЙ успешной саммаризацией (без payload.error)
            if USE_POSTGRESQL:
                real_success_summarization = db.query(ProcessedServiceResult.post_id).filter(
                    ProcessedServiceResult.public_bot_id == bot_id,
                    ProcessedServiceResult.service_name == 'summarization',
                    ProcessedServiceResult.status == 'completed',
                    ~ProcessedServiceResult.payload.has_key('error')
                ).subquery()
            else:
                real_success_summarization = db.query(ProcessedServiceResult.post_id).filter(
                    ProcessedServiceResult.public_bot_id == bot_id,
                    ProcessedServiceResult.service_name == 'summarization',
                    ProcessedServiceResult.status == 'completed',
                    ~ProcessedServiceResult.payload.like('%"error"%')
                ).subquery()

            # Исключаем processing/completed саммаризации
            query = query.filter(
                ~PostCache.id.in_(processing_summarization),
                ~PostCache.id.in_(real_success_summarization)
            )

            logger.info(f"🛡️ Дедупликация саммаризации: исключены processing и completed для бота {bot_id}")
    
    # Возвращаем результат
    results = query.order_by(PostCache.post_date.desc()).limit(limit).all()
    
    # Добавляем bot_id к каждому посту
    response_data = []
    for post in results:
        post_dict = post.__dict__
        post_dict['bot_id'] = bot_id
        response_data.append(PostCacheResponseWithBot.model_validate(post_dict))

    return response_data

# === MULTITENANT STATUS ENDPOINTS ===
@app.get("/api/ai/results/batch-status")
def get_ai_results_batch_status(
    post_ids: str = Query(..., description="Comma-separated list of post IDs"),
    bot_id: int = Query(..., description="Bot ID"),
    db: Session = Depends(get_db)
):
    """🔧 ИСПРАВЛЕНО: GET endpoint для проверки статусов постов в мультитенантной архитектуре"""
    try:
        # Парсим post_ids
        post_ids_list = [int(pid.strip()) for pid in post_ids.split(',') if pid.strip()]
        
        if not post_ids_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="post_ids не может быть пустым"
            )
        
        if len(post_ids_list) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Максимальное количество post_ids: 100"
            )
        
        # Проверяем существование бота
        bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Бот с ID {bot_id} не найден"
            )
        
        # Получаем статусы постов для данного бота
        results = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(post_ids_list),
            ProcessedData.public_bot_id == bot_id
        ).all()
        
        # Формируем ответ
        status_map = {}
        for result in results:
            status_map[result.post_id] = {
                "post_id": result.post_id,
                "bot_id": result.public_bot_id,
                "status": result.processing_status,
                "processed_at": result.processed_at.isoformat() if result.processed_at else None,
                "is_categorized": result.is_categorized,
                "is_summarized": result.is_summarized
            }
        
        # Добавляем отсутствующие посты как "not_found"
        for post_id in post_ids_list:
            if post_id not in status_map:
                status_map[post_id] = {
                    "post_id": post_id,
                    "bot_id": bot_id,
                    "status": "not_found",
                    "processed_at": None
                }
        
        return {
            "bot_id": bot_id,
            "requested_posts": len(post_ids_list),
            "found_posts": len(results),
            "statuses": list(status_map.values())
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Некорректные post_ids: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка получения batch статусов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения batch статусов: {str(e)}"
        )

@app.put("/api/ai/results/batch-status")
def update_ai_results_status_batch(
    request: dict,  # {"post_ids": [1, 2, 3], "bot_id": 4, "status": "categorized"}
    db: Session = Depends(get_db)
):
    """🔧 НОВОЕ: Батчевое обновление мультитенантных статусов AI обработки"""
    post_ids = request.get("post_ids", [])
    bot_id = request.get("bot_id")
    new_status = request.get("status")
    
    if not post_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле 'post_ids' обязательно и не может быть пустым"
        )
    
    if not bot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле 'bot_id' обязательно"
        )
    
    if not new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле 'status' обязательно"
        )
    
    # Валидация статуса
    valid_statuses = ["pending", "processing", "categorized", "summarized", "completed", "failed"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимый статус. Допустимые: {valid_statuses}"
        )
    
    # Валидация количества постов
    if len(post_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимальное количество постов в батче: 100"
        )
    
    try:
        # Проверяем существование бота
        bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Бот с ID {bot_id} не найден"
            )
        
        # Получаем или создаем записи processed_data для этих постов и бота
        existing_records = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(post_ids),
            ProcessedData.public_bot_id == bot_id
        ).all()
        
        existing_post_ids = {record.post_id for record in existing_records}
        missing_post_ids = set(post_ids) - existing_post_ids
        
        # Создаем записи для отсутствующих постов
        created_count = 0
        if missing_post_ids:
            for post_id in missing_post_ids:
                # Проверяем что пост существует
                post_exists = db.query(PostCache).filter(PostCache.id == post_id).first()
                if post_exists:
                    new_record = ProcessedData(
                        post_id=post_id,
                        public_bot_id=bot_id,
                        summaries={},
                        categories={},
                        metrics={},
                        processing_status=new_status
                    )
                    db.add(new_record)
                    created_count += 1
        
        # Обновляем статус существующих записей
        updated_count = 0
        if existing_records:
            updated_count = db.query(ProcessedData).filter(
                ProcessedData.post_id.in_([record.post_id for record in existing_records]),
                ProcessedData.public_bot_id == bot_id
            ).update({
                "processing_status": new_status
            }, synchronize_session=False)
        
        db.commit()
        
        total_affected = created_count + updated_count
        logger.info(f"✅ Батчево обновлено {total_affected} AI статусов на '{new_status}' для бота {bot_id}")
        
        return {
            "message": f"Батчево обновлено {total_affected} AI статусов на '{new_status}' для бота {bot_id}",
            "affected_count": total_affected,
            "created_count": created_count,
            "updated_count": updated_count,
            "requested_count": len(post_ids),
            "bot_id": bot_id,
            "status": new_status,
            "missing_posts": list(set(post_ids) - existing_post_ids - {r.post_id for r in existing_records}) if missing_post_ids else []
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка батчевого обновления AI статусов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка батчевого обновления AI статусов: {str(e)}"
        )

@app.get("/api/ai/results/{result_id}", response_model=AIResultResponse)
def get_ai_result_by_id(result_id: int, db: Session = Depends(get_db)):
    """Получение конкретного AI результата по ID"""
    result = db.query(ProcessedData).filter(ProcessedData.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="AI result not found")
    return result

# --------------------------------------------------------------------------
# НОВЫЕ ЭНДПОИНТЫ ДЛЯ ПАРАЛЛЕЛЬНОЙ АРХИТЕКТУРЫ (ДЕНЬ 30)
# --------------------------------------------------------------------------

# РЕЕСТР СЕРВИСОВ
# Определяет, какие сервисы должны быть выполнены для каждого поста
AI_SERVICES = [
    {"name": "categorization", "queue": "categorization", "required": True},
    {"name": "summarization",  "queue": "summarization",  "required": True},
    # Можно добавлять новые сервисы, например:
    # {"name": "ner_extraction", "queue": "processing", "required": False}
]

def _update_processed_data_flags(db: Session, post_id: int, bot_id: int):
    """🔧 ИСПРАВЛЕНО: Пересчитывает флаги и статусы с проверкой реальных AI результатов."""
    
    logger.info(f"🔄 Обновление флагов для post_id={post_id}, bot_id={bot_id}")
    
    # Получаем или создаем агрегированную запись
    agg_row = db.query(ProcessedData).filter(
        ProcessedData.post_id == post_id,
        ProcessedData.public_bot_id == bot_id
    ).with_for_update().first()

    if not agg_row:
        logger.info(f"📝 Создаем новую запись ProcessedData для post_id={post_id}, bot_id={bot_id}")
        agg_row = ProcessedData(post_id=post_id, public_bot_id=bot_id, summaries={}, categories={}, metrics={})
        db.add(agg_row)

    # Получаем все успешные результаты для этого поста/бота
    service_results = db.query(ProcessedServiceResult.service_name, ProcessedServiceResult.payload, ProcessedServiceResult.metrics).filter(
        ProcessedServiceResult.post_id == post_id,
        ProcessedServiceResult.public_bot_id == bot_id,
        ProcessedServiceResult.status == 'completed'  # ИСПРАВЛЕНО: ищем статус 'completed' а не 'success'
    ).all()
    
    logger.info(f"📊 Найдено {len(service_results)} успешных результатов для post_id={post_id}, bot_id={bot_id}")
    
    # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Проверяем что результаты реальные, а не fallback
    successful_services = {}
    for res in service_results:
        # Десериализация payload (может быть строкой JSON или уже словарем)
        if isinstance(res.payload, str):
            try:
                payload = json.loads(res.payload)
            except (json.JSONDecodeError, ValueError):
                payload = {}
        elif isinstance(res.payload, dict):
            payload = res.payload
        else:
            payload = {}
        
        logger.info(f"🔍 DEBUG: Проверяем {res.service_name}: payload={payload}, type={type(res.payload)}")
        
        if not payload.get('error'):  # Если нет поля 'error' - это реальный результат
            successful_services[res.service_name] = {'payload': payload, 'metrics': res.metrics}
            logger.info(f"✅ Принимаем реальный результат для {res.service_name}")
        else:
            logger.warning(f"⚠️ Игнорируем fallback результат для {res.service_name}: {payload.get('error')}")

    # Обновляем флаги только для РЕАЛЬНЫХ результатов
    agg_row.is_categorized = "categorization" in successful_services
    agg_row.is_summarized = "summarization" in successful_services
    
    logger.info(f"🏁 Флаги обновлены: is_categorized={agg_row.is_categorized}, is_summarized={agg_row.is_summarized}")
    
    # Обновляем агрегированные данные
    if agg_row.is_categorized:
        cat_payload = successful_services["categorization"]['payload']
        cat_metrics = successful_services["categorization"]['metrics']
        
        # Преобразуем формат из новой архитектуры в ожидаемый формат
        agg_row.categories = {
            'category_name': cat_payload.get('primary', ''),
            'secondary': cat_payload.get('secondary', []),
            'relevance_scores': cat_payload.get('relevance_scores', [])
        }
        
        # Обновляем метрики
        if not agg_row.metrics:
            agg_row.metrics = {}
        agg_row.metrics.update(cat_metrics)
        
        logger.info(f"📂 Категории обновлены: {agg_row.categories}")

    if agg_row.is_summarized:
        sum_payload = successful_services["summarization"]['payload']
        sum_metrics = successful_services["summarization"]['metrics']
        
        # Преобразуем формат из новой архитектуры в ожидаемый формат
        agg_row.summaries = {
            'summary': sum_payload.get('summary', ''),
            'language': sum_payload.get('language', 'ru')
        }
        
        # Обновляем метрики
        if not agg_row.metrics:
            agg_row.metrics = {}
        agg_row.metrics.update(sum_metrics)
        
        logger.info(f"📄 Summary обновлено: {agg_row.summaries}")

    # Проверяем, все ли ОБЯЗАТЕЛЬНЫЕ сервисы завершены
    required_services = {s['name'] for s in AI_SERVICES if s.get('required', False)}
    if required_services.issubset(successful_services.keys()):
        agg_row.processing_status = "completed"
    else:
        agg_row.processing_status = "processing"
    
    logger.info(f"✅ Обновление завершено. Статус: {agg_row.processing_status}")
    
    agg_row.processed_at = datetime.utcnow()
    db.flush()

# --------------------------------------------------------------------------
AI_SERVICES = [
    {"name": "categorization", "required": True},
    {"name": "summarization", "required": True},
]

@app.post("/api/ai/service-results/batch", status_code=status.HTTP_201_CREATED)
def create_service_results_batch(batch: ServiceResultsBatch, db: Session = Depends(get_db)):
    """
    Принимает батч результатов от одного из AI-сервисов,
    сохраняя их в `processed_service_results` с помощью "UPSERT" (обновление при конфликте).
    Для каждого уникального поста/бота вызывает функцию обновления агрегированного статуса.
    """
    logger.info(f"🚀 DEBUG: Получен POST /api/ai/service-results/batch с {len(batch.results)} результатами")
    
    if not batch.results:
        logger.warning("Получен пустой батч результатов. Действий не требуется.")
        return JSONResponse(status_code=200, content={"message": "Нет данных для сохранения."})

    try:
        # Шаг 1: Подготовить данные для "UPSERT"
        results_to_upsert = [
            {
                "post_id": r.post_id,
                "public_bot_id": r.public_bot_id,
                "service_name": r.service_name,
                "status": r.status,
                "payload": r.payload,
                "metrics": r.metrics,
                "processed_at": datetime.utcnow()
            }
            for r in batch.results
        ]
        
        # Шаг 2: Выполнить "UPSERT" (INSERT ... ON CONFLICT ...)
        if USE_POSTGRESQL:
            stmt = insert(ProcessedServiceResult).values(results_to_upsert)
            update_dict = {
                'status': stmt.excluded.status,
                'payload': stmt.excluded.payload,
                'metrics': stmt.excluded.metrics,
                'processed_at': stmt.excluded.processed_at
            }
            stmt = stmt.on_conflict_do_update(
                index_elements=['post_id', 'public_bot_id', 'service_name'],
                set_=update_dict
            )
            db.execute(stmt)
        else: # Fallback для SQLite
             for r in results_to_upsert:
                existing = db.query(ProcessedServiceResult).filter_by(
                    post_id=r['post_id'], 
                    public_bot_id=r['public_bot_id'],
                    service_name=r['service_name']
                ).first()
                if existing:
                    existing.status = r['status']
                    existing.payload = r['payload']
                    existing.metrics = r['metrics']
                    existing.processed_at = r['processed_at']
                else:
                    db.add(ProcessedServiceResult(**r))

        logger.info(f"✅ Успешно сохранено/обновлено {len(results_to_upsert)} записей в `processed_service_results`.")

        # Шаг 3: Асинхронно обновить агрегатные статусы для затронутых постов
        unique_posts_to_update = {(r.post_id, r.public_bot_id) for r in batch.results}
        
        logger.info(f"🔄 Запуск обновления агрегатных статусов для {len(unique_posts_to_update)} уникальных постов/ботов.")
        
        for post_id, bot_id in unique_posts_to_update:
            try:
                logger.info(f"🔧 DEBUG: Вызываем _update_processed_data_flags для post_id={post_id}, bot_id={bot_id}")
                _update_processed_data_flags(db, post_id, bot_id)
                logger.info(f"✅ DEBUG: _update_processed_data_flags завершилась для post_id={post_id}, bot_id={bot_id}")
            except Exception as e:
                 logger.error(f"❌ Ошибка при обновлении агрегатного статуса для post_id={post_id}, bot_id={bot_id}: {e}", exc_info=True)

        db.commit()
        
        return JSONResponse(
            status_code=201,
            content={"message": f"Успешно обработано {len(results_to_upsert)} результатов."}
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Критическая ошибка в create_service_results_batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка сервера при обработке результатов: {e}"
        )

@app.put("/api/ai/results/sync-status")
def sync_ai_service_status(request: SyncStatusRequest, db: Session = Depends(get_db)):
    """🔧 НОВЫЙ: Синхронизация статуса AI сервиса с атомарным обновлением флагов и пересчётом статуса"""
    try:
        # Валидация сервиса
        valid_services = ["categorizer", "summarizer"]
        if request.service not in valid_services:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый сервис. Допустимые: {valid_services}"
            )
        
        # Проверяем существование бота
        bot = db.query(PublicBot).filter(PublicBot.id == request.bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Бот с ID {request.bot_id} не найден"
            )
        
        # Получаем или создаем записи processed_data для этих постов и бота
        existing_records = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(request.post_ids),
            ProcessedData.public_bot_id == request.bot_id
        ).all()
        
        existing_post_ids = {record.post_id for record in existing_records}
        missing_post_ids = set(request.post_ids) - existing_post_ids
        
        # Создаем записи для отсутствующих постов
        created_count = 0
        if missing_post_ids:
            for post_id in missing_post_ids:
                # Проверяем что пост существует
                post_exists = db.query(PostCache).filter(PostCache.id == post_id).first()
                if post_exists:
                    new_record = ProcessedData(
                        post_id=post_id,
                        public_bot_id=request.bot_id,
                        summaries={},
                        categories={},
                        metrics={},
                        is_categorized=(request.service == "categorizer"),
                        is_summarized=(request.service == "summarizer"),
                        processing_status="processing"  # Один сервис завершил = processing
                    )
                    db.add(new_record)
                    created_count += 1
        
        # Обновляем флаги и статус существующих записей
        updated_count = 0
        for record in existing_records:
            # Выставляем соответствующий флаг
            if request.service == "categorizer":
                record.is_categorized = True
            elif request.service == "summarizer":
                record.is_summarized = True
            
            # Пересчитываем статус на основе флагов
            if not record.is_categorized and not record.is_summarized:
                record.processing_status = "pending"
            elif record.is_categorized and record.is_summarized:
                record.processing_status = "completed"
            else:
                record.processing_status = "processing"
            
            updated_count += 1
        
        db.commit()
        
        # Получаем статистику после обновления
        stats = db.query(
            ProcessedData.processing_status,
            func.count(ProcessedData.id).label('count')
        ).filter(
            ProcessedData.public_bot_id == request.bot_id
        ).group_by(ProcessedData.processing_status).all()
        
        status_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }
        for stat in stats:
            if stat.processing_status in status_counts:
                status_counts[stat.processing_status] = stat.count
        
        total_affected = created_count + updated_count
        logger.info(f"✅ Синхронизирован статус сервиса '{request.service}' для {total_affected} постов бота {request.bot_id}")
        
        return {
            "message": f"Синхронизирован статус сервиса '{request.service}' для {total_affected} постов",
            "service": request.service,
            "bot_id": request.bot_id,
            "affected_count": total_affected,
            "created_count": created_count,
            "updated_count": updated_count,
            "status_distribution": status_counts,
            "requested_posts": len(request.post_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка синхронизации статуса сервиса: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка синхронизации статуса: {str(e)}"
        )

# === AI MANAGEMENT ENDPOINTS ===
@app.get("/api/ai/status")
def get_ai_status(db: Session = Depends(get_db)):
    """Получить статус AI обработки (МУЛЬТИТЕНАНТНЫЕ СТАТУСЫ)"""
    try:
        # Получаем активные боты (active + development)
        active_bots = db.query(PublicBot).filter(
            PublicBot.status.in_(['active', 'development'])
        ).all()
        
        # Получаем каналы активных ботов
        active_bot_ids = [bot.id for bot in active_bots]
        
        if active_bot_ids:
            # Получаем каналы, назначенные активным ботам
            bot_channels = db.query(BotChannel).filter(
                BotChannel.public_bot_id.in_(active_bot_ids),
                BotChannel.is_active == True
            ).all()
            
            if bot_channels:
                # Получаем telegram_id каналов
                channel_ids = [bc.channel_id for bc in bot_channels]
                channels_info = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
                channel_telegram_ids = [ch.telegram_id for ch in channels_info]
                
                # 🚀 МУЛЬТИТЕНАНТНАЯ статистика постов по статусам
                multitenant_stats = {}
                for status in ['pending', 'categorized', 'summarized', 'completed', 'failed']:
                    # Считаем уникальные посты из каналов активных ботов с данным статусом
                    count = db.query(PostCache.id).join(
                        ProcessedData, PostCache.id == ProcessedData.post_id
                    ).filter(
                        ProcessedData.processing_status == status,
                        ProcessedData.public_bot_id.in_(active_bot_ids),
                        PostCache.channel_telegram_id.in_(channel_telegram_ids)
                    ).distinct().count()
                    multitenant_stats[status] = count
                
                # Создаем совместимую с UI статистику (processing = categorized + summarized)
                processing_count = multitenant_stats.get('categorized', 0) + multitenant_stats.get('summarized', 0)
                posts_stats = {
                    'pending': multitenant_stats.get('pending', 0),
                    'processing': processing_count,
                    'completed': multitenant_stats.get('completed', 0),
                    'failed': multitenant_stats.get('failed', 0)
                }
                
                # Общая статистика постов (только для активных ботов)
                total_assignable_posts = db.query(PostCache).filter(
                    PostCache.channel_telegram_id.in_(channel_telegram_ids)
                ).count()
            else:
                # Нет назначенных каналов
                multitenant_stats = {'pending': 0, 'categorized': 0, 'summarized': 0, 'completed': 0, 'failed': 0}
                posts_stats = {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
                total_assignable_posts = 0
        else:
            # Нет активных ботов
            multitenant_stats = {'pending': 0, 'categorized': 0, 'summarized': 0, 'completed': 0, 'failed': 0}
            posts_stats = {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
            total_assignable_posts = 0
        
        # Расчет прогресса от назначенных постов
        progress_percentage = 0
        if total_assignable_posts > 0:
            completed_posts = posts_stats.get('completed', 0)
            progress_percentage = round((completed_posts / total_assignable_posts) * 100, 2)
        
        # Общая статистика всех постов (для справки)
        total_posts_in_system = db.query(PostCache).count()
        
        # Статистика AI результатов
        total_ai_results = db.query(ProcessedData).count()
        results_per_post = round(total_ai_results / max(total_assignable_posts, 1), 2)
        
        # 🔧 НОВОЕ: Статистика по флагам для активных ботов
        flags_stats = {}
        if active_bot_ids:
            # Считаем посты с is_categorized = true
            categorized_count = db.query(ProcessedData).filter(
                ProcessedData.public_bot_id.in_(active_bot_ids),
                ProcessedData.is_categorized == True
            ).count()
            
            # Считаем посты с is_summarized = true
            summarized_count = db.query(ProcessedData).filter(
                ProcessedData.public_bot_id.in_(active_bot_ids),
                ProcessedData.is_summarized == True
            ).count()
            
            flags_stats = {
                "categorized": categorized_count,
                "summarized": summarized_count
            }
        else:
            flags_stats = {"categorized": 0, "summarized": 0}
        
        # Статистика ботов
        total_bots = db.query(PublicBot).count()
        active_bots_count = db.query(PublicBot).filter(PublicBot.status == 'active').count()
        development_bots = db.query(PublicBot).filter(PublicBot.status == 'development').count()
        processing_bots = active_bots_count + development_bots
        
        return {
            "posts_stats": posts_stats,  # Совместимая с UI статистика
            "multitenant_stats": multitenant_stats,  # Полная мультитенантная статистика
            "flags_stats": flags_stats,  # 🔧 НОВОЕ: Статистика по флагам
            "total_posts": total_assignable_posts,  # Посты назначенные активным ботам
            "total_posts_in_system": total_posts_in_system,  # Все посты в системе
            "progress_percentage": progress_percentage,  # Прогресс от назначенных постов
            "ai_results_stats": {
                "total_results": total_ai_results,
                "results_per_post": results_per_post
            },
            "bots_stats": {
                "total_bots": total_bots,
                "active_bots": active_bots_count,
                "development_bots": development_bots,
                "total_processing_bots": processing_bots
            },
            "is_processing": posts_stats.get('processing', 0) > 0,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "posts_stats": {"pending": 0, "processing": 0, "completed": 0, "failed": 0},
            "multitenant_stats": {"pending": 0, "categorized": 0, "summarized": 0, "completed": 0, "failed": 0},
            "flags_stats": {"categorized": 0, "summarized": 0},
            "total_posts": 0,
            "progress_percentage": 0,
            "ai_results_stats": {"total_results": 0, "results_per_post": 0},
            "bots_stats": {"total_bots": 0, "active_bots": 0, "development_bots": 0, "total_processing_bots": 0},
            "is_processing": False,
            "last_updated": datetime.now().isoformat()
        }

@app.get("/api/ai/multitenant-status")
def get_multitenant_ai_status(db: Session = Depends(get_db)):
    """🚀 НОВЫЙ: Полная мультитенантная статистика AI обработки по ботам"""
    try:
        # Получаем активные боты
        active_bots = db.query(PublicBot).filter(
            PublicBot.status.in_(['active', 'development'])
        ).all()
        
        if not active_bots:
            return {
                "bots_stats": [],
                "summary": {"pending": 0, "processing": 0, "categorized": 0, "summarized": 0, "completed": 0, "failed": 0},
                "ui_compatible_summary": {"pending": 0, "processing": 0, "completed": 0, "failed": 0},
                "total_bots": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        bots_detailed = []
        summary_stats = {"pending": 0, "processing": 0, "categorized": 0, "summarized": 0, "completed": 0, "failed": 0}
        
        for bot in active_bots:
            # Получаем каналы бота
            bot_channels = db.query(BotChannel).filter(
                BotChannel.public_bot_id == bot.id,
                BotChannel.is_active == True
            ).all()
            
            if bot_channels:
                channel_ids = [bc.channel_id for bc in bot_channels]
                channels_info = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
                channel_telegram_ids = [ch.telegram_id for ch in channels_info]
                
                # Статистика по статусам для этого бота
                bot_stats = {}
                
                # Подсчитываем по статусам
                for status in ['pending', 'processing', 'completed', 'failed']:
                    count = db.query(PostCache.id).join(
                        ProcessedData, PostCache.id == ProcessedData.post_id
                    ).filter(
                        ProcessedData.processing_status == status,
                        ProcessedData.public_bot_id == bot.id,
                        PostCache.channel_telegram_id.in_(channel_telegram_ids)
                    ).distinct().count()
                    bot_stats[status] = count
                
                # Подсчитываем по флагам (для детальной статистики)
                categorized_count = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    ProcessedData.is_categorized == True,
                    ProcessedData.public_bot_id == bot.id,
                    PostCache.channel_telegram_id.in_(channel_telegram_ids)
                ).distinct().count()
                
                summarized_count = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    ProcessedData.is_summarized == True,
                    ProcessedData.public_bot_id == bot.id,
                    PostCache.channel_telegram_id.in_(channel_telegram_ids)
                ).distinct().count()
                
                # Добавляем флаги в статистику
                bot_stats['categorized'] = categorized_count
                bot_stats['summarized'] = summarized_count
                
                # Суммируем для общей статистики
                summary_stats['pending'] += bot_stats.get('pending', 0)
                summary_stats['processing'] += bot_stats.get('processing', 0)
                summary_stats['completed'] += bot_stats.get('completed', 0)
                summary_stats['failed'] += bot_stats.get('failed', 0)
                summary_stats['categorized'] += categorized_count
                summary_stats['summarized'] += summarized_count
                
                # Общее количество постов для бота
                total_bot_posts = db.query(PostCache).filter(
                    PostCache.channel_telegram_id.in_(channel_telegram_ids)
                ).count()
                
                progress = 0
                if total_bot_posts > 0:
                    progress = round((bot_stats['completed'] / total_bot_posts) * 100, 2)
            else:
                bot_stats = {"pending": 0, "processing": 0, "categorized": 0, "summarized": 0, "completed": 0, "failed": 0}
                total_bot_posts = 0
                progress = 0
            
            # UI-совместимая статистика для бота
            ui_compatible_stats = {
                "pending": bot_stats.get('pending', 0),
                "processing": bot_stats.get('processing', 0),
                "completed": bot_stats.get('completed', 0),
                "failed": bot_stats.get('failed', 0)
            }
            
            bots_detailed.append({
                "bot_id": bot.id,
                "name": bot.name,
                "status": bot.status,
                "multitenant_stats": bot_stats,  # Полная статистика
                "ui_stats": ui_compatible_stats,  # Совместимая с UI
                "total_posts": total_bot_posts,
                "progress_percentage": progress,
                "channels_count": len(bot_channels) if bot_channels else 0
            })
        
        # UI-совместимая суммарная статистика
        ui_compatible_summary = {
            "pending": summary_stats.get('pending', 0),
            "processing": summary_stats.get('processing', 0),
            "completed": summary_stats.get('completed', 0),
            "failed": summary_stats.get('failed', 0)
        }
        
        # 🔧 ИСПРАВЛЕНО: Добавляем правильную статистику ботов для совместимости
        bot_statistics = []
        for bot_detail in bots_detailed:
            bot_statistics.append({
                "bot_id": bot_detail["bot_id"],
                "bot_name": bot_detail["name"],
                "total_posts": bot_detail["total_posts"],
                "processed_posts": bot_detail["multitenant_stats"]["completed"],
                "posts_by_status": bot_detail["multitenant_stats"]
            })
        
        return {
            "bots_stats": bots_detailed,
            "bot_statistics": bot_statistics,  # 🚀 НОВОЕ: Совместимость с диагностическими скриптами
            "summary": summary_stats,  # Полная мультитенантная статистика
            "ui_compatible_summary": ui_compatible_summary,  # Совместимая с UI
            "total_bots": len(active_bots),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "bots_stats": [],
            "summary": {"pending": 0, "processing": 0, "categorized": 0, "summarized": 0, "completed": 0, "failed": 0},
            "ui_compatible_summary": {"pending": 0, "processing": 0, "completed": 0, "failed": 0},
            "total_bots": 0,
            "last_updated": datetime.now().isoformat()
        }

@app.get("/api/ai/tasks")
def get_ai_tasks(db: Session = Depends(get_db)):
    """Получить список активных AI задач"""
    try:
        # Получаем посты в статусе "processing"
        processing_posts = db.query(PostCache).filter(
            PostCache.processing_status == "processing"
        ).order_by(PostCache.collected_at.desc()).all()
        
        # Получаем информацию о каналах для контекста
        channel_ids = list(set([post.channel_telegram_id for post in processing_posts]))
        channels_info = db.query(Channel).filter(Channel.telegram_id.in_(channel_ids)).all()
        channels_map = {ch.telegram_id: ch.channel_name for ch in channels_info}
        
        tasks = []
        for post in processing_posts:
            tasks.append({
                "post_id": post.id,
                "channel_name": channels_map.get(post.channel_telegram_id, f"Channel {post.channel_telegram_id}"),
                "channel_telegram_id": post.channel_telegram_id,
                "content_preview": (post.content[:100] + "...") if post.content and len(post.content) > 100 else post.content,
                "post_date": post.post_date,
                "collected_at": post.collected_at,
                "views": post.views
            })
        
        return {
            "success": True,
            "active_tasks": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "active_tasks": 0,
            "tasks": []
        }

@app.post("/api/ai/reprocess-all")
async def reprocess_all_posts(db: Session = Depends(get_db)):
    """✅ МУЛЬТИТЕНАНТНЫЙ ПЕРЕЗАПУСК: Очистить все AI результаты + автозапуск AI Orchestrator"""
    try:
        # ✅ ПРАВИЛЬНАЯ МУЛЬТИТЕНАНТНАЯ АРХИТЕКТУРА:
        # 1. НЕ трогаем posts_cache.processing_status (он глобальный, управляется AI Orchestrator)
        # 2. Удаляем только записи из processed_data (мультитенантные результаты)
        # 3. AI Orchestrator автоматически увидит все посты как "необработанные" для каждого бота
        
        # Подсчитываем AI результаты для удаления
        deleted_results = db.query(ProcessedData).count()
        
        # Удаляем все AI результаты (мультитенантные статусы автоматически удалятся)
        db.query(ProcessedData).delete(synchronize_session=False)
        
        # 🔧 ИСПРАВЛЕНИЕ: Удаляем все записи из processed_service_results  
        db.query(ProcessedServiceResult).delete(synchronize_session=False)
        
        db.commit()
        
        # 🚀 АВТОЗАПУСК AI ORCHESTRATOR
        ai_start_success = False
        ai_message = ""
        
        if deleted_results > 0:
            try:
                # Вызываем существующую функцию trigger_ai_processing
                trigger_response = await trigger_ai_processing()
                ai_start_success = trigger_response.get("success", False)
                ai_message = "AI Orchestrator запущен автоматически через trigger_ai_processing"
            except Exception as e:
                ai_message = f"Ошибка автозапуска AI через trigger_ai_processing: {str(e)}"
        else:
            ai_message = "Нет AI результатов для очистки, автозапуск не требуется"
        
        return {
            "success": True,
            "message": "✅ Мультитенантный перезапуск AI обработки инициирован",
            "ai_results_cleared": deleted_results,
            "multitenant_architecture": True,  # Маркер новой архитектуры
            "ai_auto_start": ai_start_success,
            "ai_message": ai_message
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при перезапуске AI обработки"
        }

@app.post("/api/ai/reprocess-bot/{bot_id}")
def reprocess_bot_posts(bot_id: int, db: Session = Depends(get_db)):
    """Перезапустить AI обработку для конкретного бота"""
    try:
        # Проверяем существование бота
        bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail="Бот не найден")
        
        # Получаем каналы бота
        bot_channels = db.query(BotChannel).filter(
            BotChannel.public_bot_id == bot_id,
            BotChannel.is_active == True
        ).all()
        
        if not bot_channels:
            return {
                "success": False,
                "error": "У бота нет настроенных каналов",
                "posts_reset": 0,
                "ai_results_cleared": 0
            }
        
        # Получаем telegram_id каналов
        channel_ids = [bc.channel_id for bc in bot_channels]
        channels_info = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
        channel_telegram_ids = [ch.telegram_id for ch in channels_info]
        
        # Сбрасываем статус постов из каналов бота
        updated_count = db.query(PostCache).filter(
            PostCache.channel_telegram_id.in_(channel_telegram_ids)
        ).update(
            {"processing_status": "pending"},
            synchronize_session=False
        )
        
        # Удаляем AI результаты для этого бота
        deleted_results = db.query(ProcessedData).filter(
            ProcessedData.public_bot_id == bot_id
        ).count()
        
        db.query(ProcessedData).filter(
            ProcessedData.public_bot_id == bot_id
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Перезапуск AI обработки для бота '{bot.name}' инициирован",
            "bot_name": bot.name,
            "posts_reset": updated_count,
            "ai_results_cleared": deleted_results,
            "channels_affected": len(channel_telegram_ids)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при перезапуске AI обработки для бота {bot_id}"
        }

@app.post("/api/ai/reprocess-channel/{channel_id}")
def reprocess_channel_posts(channel_id: int, db: Session = Depends(get_db)):
    """Перезапустить AI обработку для конкретного канала"""
    try:
        # Проверяем существование канала
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Канал не найден")
        
        # Сбрасываем статус постов из этого канала
        updated_count = db.query(PostCache).filter(
            PostCache.channel_telegram_id == channel.telegram_id
        ).update(
            {"processing_status": "pending"},
            synchronize_session=False
        )
        
        # Удаляем AI результаты для постов этого канала
        # Получаем ID постов канала
        post_ids = db.query(PostCache.id).filter(
            PostCache.channel_telegram_id == channel.telegram_id
        ).all()
        post_ids_list = [pid[0] for pid in post_ids]
        
        deleted_results = 0
        if post_ids_list:
            deleted_results = db.query(ProcessedData).filter(
                ProcessedData.post_id.in_(post_ids_list)
            ).count()
            
            db.query(ProcessedData).filter(
                ProcessedData.post_id.in_(post_ids_list)
            ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Перезапуск AI обработки для канала '{channel.title or channel.channel_name}' инициирован",
            "channel_name": channel.title or channel.channel_name,
            "channel_username": channel.username,
            "posts_reset": updated_count,
            "ai_results_cleared": deleted_results
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": f"Ошибка при перезапуске AI обработки для канала {channel_id}"
        }

@app.post("/api/ai/reprocess-channels")
def reprocess_multiple_channels(request: dict, db: Session = Depends(get_db)):
    """Перезапустить AI обработку для нескольких каналов"""
    try:
        channel_ids = request.get("channel_ids", [])
        if not channel_ids:
            return {
                "success": False,
                "error": "Не указаны каналы для перезапуска",
                "channels_processed": 0,
                "total_posts_reset": 0,
                "total_ai_results_cleared": 0
            }
        
        # Проверяем существование каналов
        channels = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
        if not channels:
            return {
                "success": False,
                "error": "Указанные каналы не найдены",
                "channels_processed": 0,
                "total_posts_reset": 0,
                "total_ai_results_cleared": 0
            }
        
        total_posts_reset = 0
        total_ai_results_cleared = 0
        processed_channels = []
        
        for channel in channels:
            # Сбрасываем статус постов канала
            updated_count = db.query(PostCache).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).update(
                {"processing_status": "pending"},
                synchronize_session=False
            )
            
            # Удаляем AI результаты для постов канала
            post_ids = db.query(PostCache.id).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).all()
            post_ids_list = [pid[0] for pid in post_ids]
            
            deleted_results = 0
            if post_ids_list:
                deleted_results = db.query(ProcessedData).filter(
                    ProcessedData.post_id.in_(post_ids_list)
                ).count()
                
                db.query(ProcessedData).filter(
                    ProcessedData.post_id.in_(post_ids_list)
                ).delete(synchronize_session=False)
            
            total_posts_reset += updated_count
            total_ai_results_cleared += deleted_results
            
            processed_channels.append({
                "id": channel.id,
                "name": channel.title or channel.channel_name,
                "username": channel.username,
                "posts_reset": updated_count,
                "ai_results_cleared": deleted_results
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Перезапуск AI обработки инициирован для {len(processed_channels)} каналов",
            "channels_processed": len(processed_channels),
            "total_posts_reset": total_posts_reset,
            "total_ai_results_cleared": total_ai_results_cleared,
            "processed_channels": processed_channels
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при перезапуске AI обработки для каналов"
        }

@app.post("/api/ai/stop")
def stop_ai_processing(db: Session = Depends(get_db)):
    """Остановить AI обработку - сбросить все посты в статус 'pending'"""
    try:
        # Сбрасываем все посты со статусом 'processing' в 'pending'
        updated_count = db.query(PostCache).filter(
            PostCache.processing_status == "processing"
        ).update(
            {"processing_status": "pending"},
            synchronize_session=False
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": "AI обработка остановлена",
            "posts_stopped": updated_count,
            "note": "Посты в статусе 'processing' переведены в 'pending'"
        }
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при остановке AI обработки"
        }

@app.delete("/api/ai/clear-results")
async def clear_ai_results(confirm: bool = False, db: Session = Depends(get_db)):
    """✅ МУЛЬТИТЕНАНТНАЯ ОЧИСТКА: Удалить все AI результаты + автозапуск AI Orchestrator"""
    if not confirm:
        return {
            "success": False,
            "error": "Требуется подтверждение",
            "message": "Добавьте параметр ?confirm=true для подтверждения операции"
        }
    
    try:
        # Подсчитываем количество записей для удаления
        total_results = db.query(ProcessedData).count()
        
        # ✅ ПРАВИЛЬНАЯ МУЛЬТИТЕНАНТНАЯ АРХИТЕКТУРА:
        # 1. НЕ трогаем posts_cache.processing_status (он глобальный)
        # 2. Удаляем только записи из processed_data (мультитенантные результаты)
        # 3. AI Orchestrator автоматически увидит посты как "необработанные" для каждого бота
        
        # Удаляем все AI результаты (мультитенантные статусы автоматически удалятся)
        db.query(ProcessedData).delete(synchronize_session=False)
        
        # 🔧 ИСПРАВЛЕНИЕ: Удаляем все записи из processed_service_results
        db.query(ProcessedServiceResult).delete(synchronize_session=False)
        
        db.commit()
        
        # АВТОМАТИЧЕСКИ ЗАПУСКАЕМ AI ORCHESTRATOR ПОСЛЕ СБРОСА
        ai_orchestrator_triggered = False
        trigger_error = None
        
        if total_results > 0:
            try:
                # Вызываем существующую функцию trigger_ai_processing
                trigger_response = await trigger_ai_processing()
                ai_orchestrator_triggered = trigger_response.get("success", False)
            except Exception as e:
                trigger_error = str(e)
        
        # Формируем ответ
        result = {
            "success": True,
            "deleted_results": total_results,
            "multitenant_architecture": True,  # Маркер новой архитектуры
            "ai_orchestrator_triggered": ai_orchestrator_triggered
        }
        
        if ai_orchestrator_triggered:
            result["message"] = f"✅ Удалено {total_results} AI результатов (мультитенантная архитектура). AI Orchestrator запущен автоматически."
        elif total_results > 0:
            result["message"] = f"✅ Удалено {total_results} AI результатов (мультитенантная архитектура). Ошибка автозапуска AI Orchestrator: {trigger_error or 'Неизвестная ошибка'}"
            result["trigger_error"] = trigger_error
        else:
            result["message"] = "✅ Нет AI результатов для удаления (мультитенантная архитектура)"
        
        return result
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при удалении AI результатов"
        }

# Digest Preview API Endpoint
@app.post("/api/public-bots/{bot_id}/preview-digest")
async def generate_digest_preview(bot_id: int, db: Session = Depends(get_db)):
    """
    Генерация РЕАЛЬНОГО превью дайджеста для бота с использованием AI сервисов
    
    Алгоритм:
    1. Получить каналы, на которые подписан бот
    2. Найти 5 постов с ненулевым содержанием из этих каналов
    3. Проверить AI обработку, запустить если нужно
    4. Создать реальный дайджест используя логику Telegram бота
    5. Вернуть превью с настоящими AI резюме и категориями
    """
    try:
        # 1. Проверяем существование бота
        bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бот не найден"
            )
        
        # 2. Получаем каналы бота
        bot_channels = db.query(BotChannel).filter(
            BotChannel.public_bot_id == bot_id,
            BotChannel.is_active == True
        ).all()
        
        if not bot_channels:
            return {
                "success": False,
                "error": "У бота нет настроенных каналов",
                "fallback_data": {
                    "bot_name": bot.name,
                    "message": "Для генерации превью дайджеста необходимо настроить каналы бота"
                }
            }
        
        # 3. Получаем категории бота
        bot_categories = db.query(BotCategory).filter(
            BotCategory.public_bot_id == bot_id,
            BotCategory.is_active == True
        ).all()
        
        if not bot_categories:
            return {
                "success": False,
                "error": "У бота нет настроенных категорий",
                "fallback_data": {
                    "bot_name": bot.name,
                    "message": "Для генерации превью дайджеста необходимо настроить категории бота"
                }
            }
        
        # 4. Получаем telegram_id каналов бота
        channel_ids = [bc.channel_id for bc in bot_channels]
        channels_info = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
        channel_telegram_ids = [ch.telegram_id for ch in channels_info]
        
        # 5. Получаем 5 постов с ненулевым содержанием из каналов бота
        posts_query = db.query(PostCache).filter(
            PostCache.channel_telegram_id.in_(channel_telegram_ids),
            PostCache.content.isnot(None),
            PostCache.content != "",
            func.length(PostCache.content) > 50  # Минимум 50 символов
        ).order_by(PostCache.collected_at.desc()).limit(5)
        
        posts = posts_query.all()
        
        if not posts:
            return {
                "success": False,
                "error": "Нет подходящих постов для превью",
                "fallback_data": {
                    "bot_name": bot.name,
                    "message": f"В каналах бота нет постов с достаточным содержанием для генерации превью"
                }
            }
        
        # 6. Проверяем, есть ли уже AI обработка для этих постов
        post_ids = [post.id for post in posts]
        existing_ai_results = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(post_ids),
            ProcessedData.public_bot_id == bot_id
        ).all()
        
        existing_post_ids = {result.post_id for result in existing_ai_results}
        unprocessed_posts = [post for post in posts if post.id not in existing_post_ids]
        
        # 7. Если есть необработанные посты - запускаем AI Orchestrator
        if unprocessed_posts:
            print(f"🧠 Запускаем AI обработку для {len(unprocessed_posts)} постов...")
            
            # Импортируем AI Orchestrator
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            
            from ai_services.orchestrator_v5_parallel import AIOrchestrator
            
            # Создаем AI Orchestrator
            orchestrator = AIOrchestrator(backend_url="http://localhost:8000")
            
            # Запускаем AI обработку для конкретного бота через orchestrator_v5_parallel
            try:
                # Создаем словарь бота для AI Orchestrator v5
                bot_data = {
                    "id": bot.id,
                    "name": bot.name,
                    "categorization_prompt": bot.categorization_prompt or "",
                    "summarization_prompt": bot.summarization_prompt or "",
                    "status": bot.status
                }
                
                # Запускаем AI обработку для конкретного бота
                processed_count = await orchestrator.process_bot(bot_data)
                
                if processed_count > 0:
                    print(f"✅ AI обработка завершена: {processed_count} постов обработано")
                else:
                    print("⚠️ AI обработка не дала результатов")
            except Exception as e:
                print(f"❌ Ошибка AI обработки: {str(e)}")
                # Продолжаем с существующими данными
        
        # 8. Получаем все AI результаты (существующие + новые)
        all_ai_results = db.query(ProcessedData).filter(
            ProcessedData.post_id.in_(post_ids),
            ProcessedData.public_bot_id == bot_id
        ).all()
        
        # 9. Формируем превью дайджеста
        digest_posts = []
        for result in all_ai_results:
            # Находим соответствующий пост
            post = next((p for p in posts if p.id == result.post_id), None)
            if not post:
                continue
            
            # Парсим AI данные
            try:
                summaries = result.summaries if USE_POSTGRESQL else json.loads(result.summaries)
                categories = result.categories if USE_POSTGRESQL else json.loads(result.categories)
                metrics = result.metrics if USE_POSTGRESQL else json.loads(result.metrics)
            except:
                continue
            
            digest_posts.append({
                "post_id": post.id,
                "title": post.title,
                "content_preview": (post.content[:200] + "...") if post.content and len(post.content) > 200 else post.content,
                "channel_telegram_id": post.channel_telegram_id,
                "post_date": post.post_date,
                "views": post.views,
                "ai_summary": summaries.get("summary", "Резюме недоступно"),
                "ai_category": categories.get("category", "Без категории"),
                "ai_metrics": {
                    "importance": metrics.get("importance", 0),
                    "urgency": metrics.get("urgency", 0),
                    "significance": metrics.get("significance", 0)
                }
            })
        
        # 10. Сортируем по важности
        digest_posts.sort(key=lambda x: x["ai_metrics"]["importance"], reverse=True)
        
        return {
            "success": True,
            "bot_name": bot.name,
            "bot_id": bot.id,
            "preview_generated_at": datetime.now(),
            "total_posts_analyzed": len(posts),
            "ai_processed_posts": len(all_ai_results),
            "digest_posts": digest_posts[:bot.max_posts_per_digest],
            "channels_included": len(channel_telegram_ids),
            "categories_configured": len(bot_categories)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback_data": {
                "bot_name": "Неизвестный бот",
                "message": f"Ошибка генерации превью: {str(e)}"
            }
        }

# 🚀 НОВЫЙ ENDPOINT: Автозапуск AI Orchestrator
@app.post("/api/ai/trigger-processing")
async def trigger_ai_processing():
    """Реактивный запуск AI Orchestrator для обработки необработанных постов"""
    global orchestrator_commands
    
    try:
        # 🔧 ИСПРАВЛЕНО: Используем мультитенантную логику для подсчета необработанных постов
        db = next(get_db())
        
        # Находим активные боты
        active_bots = db.query(PublicBot).filter(
            PublicBot.status.in_(['active', 'development'])
        ).all()
        
        if not active_bots:
            return {
                "success": True,
                "message": "Нет активных ботов для обработки",
                "pending_posts": 0
            }
        
        # Собираем каналы всех активных ботов
        active_channel_ids = set()
        for bot in active_bots:
            bot_channels = db.query(BotChannel).filter(
                BotChannel.public_bot_id == bot.id,
                BotChannel.is_active == True
            ).all()
            for bot_channel in bot_channels:
                active_channel_ids.add(bot_channel.channel_id)
        
        if not active_channel_ids:
            return {
                "success": True,
                "message": "У активных ботов нет каналов для обработки",
                "pending_posts": 0
            }
        
        # Получаем telegram_id каналов
        channels = db.query(Channel).filter(Channel.id.in_(active_channel_ids)).all()
        active_telegram_ids = [ch.telegram_id for ch in channels]
        
        # Считаем все посты из каналов активных ботов
        total_posts = db.query(PostCache).filter(
            PostCache.channel_telegram_id.in_(active_telegram_ids)
        ).count()
        
        if total_posts == 0:
            return {
                "success": True,
                "message": "Нет постов в каналах активных ботов",
                "pending_posts": 0
            }
        
        # Добавляем команду в очередь для AI Orchestrator (если он работает в continuous режиме)
        trigger_command = {
            "command_type": "trigger_processing",
            "message": f"Запрос обработки {total_posts} постов для {len(active_bots)} активных ботов",
            "pending_posts": total_posts
        }
        orchestrator_commands.append({
            "id": len(orchestrator_commands) + 1,
            "timestamp": datetime.now().isoformat(),
            **trigger_command
        })
        
        # AI Orchestrator теперь работает через Celery tasks
        
        # Запускаем AI Orchestrator через Celery task
        task = celery_client.send_task(
            'tasks.trigger_ai_processing',
            args=[None, False],  # bot_id=None (все боты), force_reprocess=False
            kwargs={}
        )
        
        return {
            "success": True,
            "message": f"AI обработка запущена для {total_posts} постов",
            "pending_posts": total_posts,
            "task_id": task.id,
            "command_queued": True
        }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при запуске AI Orchestrator"
        }

# 🔄 ОБНОВЛЕННЫЕ ENDPOINTS с автозапуском
@app.post("/api/ai/reprocess-channels-auto")
def reprocess_multiple_channels_with_auto_start(request: dict, db: Session = Depends(get_db)):
    """Перезапустить AI обработку для нескольких каналов + автозапуск AI Orchestrator"""
    try:
        # 1. Выполняем стандартный reprocess
        channel_ids = request.get("channel_ids", [])
        if not channel_ids:
            return {
                "success": False,
                "error": "Не указаны каналы для перезапуска"
            }
        
        # Проверяем существование каналов
        channels = db.query(Channel).filter(Channel.id.in_(channel_ids)).all()
        if not channels:
            return {
                "success": False,
                "error": "Указанные каналы не найдены"
            }
        
        total_posts_reset = 0
        total_ai_results_cleared = 0
        processed_channels = []
        
        for channel in channels:
            # Сбрасываем статус постов канала
            updated_count = db.query(PostCache).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).update(
                {"processing_status": "pending"},
                synchronize_session=False
            )
            
            # Удаляем AI результаты для постов канала
            post_ids = db.query(PostCache.id).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).all()
            post_ids_list = [pid[0] for pid in post_ids]
            
            deleted_results = 0
            if post_ids_list:
                deleted_results = db.query(ProcessedData).filter(
                    ProcessedData.post_id.in_(post_ids_list)
                ).count()
                
                db.query(ProcessedData).filter(
                    ProcessedData.post_id.in_(post_ids_list)
                ).delete(synchronize_session=False)
            
            total_posts_reset += updated_count
            total_ai_results_cleared += deleted_results
            
            processed_channels.append({
                "id": channel.id,
                "name": channel.title or channel.channel_name,
                "username": channel.username,
                "posts_reset": updated_count,
                "ai_results_cleared": deleted_results
            })
        
        db.commit()
        
        # 2. Автозапуск AI Orchestrator через Celery
        ai_start_success = False
        ai_message = ""
        
        try:
            # Запускаем AI Orchestrator через Celery task
            task = celery_client.send_task(
                'tasks.trigger_ai_processing',
                args=[None, True],  # bot_id=None (все боты), force_reprocess=True
                kwargs={}
            )
            
            ai_start_success = True
            ai_message = f"AI Orchestrator запущен автоматически (Task ID: {task.id})"
        except Exception as e:
            ai_message = f"Ошибка автозапуска AI: {str(e)}"
        
        return {
            "success": True,
            "message": f"Перезапуск AI обработки инициирован для {len(processed_channels)} каналов",
            "channels_processed": len(processed_channels),
            "total_posts_reset": total_posts_reset,
            "total_ai_results_cleared": total_ai_results_cleared,
            "processed_channels": processed_channels,
            "ai_auto_start": ai_start_success,
            "ai_message": ai_message
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "Ошибка при перезапуске AI обработки для каналов"
        }

# 🚀 НОВЫЙ ENDPOINT: Детальная статистика AI сервисов
@app.get("/api/ai/detailed-status")
def get_detailed_ai_status(db: Session = Depends(get_db)):
    """Получить детальную статистику AI сервисов (МУЛЬТИТЕНАНТНЫЕ СТАТУСЫ)"""
    try:
        # 1. Находим активные боты и их каналы (та же логика что в /api/ai/status)
        active_bots = db.query(PublicBot).filter(
            PublicBot.status.in_(['active', 'development'])
        ).all()
        
        # Собираем все каналы активных ботов
        active_channel_ids = set()
        for bot in active_bots:
            bot_channels = db.query(BotChannel).filter(
                BotChannel.public_bot_id == bot.id,
                BotChannel.is_active == True
            ).all()
            for bot_channel in bot_channels:
                active_channel_ids.add(bot_channel.channel_id)
        
        # Получаем telegram_id каналов
        if active_channel_ids:
            channels = db.query(Channel).filter(Channel.id.in_(active_channel_ids)).all()
            active_telegram_ids = [ch.telegram_id for ch in channels]
        else:
            active_telegram_ids = []
        
        # 2. 🚀 МУЛЬТИТЕНАНТНАЯ статистика постов (только для постов активных ботов)
        active_bot_ids = [bot.id for bot in active_bots]
        multitenant_stats = {}
        for status in ['pending', 'categorized', 'summarized', 'completed', 'failed']:
            if active_telegram_ids and active_bot_ids:
                # Считаем уникальные посты с мультитенантными статусами
                count = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    ProcessedData.processing_status == status,
                    ProcessedData.public_bot_id.in_(active_bot_ids),
                    PostCache.channel_telegram_id.in_(active_telegram_ids)
                ).distinct().count()
            else:
                count = 0
            multitenant_stats[status] = count
        
        # Создаем совместимую с UI статистику
        processing_count = multitenant_stats.get('categorized', 0) + multitenant_stats.get('summarized', 0)
        posts_stats = {
            'pending': multitenant_stats.get('pending', 0),
            'processing': processing_count,
            'completed': multitenant_stats.get('completed', 0),
            'failed': multitenant_stats.get('failed', 0)
        }
        
        # Всего постов назначенных активным ботам
        if active_telegram_ids:
            total_posts = db.query(PostCache).filter(
                PostCache.channel_telegram_id.in_(active_telegram_ids)
            ).count()
        else:
            total_posts = 0
            
        progress_percentage = 0
        if total_posts > 0:
            completed_posts = posts_stats.get('completed', 0)
            progress_percentage = round((completed_posts / total_posts) * 100, 2)
        
        # 3. 🚀 МУЛЬТИТЕНАНТНАЯ статистика по каналам (только активные каналы)
        channels_detailed = []
        if active_telegram_ids and active_bot_ids:
            for telegram_id in active_telegram_ids:
                # Считаем мультитенантную статистику для каждого канала
                channel_total_posts = db.query(PostCache).filter(PostCache.channel_telegram_id == telegram_id).count()
                
                # Мультитенантные статусы для канала
                pending = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    PostCache.channel_telegram_id == telegram_id,
                    ProcessedData.processing_status == 'pending',
                    ProcessedData.public_bot_id.in_(active_bot_ids)
                ).distinct().count()
                
                categorized = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    PostCache.channel_telegram_id == telegram_id,
                    ProcessedData.processing_status == 'categorized',
                    ProcessedData.public_bot_id.in_(active_bot_ids)
                ).distinct().count()
                
                summarized = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    PostCache.channel_telegram_id == telegram_id,
                    ProcessedData.processing_status == 'summarized',
                    ProcessedData.public_bot_id.in_(active_bot_ids)
                ).distinct().count()
                
                completed = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    PostCache.channel_telegram_id == telegram_id,
                    ProcessedData.processing_status == 'completed',
                    ProcessedData.public_bot_id.in_(active_bot_ids)
                ).distinct().count()
                
                failed = db.query(PostCache.id).join(
                    ProcessedData, PostCache.id == ProcessedData.post_id
                ).filter(
                    PostCache.channel_telegram_id == telegram_id,
                    ProcessedData.processing_status == 'failed',
                    ProcessedData.public_bot_id.in_(active_bot_ids)
                ).distinct().count()
                
                # Получаем информацию о канале
                channel = db.query(Channel).filter(Channel.telegram_id == telegram_id).first()
                channel_name = channel.title or channel.channel_name if channel else f'Channel {telegram_id}'
                channel_username = channel.username if channel else None
                
                processing_count = categorized + summarized  # Промежуточные статусы
                
                channels_detailed.append({
                    'telegram_id': telegram_id,
                    'name': channel_name,
                    'username': channel_username,
                    'total_posts': channel_total_posts,
                    'pending': pending,
                    'processing': processing_count,  # Для совместимости с UI
                    'categorized': categorized,  # Новый статус
                    'summarized': summarized,   # Новый статус
                    'completed': completed,
                    'failed': failed,
                    'progress': round(completed / max(channel_total_posts, 1) * 100, 1)
                })
        
        # 4. Статистика AI результатов по ботам (только активные боты)
        
        if active_bot_ids:
            ai_results_by_bot = db.query(
                ProcessedData.public_bot_id,
                func.count(ProcessedData.id).label('results_count'),
                func.max(ProcessedData.processed_at).label('last_processed')
            ).filter(ProcessedData.public_bot_id.in_(active_bot_ids)).group_by(ProcessedData.public_bot_id).all()
        else:
            ai_results_by_bot = []
        
        # Получаем названия ботов
        bot_names = {}
        for bot in active_bots:
            bot_names[bot.id] = {
                'name': bot.name,
                'status': bot.status
            }
        
        bots_detailed = []
        for stat in ai_results_by_bot:
            bot_info = bot_names.get(stat.public_bot_id, {})
            bots_detailed.append({
                'bot_id': stat.public_bot_id,
                'name': bot_info.get('name', f'Bot {stat.public_bot_id}'),
                'status': bot_info.get('status', 'unknown'),
                'results_count': stat.results_count,
                'last_processed': stat.last_processed.isoformat() if stat.last_processed else None
            })
        
        # 5. Последние обработанные посты (только от активных ботов)
        if active_bot_ids:
            recent_processed = db.query(ProcessedData).filter(
                ProcessedData.public_bot_id.in_(active_bot_ids)
            ).order_by(ProcessedData.processed_at.desc()).limit(10).all()
        else:
            recent_processed = []
        
        # Создаем словарь названий каналов для последних постов
        channel_names = {}
        if active_telegram_ids:
            for telegram_id in active_telegram_ids:
                channel = db.query(Channel).filter(Channel.telegram_id == telegram_id).first()
                if channel:
                    channel_names[telegram_id] = {
                        'name': channel.title or channel.channel_name,
                        'username': channel.username
                    }
        
        recent_posts = []
        for result in recent_processed:
            # Получаем информацию о посте
            post = db.query(PostCache).filter(PostCache.id == result.post_id).first()
            if post:
                recent_posts.append({
                    'post_id': result.post_id,
                    'bot_id': result.public_bot_id,
                    'bot_name': bot_names.get(result.public_bot_id, {}).get('name', f'Bot {result.public_bot_id}'),
                    'channel_id': post.channel_telegram_id,
                    'channel_name': channel_names.get(post.channel_telegram_id, {}).get('name', f'Channel {post.channel_telegram_id}'),
                    'processed_at': result.processed_at.isoformat(),
                    'processing_version': result.processing_version,
                    'content_preview': (post.content or '')[:100] + '...' if post.content else 'Нет содержания'
                })
        
        # 6. Определение статуса AI Orchestrator
        is_processing = posts_stats.get('processing', 0) > 0
        orchestrator_status = "АКТИВЕН" if is_processing else "НЕ АКТИВЕН"
        
        # 7. Время последней активности
        last_activity = None
        if recent_processed:
            last_activity = recent_processed[0].processed_at.isoformat()
        
        # 8. Добавляем дополнительную информацию для сравнения
        total_posts_in_system = db.query(PostCache).count()
        
        return {
            # Базовая статистика (только активные боты)
            "posts_stats": posts_stats,  # Совместимая с UI статистика
            "multitenant_stats": multitenant_stats,  # Полная мультитенантная статистика
            "total_posts": total_posts,  # Посты назначенные активным ботам
            "total_posts_in_system": total_posts_in_system,  # Все посты в системе
            "progress_percentage": progress_percentage,
            
            # Статус AI Orchestrator
            "orchestrator_status": orchestrator_status,
            "is_processing": is_processing,
            "last_activity": last_activity,
            
            # Детальная статистика по каналам (только активные)
            "channels_detailed": channels_detailed,
            
            # Детальная статистика по ботам (только активные)
            "bots_detailed": bots_detailed,
            
            # Последние обработанные посты (только активные боты)
            "recent_processed": recent_posts,
            
            # Метаданные
            "last_updated": datetime.now().isoformat(),
            "total_channels": len(channels_detailed),
            "total_active_bots": len(active_bots),
            "active_channel_telegram_ids": active_telegram_ids,  # Для отладки
            "active_bot_ids": active_bot_ids  # Для отладки
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "posts_stats": {"pending": 0, "processing": 0, "completed": 0, "failed": 0},
            "multitenant_stats": {"pending": 0, "categorized": 0, "summarized": 0, "completed": 0, "failed": 0},
            "total_posts": 0,
            "total_posts_in_system": 0,
            "progress_percentage": 0,
            "orchestrator_status": "ОШИБКА",
            "is_processing": False,
            "channels_detailed": [],
            "bots_detailed": [],
            "recent_processed": [],
            "last_updated": datetime.now().isoformat()
        }

# Глобальная переменная для хранения последнего статуса AI Orchestrator
orchestrator_status_cache = {
    "status": "UNKNOWN",
    "timestamp": None,
    "stats": {},
    "details": {}
}

@app.post("/api/ai/orchestrator-status")
async def receive_orchestrator_status(status_data: dict):
    """Получение отчетов о статусе AI Orchestrator"""
    global orchestrator_status_cache
    
    try:
        # Обновляем кэш статуса
        orchestrator_status_cache.update({
            "status": status_data.get("orchestrator_status", "UNKNOWN"),
            "timestamp": status_data.get("timestamp"),
            "stats": status_data.get("stats", {}),
            "details": status_data.get("details", {})
        })
        
        print(f"📡 Получен статус AI Orchestrator: {orchestrator_status_cache['status']}")
        
        return {"success": True, "message": "Статус получен"}
        
    except Exception as e:
        print(f"❌ Ошибка при получении статуса AI Orchestrator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/orchestrator-live-status")
async def get_orchestrator_live_status():
    """Получение детального статуса AI Orchestrator с диагностикой"""
    global orchestrator_status_cache, orchestrator_process
    
    try:
        # Проверяем актуальность статуса (если старше 2 минут - считаем неактивным)
        current_time = datetime.now()
        is_active = False
        
        if orchestrator_status_cache["timestamp"]:
            try:
                status_time = datetime.fromisoformat(orchestrator_status_cache["timestamp"].replace('Z', '+00:00'))
                # Убираем timezone info для сравнения
                if status_time.tzinfo:
                    status_time = status_time.replace(tzinfo=None)
                
                time_diff = (current_time - status_time).total_seconds()
                is_active = time_diff < 120  # 2 минуты
            except Exception as e:
                print(f"⚠️ Ошибка парсинга времени статуса: {e}")
        
        # Проверяем статус фонового процесса
        background_process_info = {
            "is_running": orchestrator_process is not None and orchestrator_process.poll() is None,
            "process_id": orchestrator_process.pid if orchestrator_process and orchestrator_process.poll() is None else None,
            "managed_by_backend": True
        }
        
        # Расширенная диагностика
        diagnostics = {
            "heartbeat_active": is_active,
            "heartbeat_age_seconds": int((current_time - datetime.fromisoformat(orchestrator_status_cache["timestamp"].replace('Z', '+00:00')).replace(tzinfo=None)).total_seconds()) if orchestrator_status_cache["timestamp"] else None,
            "background_process": background_process_info,
            "overall_health": "HEALTHY" if (is_active or background_process_info["is_running"]) else "UNHEALTHY",
            "connection_method": "BACKGROUND_PROCESS" if background_process_info["is_running"] else "HEARTBEAT_ONLY"
        }
        
        return {
            "orchestrator_active": is_active or background_process_info["is_running"],
            "status": orchestrator_status_cache["status"] if is_active else ("BACKGROUND_RUNNING" if background_process_info["is_running"] else "INACTIVE"),
            "last_update": orchestrator_status_cache["timestamp"],
            "stats": orchestrator_status_cache["stats"],
            "details": orchestrator_status_cache["details"],
            "time_since_update": diagnostics["heartbeat_age_seconds"],
            "diagnostics": diagnostics,
            "background_control": background_process_info
        }
        
    except Exception as e:
        print(f"❌ Ошибка при получении live статуса: {str(e)}")
        return {
            "orchestrator_active": False,
            "status": "ERROR",
            "error": str(e),
            "diagnostics": {
                "overall_health": "ERROR",
                "connection_method": "NONE"
            }
        }

# === AI ORCHESTRATOR COMMANDS ===

# Глобальный список команд для AI Orchestrator
orchestrator_commands = []

@app.get("/api/ai/orchestrator-commands")
async def get_orchestrator_commands():
    """Получение команд для AI Orchestrator"""
    global orchestrator_commands
    return orchestrator_commands

@app.post("/api/ai/orchestrator-commands")
async def add_orchestrator_command(command: dict):
    """Добавление команды для AI Orchestrator"""
    global orchestrator_commands
    
    # Добавляем ID и timestamp
    command_with_id = {
        "id": len(orchestrator_commands) + 1,
        "timestamp": datetime.now().isoformat(),
        **command
    }
    
    orchestrator_commands.append(command_with_id)
    
    return {"success": True, "command_id": command_with_id["id"]}

@app.delete("/api/ai/orchestrator-commands/{command_id}")
async def mark_command_processed(command_id: int):
    """Пометить команду как обработанную (удалить из очереди)"""
    global orchestrator_commands
    
    # Удаляем команду из списка
    orchestrator_commands = [cmd for cmd in orchestrator_commands if cmd["id"] != command_id]
    
    return {"success": True, "message": f"Команда {command_id} помечена как обработанная"}

# === КОНЕЦ AI ORCHESTRATOR COMMANDS ===

# === AI ORCHESTRATOR BACKGROUND CONTROL ===

# Глобальная переменная для хранения процесса AI Orchestrator
orchestrator_process = None
orchestrator_logs = []  # Буфер для хранения логов (последние 100 записей)

@app.post("/api/ai/orchestrator/start-background")
async def start_orchestrator_background():
    """Запуск AI Orchestrator в фоновом режиме"""
    global orchestrator_process
    
    try:
        # AI Orchestrator теперь работает через Celery - проверяем доступность Redis
        try:
            # Проверяем, что Celery client может подключиться к Redis
            celery_client.control.inspect().ping()
        except Exception as e:
            return {
                "success": False,
                "message": f"Celery client недоступен: {str(e)}",
                "status": "celery_unavailable"
            }
        
        # Запускаем AI Orchestrator через Celery task
        task = celery_client.send_task(
            'tasks.trigger_ai_processing',
            args=[None, False],  # bot_id=None (все боты), force_reprocess=False
            kwargs={}
        )
        
        # Добавляем лог о запуске
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": f"AI Orchestrator запущен в фоновом режиме (Task ID: {task.id})"
        }
        orchestrator_logs.append(log_entry)
        
        return {
            "success": True,
            "message": "AI Orchestrator успешно запущен в фоновом режиме",
            "status": "started",
            "task_id": task.id
        }
        
    except Exception as e:
        error_msg = f"Ошибка при запуске AI Orchestrator: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Добавляем лог об ошибке
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": error_msg
        }
        orchestrator_logs.append(log_entry)
        
        return {
            "success": False,
            "message": error_msg,
            "status": "error"
        }

@app.post("/api/ai/orchestrator/stop-background")
async def stop_orchestrator_background():
    """Остановка AI Orchestrator фонового режима"""
    global orchestrator_process
    
    try:
        # С Celery tasks нет постоянного процесса для остановки
        # Задачи выполняются по мере необходимости
        
        # Добавляем лог об остановке
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "AI Orchestrator остановлен (Celery tasks больше не отправляются)"
        }
        orchestrator_logs.append(log_entry)
        
        orchestrator_process = None
        
        return {
            "success": True,
            "message": "AI Orchestrator успешно остановлен",
            "status": "stopped",
            "note": "Celery tasks больше не отправляются"
        }
        
    except Exception as e:
        error_msg = f"Ошибка при остановке AI Orchestrator: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Добавляем лог об ошибке
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "ERROR",
            "message": error_msg
        }
        orchestrator_logs.append(log_entry)
        
        return {
            "success": False,
            "message": error_msg,
            "status": "error"
        }

@app.post("/api/ai/orchestrator/restart")
async def restart_orchestrator():
    """Перезапуск AI Orchestrator"""
    try:
        # Сначала останавливаем
        stop_result = await stop_orchestrator_background()
        
        # Небольшая пауза перед запуском
        import asyncio
        await asyncio.sleep(2)
        
        # Затем запускаем
        start_result = await start_orchestrator_background()
        
        if start_result["success"]:
            return {
                "success": True,
                "message": "AI Orchestrator успешно перезапущен",
                "status": "restarted",
                "stop_result": stop_result,
                "start_result": start_result
            }
        else:
            return {
                "success": False,
                "message": "Ошибка при перезапуске AI Orchestrator",
                "status": "restart_failed",
                "stop_result": stop_result,
                "start_result": start_result
            }
            
    except Exception as e:
        error_msg = f"Ошибка при перезапуске AI Orchestrator: {str(e)}"
        print(f"❌ {error_msg}")
        
        return {
            "success": False,
            "message": error_msg,
            "status": "error"
        }

@app.get("/api/ai/orchestrator/logs")
async def get_orchestrator_logs(limit: int = 50):
    """Получение логов AI Orchestrator"""
    global orchestrator_logs
    
    try:
        # Ограничиваем количество логов (берем последние)
        recent_logs = orchestrator_logs[-limit:] if len(orchestrator_logs) > limit else orchestrator_logs
        
        # Также проверяем статус процесса
        process_info = {
            "is_running": orchestrator_process is not None and orchestrator_process.poll() is None,
            "process_id": orchestrator_process.pid if orchestrator_process and orchestrator_process.poll() is None else None
        }
        
        return {
            "success": True,
            "logs": recent_logs,
            "total_logs": len(orchestrator_logs),
            "process_info": process_info,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Ошибка при получении логов: {str(e)}"
        print(f"❌ {error_msg}")
        
        return {
            "success": False,
            "message": error_msg,
            "logs": [],
            "process_info": {"is_running": False, "process_id": None}
        }

# === КОНЕЦ AI ORCHESTRATOR BACKGROUND CONTROL ===

# === МУЛЬТИТЕНАНТНАЯ ОЧИСТКА ДАННЫХ ===

@app.delete("/api/data/clear-all")
async def clear_all_data(
    confirm: bool = False,
    include_posts: bool = False,  # По умолчанию НЕ удаляем посты
    include_ai_results: bool = True,  # По умолчанию удаляем только AI результаты
    db: Session = Depends(get_db)
):
    """Удаляет все AI результаты и сбрасывает статус обработки"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Для подтверждения операции установите confirm=true")
    
    try:
        deleted_stats = {
            "posts_cache": 0,
            "processed_data": 0,
            "posts_reset_to_pending": 0,
            "operation": "clear_all_data",
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Очистка AI результатов (МУЛЬТИТЕНАНТНАЯ АРХИТЕКТУРА)
        if include_ai_results:
            ai_results_count = db.query(func.count(ProcessedData.id)).scalar()
            db.query(ProcessedData).delete()
            deleted_stats["processed_data"] = ai_results_count
            
            # В мультитенантной архитектуре нет глобального processing_status
            # Статусы хранятся в processed_data.processing_status для каждого бота
            # Поэтому просто удаляем AI результаты, статусы сбрасываются автоматически
            deleted_stats["posts_reset_to_pending"] = 0  # Не применимо в мультитенантной архитектуре
            
        # 2. Очистка кэша постов
        if include_posts:
            posts_count = db.query(func.count(PostCache.id)).scalar()
            db.query(PostCache).delete()
            deleted_stats["posts_cache"] = posts_count
            
        db.commit()
        
        logger.info(f"🧹 ПОЛНАЯ ОЧИСТКА ДАННЫХ: {deleted_stats}")
        
        return {
            "success": True,
            "message": "AI результаты очищены, статус обработки сброшен",
            "deleted_stats": deleted_stats
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при полной очистке данных: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке данных: {str(e)}")

@app.delete("/api/data/clear-by-channel/{channel_id}")
async def clear_data_by_channel(
    channel_id: int,
    confirm: bool = False,
    include_posts: bool = False,  # По умолчанию НЕ удаляем посты
    include_ai_results: bool = True,  # По умолчанию удаляем только AI результаты
    db: Session = Depends(get_db)
):
    """Удаляет AI результаты канала и сбрасывает статус обработки"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Для подтверждения операции установите confirm=true")
    
    try:
        # Проверяем существование канала
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail=f"Канал с ID {channel_id} не найден")
        
        # Простая статистика
        deleted_stats = {
            "channel_id": channel_id,
            "channel_name": channel.channel_name,
            "posts_cache": 0,
            "processed_data": 0,
            "posts_reset_to_pending": 0,
            "operation": "clear_by_channel"
        }
        
        # 1. Очистка AI результатов
        if include_ai_results:
            # Найти посты канала
            channel_posts = db.query(PostCache.id).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).all()
            
            if channel_posts:
                post_ids = [post.id for post in channel_posts]
                
                # Удалить AI результаты
                ai_count = db.query(ProcessedData).filter(
                    ProcessedData.post_id.in_(post_ids)
                ).count()
                
                db.query(ProcessedData).filter(
                    ProcessedData.post_id.in_(post_ids)
                ).delete(synchronize_session=False)
                
                deleted_stats["processed_data"] = ai_count
                
                # В мультитенантной архитектуре статусы хранятся в processed_data
                # Удаление AI результатов автоматически "сбрасывает" статусы
                deleted_stats["posts_reset_to_pending"] = 0  # Не применимо в мультитенантной архитектуре
        
        # 2. Очистка постов
        if include_posts:
            posts_count = db.query(PostCache).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).count()
            
            db.query(PostCache).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).delete()
            
            deleted_stats["posts_cache"] = posts_count
        
        # Коммитим изменения
        db.commit()
        
        return {
            "success": True,
            "message": f"AI результаты канала '{channel.channel_name}' очищены, статус сброшен",
            "deleted_stats": deleted_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке данных канала: {str(e)}")

@app.delete("/api/data/clear-by-bot/{bot_id}")
async def clear_data_by_bot(
    bot_id: int,
    confirm: bool = False,
    include_posts: bool = False,  # По умолчанию НЕ удаляем посты при очистке по боту
    include_ai_results: bool = True,
    db: Session = Depends(get_db)
):
    """Удаляет AI результаты бота и сбрасывает статус обработки"""
    if not confirm:
        raise HTTPException(status_code=400, detail="Для подтверждения операции установите confirm=true")
    
    try:
        # Проверяем существование бота
        bot = db.query(PublicBot).filter(PublicBot.id == bot_id).first()
        if not bot:
            raise HTTPException(status_code=404, detail=f"Бот с ID {bot_id} не найден")
        
        deleted_stats = {
            "bot_id": bot_id,
            "bot_name": bot.name,
            "posts_cache": 0,
            "processed_data": 0,
            "posts_reset_to_pending": 0,
            "operation": "clear_by_bot",
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Очистка AI результатов бота
        if include_ai_results:
            ai_results_count = db.query(func.count(ProcessedData.id)).filter(
                ProcessedData.public_bot_id == bot_id
            ).scalar()
            
            db.query(ProcessedData).filter(
                ProcessedData.public_bot_id == bot_id
            ).delete()
            
            deleted_stats["processed_data"] = ai_results_count
            
            # Сбрасываем статус обработки постов из каналов бота на "pending"
            # Получаем каналы, связанные с ботом
            bot_channels = db.query(BotChannel.channel_id).filter(
                BotChannel.public_bot_id == bot_id
            ).subquery()
            
            # Получаем telegram_id этих каналов
            channel_telegram_ids = db.query(Channel.telegram_id).filter(
                Channel.id.in_(db.query(bot_channels.c.channel_id))
            ).all()
            
            telegram_ids = [row[0] for row in channel_telegram_ids]
            
            if telegram_ids:
                # Сбрасываем статус обработки для постов из каналов бота
                posts_reset_count = db.query(PostCache).filter(
                    PostCache.channel_telegram_id.in_(telegram_ids),
                    PostCache.processing_status != "pending"
                ).count()
                
                db.query(PostCache).filter(
                    PostCache.channel_telegram_id.in_(telegram_ids),
                    PostCache.processing_status != "pending"
                ).update({"processing_status": "pending"}, synchronize_session=False)
                
                deleted_stats["posts_reset_to_pending"] = posts_reset_count
        
        # 2. Опционально: очистка постов из связанных каналов
        if include_posts:
            # Получаем каналы, связанные с ботом
            bot_channels = db.query(BotChannel.channel_id).filter(
                BotChannel.public_bot_id == bot_id
            ).subquery()
            
            # Получаем telegram_id этих каналов
            channel_telegram_ids = db.query(Channel.telegram_id).filter(
                Channel.id.in_(db.query(bot_channels.c.channel_id))
            ).all()
            
            telegram_ids = [row[0] for row in channel_telegram_ids]
            
            if telegram_ids:
                posts_count = db.query(func.count(PostCache.id)).filter(
                    PostCache.channel_telegram_id.in_(telegram_ids)
                ).scalar()
                
                db.query(PostCache).filter(
                    PostCache.channel_telegram_id.in_(telegram_ids)
                ).delete(synchronize_session=False)
                
                deleted_stats["posts_cache"] = posts_count
                deleted_stats["affected_channels"] = len(telegram_ids)
        
        db.commit()
        
        logger.info(f"🧹 ОЧИСТКА ПО БОТУ {bot.name}: {deleted_stats}")
        
        return {
            "success": True,
            "message": f"AI результаты бота '{bot.name}' очищены, статус сброшен",
            "deleted_stats": deleted_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при очистке данных бота {bot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке данных бота: {str(e)}")

@app.get("/api/data/cleanup-preview")
async def get_cleanup_preview(
    cleanup_type: str = Query(..., regex="^(all|channel|bot)$"),
    target_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Предварительный просмотр данных для очистки"""
    try:
        preview = {
            "cleanup_type": cleanup_type,
            "target_id": target_id,
            "posts_count": 0,
            "ai_results_count": 0,
            "affected_channels": [],
            "affected_bots": [],
            "size_estimate": "0 MB",
            "timestamp": datetime.now().isoformat()
        }
        
        if cleanup_type == "all":
            # Полная очистка - все данные
            preview["posts_count"] = db.query(func.count(PostCache.id)).scalar()
            preview["ai_results_count"] = db.query(func.count(ProcessedData.id)).scalar()
            
            # Получаем список всех каналов и ботов
            channels = db.query(Channel.id, Channel.channel_name, Channel.telegram_id).all()
            bots = db.query(PublicBot.id, PublicBot.name).all()
            
            preview["affected_channels"] = [
                {"id": ch.id, "name": ch.channel_name, "telegram_id": ch.telegram_id} 
                for ch in channels
            ]
            preview["affected_bots"] = [
                {"id": bot.id, "name": bot.name} 
                for bot in bots
            ]
            
        elif cleanup_type == "channel" and target_id:
            # Очистка по каналу
            channel = db.query(Channel).filter(Channel.id == target_id).first()
            if not channel:
                raise HTTPException(status_code=404, detail=f"Канал с ID {target_id} не найден")
            
            preview["posts_count"] = db.query(func.count(PostCache.id)).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).scalar()
            
            # AI результаты для постов этого канала (всех ботов)
            channel_posts = db.query(PostCache.id).filter(
                PostCache.channel_telegram_id == channel.telegram_id
            ).subquery()
            
            preview["ai_results_count"] = db.query(func.count(ProcessedData.id)).filter(
                ProcessedData.post_id.in_(db.query(channel_posts.c.id))
            ).scalar()
            
            preview["affected_channels"] = [
                {"id": channel.id, "name": channel.channel_name, "telegram_id": channel.telegram_id}
            ]
            
            # Боты, которые используют этот канал
            bots_using_channel = db.query(PublicBot.id, PublicBot.name).join(
                BotChannel, PublicBot.id == BotChannel.public_bot_id
            ).filter(BotChannel.channel_id == target_id).all()
            
            preview["affected_bots"] = [
                {"id": bot.id, "name": bot.name} 
                for bot in bots_using_channel
            ]
            
        elif cleanup_type == "bot" and target_id:
            # Очистка по боту
            bot = db.query(PublicBot).filter(PublicBot.id == target_id).first()
            if not bot:
                raise HTTPException(status_code=404, detail=f"Бот с ID {target_id} не найден")
            
            preview["ai_results_count"] = db.query(func.count(ProcessedData.id)).filter(
                ProcessedData.public_bot_id == target_id
            ).scalar()
            
            # Каналы, связанные с ботом
            channels_for_bot = db.query(Channel.id, Channel.channel_name, Channel.telegram_id).join(
                BotChannel, Channel.id == BotChannel.channel_id
            ).filter(BotChannel.public_bot_id == target_id).all()
            
            preview["affected_channels"] = [
                {"id": ch.id, "name": ch.channel_name, "telegram_id": ch.telegram_id} 
                for ch in channels_for_bot
            ]
            preview["affected_bots"] = [{"id": bot.id, "name": bot.name}]
            
            # Посты в связанных каналах (если включить очистку постов)
            if channels_for_bot:
                telegram_ids = [ch.telegram_id for ch in channels_for_bot]
                preview["posts_count"] = db.query(func.count(PostCache.id)).filter(
                    PostCache.channel_telegram_id.in_(telegram_ids)
                ).scalar()
        
        else:
            raise HTTPException(status_code=400, detail="Неверный тип очистки или отсутствует target_id")
        
        # Примерная оценка размера (очень грубая)
        total_records = preview["posts_count"] + preview["ai_results_count"]
        size_mb = round(total_records * 0.005, 2)  # ~5KB на запись в среднем
        preview["size_estimate"] = f"{size_mb} MB"
        
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка при получении preview очистки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении preview: {str(e)}")

# === КОНЕЦ МУЛЬТИТЕНАНТНОЙ ОЧИСТКИ ДАННЫХ ===

@app.delete("/api/data/test-cleanup/{channel_id}")
async def test_cleanup_channel(channel_id: int, db: Session = Depends(get_db)):
    """Простая тестовая функция очистки"""
    try:
        logger.info(f"🔍 TEST: Начинаем тест очистки канала {channel_id}")
        
        # Проверяем существование канала
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return {"error": f"Канал с ID {channel_id} не найден"}
        
        logger.info(f"🔍 TEST: Канал найден: {channel.channel_name}")
        
        return {
            "success": True,
            "channel_id": channel_id,
            "channel_name": channel.channel_name,
            "telegram_id": channel.telegram_id,
            "message": "Тестовая функция работает"
        }
        
    except Exception as e:
        logger.error(f"🔍 TEST: Ошибка в тестовой функции: {str(e)}")
        return {"error": str(e)}

# === WEBHOOK ENDPOINTS ===

@app.post("/api/webhooks/bot-changed")
async def bot_changed_webhook(request: dict):
    """
    Webhook для уведомления MultiBotManager об изменениях конфигурации ботов
    
    Args:
        request: {"bot_id": int, "action": "created|updated|deleted|status_changed"}
    
    Returns:
        {"status": "success", "message": "Webhook processed"}
    """
    try:
        bot_id = request.get("bot_id")
        action = request.get("action", "updated")
        
        if not bot_id:
            raise HTTPException(status_code=400, detail="bot_id is required")
        
        logger.info(f"🔔 Webhook получен: bot_id={bot_id}, action={action}")
        
        # Отправляем уведомление MultiBotManager через HTTP
        multibot_manager_url = os.getenv("MULTIBOT_MANAGER_URL", "http://localhost:8001")
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{multibot_manager_url}/reload",
                    json={"bot_id": bot_id, "action": action},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ MultiBotManager уведомлен о изменении бота {bot_id}")
                    return {"status": "success", "message": f"MultiBotManager notified about bot {bot_id}"}
                else:
                    logger.warning(f"⚠️ MultiBotManager не ответил: {response.status_code}")
                    return {"status": "partial", "message": f"Webhook received but MultiBotManager unavailable"}
                    
        except Exception as e:
            logger.error(f"❌ Ошибка уведомления MultiBotManager: {e}")
            # Webhook все равно считается успешным даже если MultiBotManager недоступен
            return {"status": "partial", "message": f"Webhook received but MultiBotManager error: {str(e)}"}
            
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
