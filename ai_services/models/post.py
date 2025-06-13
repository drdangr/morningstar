from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Post(Base):
    """Модель поста из posts_cache"""
    __tablename__ = 'posts_cache'
    
    id = Column(Integer, primary_key=True)
    channel_telegram_id = Column(Integer, nullable=False)
    telegram_message_id = Column(Integer, nullable=False)
    title = Column(Text)
    content = Column(Text)
    media_urls = Column(JSON, default=list)
    views = Column(Integer, default=0)
    post_date = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    userbot_metadata = Column(JSON, default=dict)
    processing_status = Column(String(50), default='pending')
    public_bot_id = Column(Integer, ForeignKey('public_bots.id'))
    retention_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    processed_results = relationship("ProcessedPost", back_populates="post")
    
    @classmethod
    async def get(cls, post_id: int) -> 'Post':
        """Получение поста по ID"""
        # TODO: Реализовать получение из БД
        pass
    
    @classmethod
    async def get_many(cls, post_ids: list[int]) -> list['Post']:
        """Получение нескольких постов по ID"""
        # TODO: Реализовать получение из БД
        pass

class ProcessedPost(Base):
    """Модель обработанного поста"""
    __tablename__ = 'processed_posts'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts_cache.id'), nullable=False)
    public_bot_id = Column(Integer, ForeignKey('public_bots.id'), nullable=False)
    summary = Column(Text)
    categories = Column(JSON)
    relevance_scores = Column(JSON)
    importance = Column(Integer)
    urgency = Column(Integer)
    significance = Column(Integer)
    tokens_used = Column(Integer)
    processing_time = Column(Float)  # в секундах
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    post = relationship("Post", back_populates="processed_results")
    
    async def save(self):
        """Сохранение результата обработки"""
        # TODO: Реализовать сохранение в БД
        pass 