from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from loguru import logger

class BaseAIService(ABC):
    """Базовый класс для всех AI сервисов"""
    
    def __init__(self, model_name: str, max_tokens: int = 4000, temperature: float = 0.3):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logger.bind(service=self.__class__.__name__)
        
    @abstractmethod
    async def process(self, text: str, **kwargs) -> Dict[str, Any]:
        """Обработка текста AI моделью"""
        pass
    
    @abstractmethod
    async def process_batch(self, texts: list[str], **kwargs) -> list[Dict[str, Any]]:
        """Пакетная обработка текстов"""
        pass
    
    async def validate_input(self, text: str) -> bool:
        """Валидация входных данных"""
        if not isinstance(text, str):
            self.logger.error(f"Invalid input type: {type(text)}, expected str")
            return False
        
        if not text or text.strip() == "":
            self.logger.warning(f"Empty input text - will skip processing")
            return False
        
        return True
    
    async def handle_error(self, error: Exception, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Обработка ошибок"""
        self.logger.error(f"Error in {self.__class__.__name__}: {str(error)}", extra=context)
        return {
            "error": str(error),
            "status": "error",
            "context": context
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Получение метрик сервиса"""
        return {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        } 