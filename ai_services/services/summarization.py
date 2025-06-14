from typing import Dict, Any, Optional
from .base import BaseAIService
from openai import AsyncOpenAI
from loguru import logger
import os

class SummarizationService(BaseAIService):
    """Сервис для генерации краткого содержания постов"""
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        max_tokens: int = 4000,
        temperature: float = 0.3,
        max_summary_length: int = 150
    ):
        super().__init__(model_name, max_tokens, temperature)
        self.max_summary_length = max_summary_length
        self.logger = logger.bind(service="SummarizationService")
        
        # Инициализируем клиент OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def process(
        self,
        text: str,
        language: str = "ru",
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Генерация краткого содержания для одного поста"""
        
        if not await self.validate_input(text):
            return await self.handle_error(ValueError("Invalid input text"))
        
        try:
            # Формируем промпт
            prompt = custom_prompt or self._get_default_prompt(language)
            
            # Вызываем OpenAI API с новым синтаксисом
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Извлекаем результат
            summary = response.choices[0].message.content.strip()
            
            return {
                "summary": summary,
                "language": language,
                "tokens_used": response.usage.total_tokens,
                "status": "success"
            }
            
        except Exception as e:
            return await self.handle_error(e, {"text_length": len(text)})
    
    async def process_batch(
        self,
        texts: list[str],
        language: str = "ru",
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> list[Dict[str, Any]]:
        """Пакетная обработка постов"""
        
        results = []
        for text in texts:
            result = await self.process(text, language, custom_prompt, **kwargs)
            results.append(result)
        
        return results
    
    def _get_default_prompt(self, language: str) -> str:
        """Получение стандартного промпта для языка"""
        
        prompts = {
            "ru": f"""Создай краткое содержание текста длиной не более {self.max_summary_length} символов.
            Сохрани ключевую информацию и важные детали.
            Используй нейтральный тон.
            Формат: краткое содержание""",
            
            "en": f"""Create a summary of the text no longer than {self.max_summary_length} characters.
            Preserve key information and important details.
            Use a neutral tone.
            Format: summary"""
        }
        
        return prompts.get(language, prompts["ru"]) 