from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from loguru import logger
from datetime import datetime, timedelta
import os, openai

from ai_services.models.post import Post, ProcessedPost
from ai_services.models.bot import PublicBot
from ai_services.utils.metrics import ProcessingMetrics
from ai_services.services.summarization import SummarizationService
from ai_services.services.categorization import CategorizationService

# Инициализация FastAPI
app = FastAPI(
    title="MorningStarBot3 AI Services",
    description="AI сервисы для обработки постов и генерации дайджестов",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class SummarizeRequest(BaseModel):
    text: str
    language: str = "ru"
    custom_prompt: Optional[str] = None

class CategorizeRequest(BaseModel):
    text: str
    custom_prompt: Optional[str] = None

class BatchRequest(BaseModel):
    texts: List[str]
    language: str = "ru"
    custom_prompt: Optional[str] = None

# Новые модели данных
class PostProcessingRequest(BaseModel):
    post_id: int
    public_bot_id: int
    priority: int = 0

class BatchProcessingRequest(BaseModel):
    public_bot_id: int
    post_ids: List[int]
    priority: int = 0

class ProcessingStatus(BaseModel):
    post_id: int
    public_bot_id: int
    status: str
    progress: float
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

# Устанавливаем API-ключ для openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не найден в переменных окружения или .env")

openai.api_key = OPENAI_API_KEY

# Инициализация сервисов
summarization_service = SummarizationService()
categorization_service = CategorizationService(openai_api_key=OPENAI_API_KEY)

# Роуты
@app.post("/api/v1/summarize")
async def summarize(request: SummarizeRequest):
    """Суммаризация текста"""
    try:
        result = await summarization_service.process(
            request.text,
            language=request.language,
            custom_prompt=request.custom_prompt
        )
        return result
    except Exception as e:
        logger.error(f"Error in summarize: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/categorize")
async def categorize(request: CategorizeRequest):
    """Категоризация текста"""
    try:
        result = await categorization_service.process(
            request.text,
            custom_prompt=request.custom_prompt
        )
        return result
    except Exception as e:
        logger.error(f"Error in categorize: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process-batch")
async def process_batch(request: BatchRequest):
    """Пакетная обработка текстов"""
    try:
        # Параллельная обработка
        summarize_results = await summarization_service.process_batch(
            request.texts,
            language=request.language,
            custom_prompt=request.custom_prompt
        )
        
        categorize_results = await categorization_service.process_batch(
            request.texts,
            custom_prompt=request.custom_prompt
        )
        
        # Объединяем результаты
        results = []
        for i in range(len(request.texts)):
            results.append({
                "summary": summarize_results[i],
                "categories": categorize_results[i]
            })
        
        return results
    except Exception as e:
        logger.error(f"Error in process_batch: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {
        "status": "ok",
        "services": {
            "summarization": summarization_service.get_metrics(),
            "categorization": categorization_service.get_metrics()
        }
    }

@app.post("/api/v1/process-post")
async def process_post(
    request: PostProcessingRequest,
    background_tasks: BackgroundTasks
) -> ProcessingStatus:
    """Обработка одного поста для конкретного бота"""
    try:
        # Получаем пост из БД
        post = await Post.get(request.post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
            
        # Получаем бота
        bot = await PublicBot.get(request.public_bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        # Запускаем обработку в фоне
        background_tasks.add_task(
            process_post_background,
            post=post,
            bot=bot,
            priority=request.priority
        )
        
        return ProcessingStatus(
            post_id=request.post_id,
            public_bot_id=request.public_bot_id,
            status="pending",
            progress=0.0
        )
        
    except Exception as e:
        logger.error(f"Error in process_post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process-batch")
async def process_batch_posts(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks
) -> List[ProcessingStatus]:
    """Пакетная обработка постов для бота"""
    try:
        # Получаем бота
        bot = await PublicBot.get(request.public_bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
            
        # Получаем посты
        posts = await Post.get_many(request.post_ids)
        if not posts:
            raise HTTPException(status_code=404, detail="No posts found")
            
        # Запускаем обработку в фоне
        statuses = []
        for post in posts:
            background_tasks.add_task(
                process_post_background,
                post=post,
                bot=bot,
                priority=request.priority
            )
            statuses.append(ProcessingStatus(
                post_id=post.id,
                public_bot_id=request.public_bot_id,
                status="pending",
                progress=0.0
            ))
            
        return statuses
        
    except Exception as e:
        logger.error(f"Error in process_batch_posts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/processing-status/{post_id}/{public_bot_id}")
async def get_processing_status(
    post_id: int,
    public_bot_id: int
) -> ProcessingStatus:
    """Получение статуса обработки поста"""
    try:
        # Получаем статус из очереди
        status = await ProcessingMetrics.get_status(post_id, public_bot_id)
        if not status:
            raise HTTPException(status_code=404, detail="Processing status not found")
            
        return status
        
    except Exception as e:
        logger.error(f"Error in get_processing_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/bot-metrics/{public_bot_id}")
async def get_bot_metrics(
    public_bot_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Получение метрик обработки для бота"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()
            
        metrics = await ProcessingMetrics.get_bot_metrics(
            public_bot_id,
            start_date,
            end_date
        )
        
        return {
            "bot_id": public_bot_id,
            "period": {
                "start": start_date,
                "end": end_date
            },
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error in get_bot_metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Фоновые задачи
async def process_post_background(
    post: Post,
    bot: PublicBot,
    priority: int = 0
):
    """Фоновая обработка поста"""
    try:
        # Обновляем статус
        await ProcessingMetrics.update_status(
            post.id,
            bot.id,
            "processing",
            0.0
        )
        
        # Суммаризация
        summary_result = await summarization_service.process(
            post.content,
            language=bot.default_language,
            custom_prompt=bot.summarization_prompt
        )
        
        # Категоризация
        category_result = await categorization_service.process(
            post.content,
            custom_prompt=bot.categorization_prompt
        )
        
        # Сохраняем результат
        processed_post = ProcessedPost(
            post_id=post.id,
            public_bot_id=bot.id,
            summaries={bot.default_language: summary_result["summary"]},
            categories=category_result["categories"],
            relevance_scores=category_result.get("relevance_scores", []),
            importance=category_result.get("importance", 0.0),
            urgency=category_result.get("urgency", 0.0),
            significance=category_result.get("significance", 0.0),
            tokens_used=summary_result.get("tokens_used", 0) + category_result.get("tokens_used", 0),
            processing_time=(datetime.utcnow() - post.collected_at).total_seconds(),
            processing_version="v1.0",
        )
        await processed_post.save_via_api()
        
        # Обновляем метрики
        await ProcessingMetrics.update_metrics(
            bot.id,
            processed_post
        )
        
        # Обновляем статус
        await ProcessingMetrics.update_status(
            post.id,
            bot.id,
            "completed",
            1.0,
            metrics={
                "tokens_used": processed_post.tokens_used,
                "processing_time": processed_post.processing_time
            }
        )
        
    except Exception as e:
        logger.error(f"Error in process_post_background: {str(e)}")
        await ProcessingMetrics.update_status(
            post.id,
            bot.id,
            "error",
            0.0,
            error=str(e)
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 