from typing import Optional, Dict, Any
from pydantic import BaseModel
import aiohttp
import os
from loguru import logger

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

class PublicBotData(BaseModel):
    id: int
    name: str
    default_language: str = "ru"
    categorization_prompt: Optional[str] = None
    summarization_prompt: Optional[str] = None
    status: Optional[str] = None
    additional_data: Dict[str, Any] = {}

class PublicBot:
    """Клиент для получения информации о PublicBot из Backend API"""

    @staticmethod
    async def get(bot_id: int, backend_url: str = BACKEND_URL) -> Optional[PublicBotData]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backend_url}/api/public-bots/{bot_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return PublicBotData(**data)
                    else:
                        logger.warning(f"PublicBot {bot_id} not found. HTTP {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching PublicBot {bot_id}: {str(e)}")
            return None 