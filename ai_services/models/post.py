from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import os
import aiohttp
import asyncio
from loguru import logger

Base = declarative_base()

class PostData(BaseModel):
    """Pydantic модель для валидации данных поста"""
    id: int
    channel_telegram_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)  # 🔧 ИСПРАВЛЕНО: поддержка BigInteger диапазона
    telegram_message_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)  # 🔧 ИСПРАВЛЕНО: поддержка BigInteger диапазона
    title: Optional[str] = None
    content: Optional[str] = None
    media_urls: List[str] = Field(default_factory=list)
    views: int = 0
    post_date: datetime
    collected_at: datetime
    userbot_metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_status: str = "pending"
    public_bot_id: Optional[int] = None
    retention_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('processing_status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'processing', 'completed', 'failed']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        # Разрешаем пустой контент для медиа-постов
        if v and len(v.strip()) < 3:
            raise ValueError('Content must be at least 3 characters long if present')
        return v
    
    @validator('views')
    def validate_views(cls, v):
        if v < 0:
            raise ValueError('Views cannot be negative')
        return v

class Post(Base):
    """Модель поста из posts_cache"""
    __tablename__ = 'posts_cache'
    
    id = Column(BigInteger, primary_key=True)
    channel_telegram_id = Column(BigInteger, nullable=False, index=True)
    telegram_message_id = Column(BigInteger, nullable=False)
    title = Column(Text)
    content = Column(Text)
    media_urls = Column(JSONB, default=list)
    views = Column(Integer, default=0)
    post_date = Column(DateTime, nullable=False)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    userbot_metadata = Column(JSONB, default=dict)
    # processing_status = Column(String(50), default='pending')  # УБРАНО: заменено мультитенантными статусами в processed_data
    public_bot_id = Column(Integer, ForeignKey('public_bots.id'))
    retention_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    processed_results = relationship("ProcessedPost", back_populates="post")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'channel_telegram_id': self.channel_telegram_id,
            'telegram_message_id': self.telegram_message_id,
            'title': self.title,
            'content': self.content,
            'media_urls': self.media_urls or [],
            'views': self.views,
            'post_date': self.post_date.isoformat() if self.post_date else None,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'userbot_metadata': self.userbot_metadata or {},
            'processing_status': self.processing_status,
            'public_bot_id': self.public_bot_id,
            'retention_until': self.retention_until.isoformat() if self.retention_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def validate_structure(self) -> bool:
        """Валидация структуры поста"""
        try:
            PostData(**self.to_dict())
            return True
        except Exception as e:
            logger.error(f"Validation failed for post {self.id}: {str(e)}")
            return False
    
    @classmethod
    async def get_from_api(cls, post_id: int, backend_url: str = None) -> Optional['PostData']:
        """Получение поста по ID через Backend API"""
        backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{backend_url}/api/posts/cache/{post_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Получен пост {post_id} из API")
                        return PostData(**data)
                    elif response.status == 404:
                        logger.warning(f"Пост {post_id} не найден")
                        return None
                    else:
                        logger.error(f"Ошибка API при получении поста {post_id}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при получении поста {post_id}: {str(e)}")
            return None
    
    @classmethod
    async def get_many_from_api(
        cls, 
        post_ids: List[int] = None,
        processing_status: str = "pending",
        limit: int = 100,
        backend_url: str = None
    ) -> List['PostData']:
        """Получение нескольких постов через Backend API"""
        backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Формируем параметры запроса
                params = {
                    'limit': limit,
                    'processing_status': processing_status,
                    'sort_by': 'collected_at',
                    'sort_order': 'asc'
                }
                
                url = f"{backend_url}/api/posts/cache"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = []
                        
                        for post_data in data:
                            try:
                                post = PostData(**post_data)
                                posts.append(post)
                            except Exception as e:
                                logger.error(f"Ошибка валидации поста {post_data.get('id')}: {str(e)}")
                                continue
                        
                        logger.info(f"Получено {len(posts)} постов из API (статус: {processing_status})")
                        return posts
                    else:
                        logger.error(f"Ошибка API при получении постов: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Ошибка при получении постов: {str(e)}")
            return []
    
    @classmethod
    async def get_pending_posts(cls, limit: int = 100, backend_url: str = None) -> List['PostData']:
        """Получение постов со статусом 'pending' для обработки"""
        return await cls.get_many_from_api(
            processing_status="pending",
            limit=limit,
            backend_url=backend_url
        )
    
    @classmethod
    async def update_status_via_api(
        cls, 
        post_id: int, 
        new_status: str, 
        backend_url: str = None
    ) -> bool:
        """Обновление статуса поста через Backend API"""
        backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{backend_url}/api/posts/cache/{post_id}/status"
                data = {"status": new_status}
                
                async with session.put(url, json=data) as response:
                    if response.status == 200:
                        logger.debug(f"Статус поста {post_id} обновлен на '{new_status}'")
                        return True
                    else:
                        logger.error(f"Ошибка обновления статуса поста {post_id}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса поста {post_id}: {str(e)}")
            return False

    # === Новые методы-обёртки для удобства использования в AI сервисах ===
    @classmethod
    async def get(cls, post_id: int, backend_url: str = None) -> Optional['PostData']:
        """Удобный alias для get_from_api, используется в AI сервисах"""
        return await cls.get_from_api(post_id, backend_url)

    @classmethod
    async def get_many(cls, post_ids: List[int], backend_url: str = None) -> List['PostData']:
        """Alias для get_many_from_api (ограничиваемся списком конкретных ID)"""
        if not post_ids:
            return []
        # API supports filtering by IDs via query params 'ids', если нет – делаем последовательные запросы
        backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        posts: List['PostData'] = []
        try:
            async with aiohttp.ClientSession() as session:
                # Пробуем одним запросом
                ids_param = ",".join(map(str, post_ids))
                url = f"{backend_url}/api/posts/cache?ids={ids_param}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for post_data in data:
                            try:
                                posts.append(PostData(**post_data))
                            except Exception as e:
                                logger.error(f"Validation error for post: {str(e)}")
                        return posts
        except Exception as e:
            logger.warning(f"Bulk fetch not supported, falling back to individual requests: {str(e)}")

        # Fallback: отдельные запросы
        for pid in post_ids:
            p = await cls.get_from_api(pid, backend_url)
            if p:
                posts.append(p)
        return posts

class ProcessedPostData(BaseModel):
    """Pydantic модель для результатов AI обработки"""
    post_id: int = Field(..., ge=-9223372036854775808, le=9223372036854775807)  # 🔧 ИСПРАВЛЕНО: поддержка BigInteger диапазона для posts_cache.id
    public_bot_id: int
    summary: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    relevance_scores: List[float] = Field(default_factory=list)
    importance: float = Field(default=0.0, ge=0.0, le=10.0)
    urgency: float = Field(default=0.0, ge=0.0, le=10.0)
    significance: float = Field(default=0.0, ge=0.0, le=10.0)
    tokens_used: int = Field(default=0, ge=0)
    processing_time: float = Field(default=0.0, ge=0.0)
    processing_version: str = "v1.0"
    ai_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('categories', 'relevance_scores')
    def validate_categories_scores_length(cls, v, values):
        if 'categories' in values and 'relevance_scores' in values:
            if len(values['categories']) != len(values['relevance_scores']):
                raise ValueError('Categories and relevance_scores must have the same length')
        return v

class ProcessedPost(Base):
    """Модель обработанного поста (результаты AI)"""
    __tablename__ = 'ai_processing_results'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(BigInteger, ForeignKey('posts_cache.id'), nullable=False)
    public_bot_id = Column(Integer, ForeignKey('public_bots.id'), nullable=False)
    
    # Результаты суммаризации
    summaries = Column(JSONB, default=dict)  # {ru: "summary", en: "summary"}
    
    # Результаты категоризации
    categories = Column(JSONB, default=list)  # ["Политика", "Экономика"]
    relevance_scores = Column(JSONB, default=list)  # [0.95, 0.8]
    
    # Метрики качества
    importance = Column(Float, default=0.0)
    urgency = Column(Float, default=0.0)
    significance = Column(Float, default=0.0)
    
    # Метаданные обработки
    processing_version = Column(String, default="v1.0")
    tokens_used = Column(Integer, default=0)
    processing_time = Column(Float, default=0.0)  # в секундах
    ai_metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    post = relationship("Post", back_populates="processed_results")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'public_bot_id': self.public_bot_id,
            'summaries': self.summaries or {},
            'categories': self.categories or [],
            'relevance_scores': self.relevance_scores or [],
            'importance': self.importance,
            'urgency': self.urgency,
            'significance': self.significance,
            'processing_version': self.processing_version,
            'tokens_used': self.tokens_used,
            'processing_time': self.processing_time,
            'ai_metadata': self.ai_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    async def save_via_api(self, backend_url: str = None) -> bool:
        """Сохранение результата обработки через Backend API"""
        backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{backend_url}/api/ai-results"
                data = self.to_dict()
                
                async with session.post(url, json=data) as response:
                    if response.status in [200, 201]:
                        logger.debug(f"Результат обработки поста {self.post_id} сохранен")
                        return True
                    else:
                        logger.error(f"Ошибка сохранения результата поста {self.post_id}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Ошибка при сохранении результата поста {self.post_id}: {str(e)}")
            return False

# Утилиты для работы с постами
class PostProcessor:
    """Утилитарный класс для обработки постов"""
    
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or os.getenv("BACKEND_API_URL", "http://localhost:8000")
    
    async def get_posts_for_processing(self, limit: int = 100) -> List[PostData]:
        """Получение постов для обработки"""
        return await Post.get_pending_posts(limit=limit, backend_url=self.backend_url)
    
    async def mark_post_processing(self, post_id: int) -> bool:
        """Отметить пост как обрабатываемый"""
        return await Post.update_status_via_api(
            post_id=post_id, 
            new_status="processing", 
            backend_url=self.backend_url
        )
    
    async def mark_post_completed(self, post_id: int) -> bool:
        """Отметить пост как обработанный"""
        return await Post.update_status_via_api(
            post_id=post_id, 
            new_status="completed", 
            backend_url=self.backend_url
        )
    
    async def mark_post_failed(self, post_id: int) -> bool:
        """Отметить пост как неудачно обработанный"""
        return await Post.update_status_via_api(
            post_id=post_id, 
            new_status="failed", 
            backend_url=self.backend_url
        )
    
    async def validate_posts_batch(self, posts: List[PostData]) -> List[PostData]:
        """Валидация батча постов"""
        valid_posts = []
        
        for post in posts:
            try:
                # Проверяем что пост имеет хотя бы один из: контент, заголовок, медиа
                has_content = post.content and len(post.content.strip()) >= 3
                has_title = post.title and len(post.title.strip()) >= 3
                has_media = post.media_urls and len(post.media_urls) > 0
                
                if not (has_content or has_title or has_media):
                    logger.warning(f"Пост {post.id} пропущен: нет контента, заголовка или медиа")
                    continue
                
                if not post.post_date:
                    logger.warning(f"Пост {post.id} пропущен: отсутствует дата поста")
                    continue
                
                valid_posts.append(post)
                
            except Exception as e:
                logger.error(f"Ошибка валидации поста {post.id}: {str(e)}")
                continue
        
        logger.info(f"Валидация завершена: {len(valid_posts)}/{len(posts)} постов прошли проверку")
        return valid_posts 