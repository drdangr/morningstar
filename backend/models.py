from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, JSON, Boolean, Float, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
import os

Base = declarative_base()

# Определяем тип БД для выбора правильных типов данных
USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "true").lower() == "true"

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
    
    # Связи
    posts = relationship("PostCache", back_populates="public_bot")
    processing_queue = relationship("PostProcessingQueue", back_populates="public_bot")
    metrics = relationship("ProcessingMetrics", back_populates="public_bot")
    ai_settings = relationship("AISetting", back_populates="bot")

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
    retention_until = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи
    processing_queue = relationship("PostProcessingQueue", back_populates="post")

# Удаляем дублирующие классы PostProcessingQueue, ProcessingMetrics, AISetting
# Они должны быть определены только в main.py

# Если нужны отдельные модели для AI Services, создадим их здесь:

class AIProcessingResult(Base):
    """Результаты AI обработки постов"""
    __tablename__ = "ai_processing_results"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts_cache.id"), nullable=False)
    public_bot_id = Column(Integer, ForeignKey("public_bots.id"), nullable=False)
    
    # Результаты суммаризации
    summaries = Column(JSONB if USE_POSTGRESQL else Text, default={} if USE_POSTGRESQL else "{}")  # {ru: "summary", en: "summary"}
    
    # Результаты категоризации
    categories = Column(JSONB if USE_POSTGRESQL else Text, default=[] if USE_POSTGRESQL else "[]")  # ["Политика", "Экономика"]
    relevance_scores = Column(JSONB if USE_POSTGRESQL else Text, default=[] if USE_POSTGRESQL else "[]")  # [0.95, 0.8]
    
    # Метрики качества
    importance = Column(Float, default=0.0)
    urgency = Column(Float, default=0.0)
    significance = Column(Float, default=0.0)
    
    # Метаданные обработки
    processing_version = Column(String, default="v1.0")
    tokens_used = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)  # в секундах
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Уникальность: один результат на пост-бот пару
    __table_args__ = (
        UniqueConstraint('post_id', 'public_bot_id', name='uq_ai_result_post_bot'),
        Index('idx_ai_results_bot_date', 'public_bot_id', 'created_at'),
        Index('idx_ai_results_metrics', 'importance', 'urgency', 'significance'),
    )

# ... остальные модели остаются без изменений ... 