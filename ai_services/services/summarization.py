from typing import Dict, Any, Optional
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
        
        # Инициализируем клиент OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = AsyncOpenAI(api_key=api_key)
        
        self.logger.info(f"📝 SummarizationService инициализирован")
        self.logger.info(f"   Модель: {model_name}")
        self.logger.info(f"   Max tokens: {max_tokens}")
        self.logger.info(f"   Temperature: {temperature}")
        if settings_manager:
            self.logger.info(f"   SettingsManager: подключен для динамических настроек")
        else:
            self.logger.info(f"   SettingsManager: не подключен, используются переданные параметры")
    
    async def process(
        self,
        text: str,
        language: str = "ru",
        custom_prompt: Optional[str] = None,
        max_summary_length: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Создание краткого содержания текста с динамическими настройками"""
        try:
            # Проверяем валидность входных данных
            if not await self.validate_input(text):
                return {
                    "summary": "",
                    "status": "skipped",
                    "reason": "empty_text",
                    "original_length": 0,
                    "summary_length": 0
                }
            
            # Получаем настройки суммаризации
            if self.settings_manager:
                try:
                    summarization_config = await self.settings_manager.get_ai_service_config('summarization')
                    model = summarization_config['model']
                    max_tokens = summarization_config['max_tokens']
                    temperature = summarization_config['temperature']
                    self.logger.debug(f"🤖 Используем настройки суммаризации: {model}, tokens={max_tokens}, temp={temperature}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка загрузки настроек суммаризации: {e}, используем переданные параметры")
                    model = self.model_name
                    max_tokens = self.max_tokens
                    temperature = self.temperature
            else:
                # Используем параметры переданные в конструктор
                model = self.model_name
                max_tokens = self.max_tokens
                temperature = self.temperature
                self.logger.debug(f"🤖 Используем настройки из конструктора: {model}, tokens={max_tokens}, temp={temperature}")
            
            # Формируем промпт
            prompt = custom_prompt or self._get_default_prompt(language)
            
            # Используем переданную длину или дефолтную
            summary_length = max_summary_length or self.max_summary_length
            
            # Добавляем рекомендацию по длине к кастомному промпту
            if custom_prompt and summary_length:
                # Более прямая инструкция для AI
                min_sentences = 2 if summary_length >= 200 else 1
                max_sentences = 4 if summary_length >= 400 else 3
                length_instruction = f"\n\nОБЯЗАТЕЛЬНОЕ ТРЕБОВАНИЕ: Резюме должно состоять из {min_sentences}-{max_sentences} полных предложений. Общая длина резюме должна быть в диапазоне {summary_length // 2}-{summary_length} символов. НЕ создавай слишком короткие резюме из одного предложения!"
                prompt = f"{custom_prompt}{length_instruction}"
            
            # Вызываем OpenAI API с новым синтаксисом
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=max_tokens,
                temperature=temperature
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
        max_summary_length: Optional[int] = None,
        **kwargs
    ) -> list[Dict[str, Any]]:
        """НАСТОЯЩАЯ пакетная обработка постов - одним запросом к OpenAI"""
        
        if not texts:
            return []
        
        self.logger.info(f"🚀 БАТЧЕВАЯ саммаризация {len(texts)} текстов одним запросом")
        
        try:
            # Получаем настройки суммаризации
            if self.settings_manager:
                try:
                    summarization_config = await self.settings_manager.get_ai_service_config('summarization')
                    model = summarization_config['model']
                    max_tokens = summarization_config['max_tokens']
                    temperature = summarization_config['temperature']
                    self.logger.debug(f"🤖 Батч: используем настройки суммаризации: {model}, tokens={max_tokens}, temp={temperature}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Батч: ошибка загрузки настроек суммаризации: {e}, используем переданные параметры")
                    model = self.model_name
                    max_tokens = self.max_tokens
                    temperature = self.temperature
            else:
                # Используем параметры переданные в конструктор
                model = self.model_name
                max_tokens = self.max_tokens
                temperature = self.temperature
                self.logger.debug(f"🤖 Батч: используем настройки из конструктора: {model}, tokens={max_tokens}, temp={temperature}")
            
            # Формируем промпт для батчевой обработки
            base_prompt = custom_prompt or self._get_default_prompt(language)
            
            # Используем переданную длину или дефолтную
            summary_length = max_summary_length or self.max_summary_length
            
            # Добавляем рекомендацию по длине к кастомному промпту
            if custom_prompt and summary_length:
                # Более прямая инструкция для AI
                min_sentences = 2 if summary_length >= 200 else 1
                max_sentences = 4 if summary_length >= 400 else 3
                length_instruction = f"\n\nОБЯЗАТЕЛЬНОЕ ТРЕБОВАНИЕ: Резюме должно состоять из {min_sentences}-{max_sentences} полных предложений. Общая длина резюме должна быть в диапазоне {summary_length // 2}-{summary_length} символов. НЕ создавай слишком короткие резюме из одного предложения!"
                base_prompt = f"{custom_prompt}{length_instruction}"
            
            # Создаем батчевый промпт
            batch_prompt = f"""{base_prompt}

ВАЖНО: Обработай следующие {len(texts)} текстов и верни результат в формате JSON массива.
Каждый элемент должен содержать поле "summary" с кратким содержанием соответствующего текста.

Формат ответа:
[
  {{"summary": "краткое содержание текста 1"}},
  {{"summary": "краткое содержание текста 2"}},
  ...
]

ТЕКСТЫ ДЛЯ ОБРАБОТКИ:"""

            # Добавляем все тексты с нумерацией
            for i, text in enumerate(texts, 1):
                batch_prompt += f"\n\n--- ТЕКСТ {i} ---\n{text}"
            
            # Отправляем батчевый запрос к OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": batch_prompt}
                ],
                max_tokens=max_tokens * 2,  # Увеличиваем лимит для батча
                temperature=temperature
            )
            
            # Парсим JSON ответ
            response_text = response.choices[0].message.content.strip()
            
            # 🔧 УМНЫЙ ПАРСИНГ: обрабатываем JSON в markdown блоках
            def extract_json_from_response(text: str) -> str:
                """Извлекает JSON из ответа OpenAI, обрабатывая markdown блоки"""
                
                # Вариант 1: JSON в markdown блоке ```json
                json_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
                if json_match:
                    self.logger.info("📝 Найден JSON в markdown блоке ```json")
                    return json_match.group(1).strip()
                
                # Вариант 2: JSON в блоке без языка ```
                json_match = re.search(r'```\s*\n(.*?)\n```', text, re.DOTALL)
                if json_match:
                    potential_json = json_match.group(1).strip()
                    if potential_json.startswith('[') or potential_json.startswith('{'):
                        self.logger.info("📝 Найден JSON в markdown блоке ```")
                        return potential_json
                
                # Вариант 3: Чистый JSON (начинается с [ или {)
                if text.startswith('[') or text.startswith('{'):
                    self.logger.info("📝 Найден чистый JSON")
                    return text
                
                # Вариант 4: Ищем JSON в тексте по паттерну
                json_match = re.search(r'(\[.*?\])', text, re.DOTALL)
                if json_match:
                    self.logger.info("📝 Найден JSON по паттерну в тексте")
                    return json_match.group(1)
                
                self.logger.warning("⚠️ JSON не найден, возвращаем исходный текст")
                return text
            
            # Извлекаем JSON из ответа
            clean_json = extract_json_from_response(response_text)
            
            # Пробуем распарсить JSON
            try:
                summaries_data = json.loads(clean_json)
                
                if not isinstance(summaries_data, list):
                    raise ValueError("Ответ не является массивом")
                
                if len(summaries_data) != len(texts):
                    self.logger.warning(f"⚠️ Количество результатов ({len(summaries_data)}) не совпадает с количеством текстов ({len(texts)})")
                
                # Формируем результаты
                results = []
                total_tokens = response.usage.total_tokens
                tokens_per_text = total_tokens // len(texts) if texts else 0
                
                for i, text in enumerate(texts):
                    if i < len(summaries_data) and isinstance(summaries_data[i], dict):
                        summary = summaries_data[i].get('summary', '')
                    else:
                        summary = f"Ошибка обработки текста {i+1}"
                        self.logger.warning(f"⚠️ Не удалось получить саммаризацию для текста {i+1}")
                    
                    results.append({
                        "summary": summary,
                        "language": language,
                        "tokens_used": tokens_per_text,
                        "status": "success"
                    })
                
                self.logger.info(f"✅ БАТЧЕВАЯ саммаризация завершена: {len(results)} результатов, {total_tokens} токенов")
                return results
                
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Ошибка парсинга JSON ответа: {e}")
                self.logger.error(f"Ответ OpenAI: {response_text[:500]}...")
                
                # Fallback: возвращаем пустые саммаризации
                results = []
                for i, text in enumerate(texts):
                    results.append({
                        "summary": f"Ошибка парсинга для текста {i+1}",
                        "language": language,
                        "tokens_used": 0,
                        "status": "error"
                    })
                return results
                
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка батчевой саммаризации: {e}")
            
            # Fallback: возвращаем ошибки для всех текстов
            results = []
            for i, text in enumerate(texts):
                results.append({
                    "summary": f"Критическая ошибка для текста {i+1}",
                    "language": language,
                    "tokens_used": 0,
                    "status": "error"
                })
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