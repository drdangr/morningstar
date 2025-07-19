from typing import Dict, Any, Optional, List
from .base import BaseAIService
from openai import AsyncOpenAI
from loguru import logger
import os
import json
import re

class SummarizationService(BaseAIService):
    """Сервис для генерации краткого содержания постов"""
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        max_tokens: int = 4000,
        temperature: float = 0.3,
        max_summary_length: int = 150,
        settings_manager=None
    ):
        super().__init__(model_name, max_tokens, temperature)
        self.max_summary_length = max_summary_length
        self.settings_manager = settings_manager
        self.logger = logger.bind(service="SummarizationService")
        
        # Клиент OpenAI будет инициализирован при первом использовании
        self.client = None
        
        self.logger.info("📝 SummarizationService инициализирован")
    
    async def _ensure_client(self):
        """🔑 ДИНАМИЧЕСКОЕ создание/обновление OpenAI клиента с актуальным ключом"""
        # Получаем актуальный ключ
        current_key = None
        
        if self.settings_manager:
            try:
                current_key = await self.settings_manager.get_openai_key()
                self.logger.info("🔑 Получен актуальный OpenAI ключ через SettingsManager")
            except Exception as e:
                self.logger.warning(f"⚠️ Не удалось получить ключ из SettingsManager: {e}")
        
        # Fallback на переменную окружения только если SettingsManager недоступен
        if not current_key:
            current_key = os.getenv('OPENAI_API_KEY')
            if current_key:
                self.logger.info("⚠️ Используется OpenAI ключ из переменной окружения (fallback)")
        
        if not current_key:
            raise ValueError("OpenAI API ключ не найден ни в SettingsManager, ни в переменных окружения")
        
        # Создаем/обновляем клиент если ключ изменился или клиента нет
        old_key = getattr(self.client, 'api_key', None) if self.client else None
        need_update = not self.client or old_key != current_key
        
        if need_update:
            self.client = AsyncOpenAI(api_key=current_key)
            self.logger.info(f"🔄 OpenAI клиент создан/обновлен с ключом {current_key[-10:]}")
        else:
            self.logger.debug(f"✅ OpenAI клиент актуален (ключ {current_key[-10:]})")
    
    async def close(self):
        """
        🔒 ЯВНОЕ закрытие OpenAI клиента для предотвращения ошибок Event loop is closed
        """
        if self.client:
            try:
                await self.client.close()
                self.logger.info("🔒 SummarizationService: OpenAI клиент закрыт")
            except Exception as e:
                self.logger.warning(f"⚠️ SummarizationService: ошибка закрытия OpenAI клиента: {e}")
            finally:
                self.client = None
    
    async def process(
        self,
        text: str,
        language: str = "ru",
        custom_prompt: Optional[str] = None,
        max_summary_length: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Создание краткого содержания одного текста"""
        try:
            # Инициализируем OpenAI клиент при первом использовании
            await self._ensure_client()
            
            # Проверяем валидность входных данных
            if not text or not text.strip():
                return {
                    "summary": "",
                    "status": "skipped",
                    "reason": "empty_text"
                }
            
            # Получаем настройки из SettingsManager или используем дефолтные
            model, max_tokens, temperature, top_p = await self._get_model_settings()
            
            # Формируем промпт
            summary_length = max_summary_length or self.max_summary_length
            prompt = self._build_single_prompt(custom_prompt, language, summary_length)
            
            # Вызываем OpenAI API
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
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
            self.logger.error(f"❌ Ошибка в process: {e}")
            return {
                "summary": f"Ошибка обработки: {str(e)}",
                "status": "error",
                "error": str(e)
            }
    
    async def process_batch(
        self,
        texts: List[str],
        language: str = "ru",
        custom_prompt: Optional[str] = None,
        max_summary_length: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Батчевая обработка текстов одним запросом"""
        
        if not texts:
            return []
        
        self.logger.info(f"🚀 Батчевая саммаризация {len(texts)} текстов")
        
        try:
            # Получаем настройки
            model, max_tokens, temperature, top_p = await self._get_model_settings()
            
            # Формируем батчевый промпт
            summary_length = max_summary_length or self.max_summary_length
            batch_prompt = self._build_batch_prompt(texts, custom_prompt, language, summary_length)
            
            # Отправляем запрос к OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": batch_prompt}
                ],
                max_tokens=max_tokens * 2,  # Увеличиваем для батча
                temperature=temperature,
                top_p=top_p
            )
            
            # Парсим результат
            response_text = response.choices[0].message.content.strip()
            summaries = self._parse_batch_response(response_text, len(texts))
            
            # Формируем результаты
            total_tokens = response.usage.total_tokens
            tokens_per_text = total_tokens // len(texts) if texts else 0
            
            results = []
            for i, summary in enumerate(summaries):
                results.append({
                    "summary": summary,
                    "language": language,
                    "tokens_used": tokens_per_text,
                    "status": "success"
                })
            
            self.logger.info(f"✅ Батчевая саммаризация завершена: {len(results)} результатов")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка батчевой саммаризации: {e}")
            
            # Возвращаем ошибки для всех текстов
            return [{
                "summary": f"Ошибка обработки текста {i+1}",
                "language": language,
                "tokens_used": 0,
                "status": "error",
                "error": str(e)
            } for i in range(len(texts))]
    
    async def _get_model_settings(self):
        """Получает настройки модели из SettingsManager или использует дефолтные"""
        if self.settings_manager:
            try:
                config = await self.settings_manager.get_ai_service_config('summarization')
                return (
                    config['model'],
                    config['max_tokens'],
                    config['temperature'],
                    config.get('top_p', 1.0)
                )
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка загрузки настроек: {e}")
        
        # Дефолтные значения
        return (
            self.model_name,
            self.max_tokens,
            self.temperature,
            1.0
        )
    
    def _build_single_prompt(self, custom_prompt: Optional[str], language: str, max_length: int) -> str:
        """Строит промпт для одиночной саммаризации"""
        # Базовый промпт или кастомный
        base_prompt = custom_prompt or self._get_default_prompt(language)
        
        # Добавляем ограничение по длине
        if max_length:
            length_instruction = f"\n\nЛимит длины: постарайся уложиться примерно в {max_length} символов, но не жертвуй важными частями ради этого. Лучше слегка превысить лимит, чем потерять суть или вкус текста."
            return f"{base_prompt}{length_instruction}"
        
        return base_prompt
    
    def _build_batch_prompt(self, texts: List[str], custom_prompt: Optional[str], language: str, max_length: int) -> str:
        """Строит промпт для батчевой обработки"""
        # Начинаем с инструкции о формате
        prompt = f"""Обработай следующие {len(texts)} текстов СТРОГО ПРИДЕРЖИВАЯСЬ ДЛЯ КАЖДОГО ИЗ ТЕКСТОВИНСТРУКЦИИ НИЖЕ и верни результат в формате JSON массива.
Каждый элемент должен содержать поле "summary".

Формат ответа:
[
  {{"summary": "результат обработки текста 1"}},
  {{"summary": "результат обработки текста 2"}},
  ...
]

Инструкции для обработки каждого текста:
"""
        
        # Добавляем кастомный или дефолтный промпт
        base_prompt = custom_prompt or self._get_default_prompt(language)
        prompt += base_prompt
        
        # Добавляем ограничение по длине
        if max_length:
            prompt += f"\n\nЛимит длины: постарайся уложиться примерно в {max_length} символов, но не жертвуй важными частями ради этого. Лучше слегка превысить лимит, чем потерять суть или вкус текста."
        
        # Добавляем тексты
        prompt += "\n\nТЕКСТЫ ДЛЯ ОБРАБОТКИ:"
        for i, text in enumerate(texts, 1):
            prompt += f"\n\n--- ТЕКСТ {i} ---\n{text}"
        
        return prompt
    
    def _parse_batch_response(self, response_text: str, expected_count: int) -> List[str]:
        """Парсит ответ батчевой обработки"""
        try:
            # Извлекаем JSON из ответа
            json_text = self._extract_json(response_text)
            
            # Парсим JSON
            data = json.loads(json_text)
            
            if not isinstance(data, list):
                raise ValueError("Ответ не является массивом")
            
            # Извлекаем саммари
            summaries = []
            for i in range(expected_count):
                if i < len(data) and isinstance(data[i], dict):
                    summary = data[i].get('summary', f'Ошибка извлечения саммари {i+1}')
                else:
                    summary = f'Отсутствует саммари для текста {i+1}'
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга ответа: {e}")
            self.logger.debug(f"Ответ: {response_text[:500]}...")
            
            # Возвращаем ошибки для всех текстов
            return [f"Ошибка парсинга ответа для текста {i+1}" for i in range(expected_count)]
    
    def _extract_json(self, text: str) -> str:
        """Извлекает JSON из текста, обрабатывая разные форматы"""
        # JSON в markdown блоке ```json
        match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # JSON в блоке без языка ```
        match = re.search(r'```\s*\n(.*?)\n```', text, re.DOTALL)
        if match:
            potential_json = match.group(1).strip()
            if potential_json.startswith('[') or potential_json.startswith('{'):
                return potential_json
        
        # Чистый JSON
        if text.strip().startswith('[') or text.strip().startswith('{'):
            return text.strip()
        
        # Ищем JSON массив в тексте
        match = re.search(r'(\[.*?\])', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Не нашли JSON
        return text
    
    def _get_default_prompt(self, language: str) -> str:
        """Возвращает дефолтный промпт для языка"""
        prompts = {
            "ru": """Создай краткое содержание текста.
Сохрани ключевую информацию и важные детали.
Используй нейтральный тон.""",
            
            "en": """Create a summary of the text.
Preserve key information and important details.
Use a neutral tone."""
        }
        
        return prompts.get(language, prompts["ru"]) 