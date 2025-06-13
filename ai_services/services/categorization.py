from typing import Dict, Any, Optional, List
from .base import BaseAIService
import openai
from loguru import logger

class CategorizationService(BaseAIService):
    """Сервис для категоризации постов"""
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        max_tokens: int = 4000,
        temperature: float = 0.3,
        categories: Optional[List[str]] = None
    ):
        super().__init__(model_name, max_tokens, temperature)
        self.categories = categories or [
            "Политика", "Экономика", "Технологии", "Наука",
            "Культура", "Спорт", "Общество", "Происшествия"
        ]
        self.logger = logger.bind(service="CategorizationService")
    
    async def process(
        self,
        text: str,
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Категоризация одного поста"""
        
        if not await self.validate_input(text):
            return await self.handle_error(ValueError("Invalid input text"))
        
        try:
            # Формируем промпт
            prompt = custom_prompt or self._get_default_prompt()
            
            # Вызываем OpenAI API
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Парсим результат
            result = self._parse_response(response.choices[0].message.content)
            
            return {
                **result,
                "tokens_used": response.usage.total_tokens,
                "status": "success"
            }
            
        except Exception as e:
            return await self.handle_error(e, {"text_length": len(text)})
    
    async def process_batch(
        self,
        texts: list[str],
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> list[Dict[str, Any]]:
        """Пакетная категоризация постов"""
        
        results = []
        for text in texts:
            result = await self.process(text, custom_prompt, **kwargs)
            results.append(result)
        
        return results
    
    def _get_default_prompt(self) -> str:
        """Получение стандартного промпта"""
        
        return f"""Проанализируй текст и определи:
1. Категории из списка: {', '.join(self.categories)}
2. Релевантность для каждой категории (0-1)
3. Важность (1-10)
4. Срочность (1-10)
5. Значимость (1-10)

Формат ответа в JSON:
{{
    "categories": ["категория1", "категория2"],
    "relevance_scores": [0.95, 0.8],
    "importance": 8,
    "urgency": 6,
    "significance": 7
}}"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Парсинг ответа от AI"""
        
        try:
            # Извлекаем JSON из ответа
            import json
            import re
            
            # Ищем JSON в тексте
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            result = json.loads(json_match.group())
            
            # Валидация полей
            required_fields = ["categories", "relevance_scores", "importance", "urgency", "significance"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            return {
                "categories": [],
                "relevance_scores": [],
                "importance": 0,
                "urgency": 0,
                "significance": 0,
                "error": str(e)
            } 