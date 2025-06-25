import sys
import os
# Добавляем путь к ai_services для корректных импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from models.post import ProcessedPost

class ProcessingMetrics:
    """Утилита для работы с метриками обработки"""
    
    @staticmethod
    async def update_status(
        post_id: int,
        public_bot_id: int,
        status: str,
        progress: float,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """Обновление статуса обработки поста"""
        try:
            # TODO: Реализовать обновление в БД
            logger.info(
                f"Updated processing status: post_id={post_id}, "
                f"bot_id={public_bot_id}, status={status}, "
                f"progress={progress}, error={error}"
            )
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
    
    @staticmethod
    async def get_status(
        post_id: int,
        public_bot_id: int
    ) -> Dict[str, Any]:
        """Получение статуса обработки поста"""
        try:
            # TODO: Реализовать получение из БД
            return {
                "post_id": post_id,
                "public_bot_id": public_bot_id,
                "status": "pending",
                "progress": 0.0
            }
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return None
    
    @staticmethod
    async def update_metrics(
        public_bot_id: int,
        processed_post: ProcessedPost
    ):
        """Обновление метрик бота"""
        try:
            # TODO: Реализовать обновление в БД
            logger.info(
                f"Updated bot metrics: bot_id={public_bot_id}, "
                f"post_id={processed_post.post_id}, "
                f"tokens={processed_post.tokens_used}, "
                f"time={processed_post.processing_time}"
            )
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    @staticmethod
    async def get_bot_metrics(
        public_bot_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Получение метрик бота за период"""
        try:
            # TODO: Реализовать получение из БД
            return {
                "total_posts": 0,
                "processed_posts": 0,
                "failed_posts": 0,
                "avg_processing_time": 0.0,
                "total_tokens_used": 0,
                "categories_distribution": {},
                "quality_metrics": {
                    "avg_importance": 0.0,
                    "avg_urgency": 0.0,
                    "avg_significance": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error getting bot metrics: {str(e)}")
            return {} 