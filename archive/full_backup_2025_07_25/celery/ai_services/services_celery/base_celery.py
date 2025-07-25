#!/usr/bin/env python3
"""
BaseAIService для Celery - адаптированная версия для работы в Celery tasks
Основано на ценных кусках из CELERY.md
"""

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional, List
import logging
from celery import Task

logger = logging.getLogger(__name__)

class BaseAIServiceCelery:
    """
    Базовый класс для AI сервисов в Celery
    Адаптирован для синхронной работы в Celery tasks
    """
    
    def __init__(self, settings_manager=None):
        """
        Инициализация сервиса
        
        Args:
            settings_manager: Менеджер настроек для динамических LLM
        """
        self.settings_manager = settings_manager
        self.session = self._create_session()
        
        # Настройки по умолчанию (fallback если settings_manager нет)
        self.default_settings = {
            'model': 'gpt-4o-mini',
            'temperature': 0.3,
            'max_tokens': 2000,
            'top_p': 1.0,
            'backend_url': 'http://localhost:8000'
        }
        
        logger.info(f"🔧 {self.__class__.__name__} инициализирован для Celery")
    
    def _create_session(self) -> requests.Session:
        """
        Создает оптимизированную HTTP сессию с connection pooling
        Ценный кусок из CELERY.md для оптимизации
        """
        session = requests.Session()
        
        # Retry стратегия - только для сетевых ошибок
        retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=(500, 502, 504, 429)  # Добавлен 429 для OpenAI rate limits
        )
        
        # Connection pooling
        adapter = HTTPAdapter(
            max_retries=retry, 
            pool_connections=10, 
            pool_maxsize=10
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def get_settings(self, setting_type: str) -> Dict[str, Any]:
        """
        Получает настройки для AI сервиса
        
        Args:
            setting_type: 'categorization' или 'summarization'
        """
        if not self.settings_manager:
            logger.warning(f"SettingsManager не подключен, используем fallback настройки")
            return self.default_settings
        
        try:
            # Получаем настройки из SettingsManager
            model = self.settings_manager.get_setting(f'ai_{setting_type}_model', self.default_settings['model'])
            temperature = float(self.settings_manager.get_setting(f'ai_{setting_type}_temperature', self.default_settings['temperature']))
            max_tokens = int(self.settings_manager.get_setting(f'ai_{setting_type}_max_tokens', self.default_settings['max_tokens']))
            top_p = float(self.settings_manager.get_setting('ai_top_p', self.default_settings['top_p']))
            backend_url = self.settings_manager.get_setting('BACKEND_URL', self.default_settings['backend_url'])
            
            settings = {
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': top_p,
                'backend_url': backend_url
            }
            
            logger.info(f"📊 Настройки {setting_type}: {settings}")
            return settings
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения настроек: {e}")
            logger.info(f"🔄 Используем fallback настройки")
            return self.default_settings
    
    def make_api_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Выполняет API запрос с правильной retry логикой
        Ценный кусок из CELERY.md
        
        Args:
            method: HTTP метод
            url: URL для запроса
            **kwargs: Дополнительные параметры
        """
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logger.error(f"🌐 API запрос failed: {method} {url} - {e}")
            # Не делаем retry здесь - это делает requests.Session
            raise e
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка API запроса: {e}")
            raise e
    
    def validate_input(self, text: str) -> bool:
        """Валидация входных данных"""
        if not isinstance(text, str):
            logger.error(f"Invalid input type: {type(text)}, expected str")
            return False
        
        if not text or text.strip() == "":
            logger.warning(f"Empty input text - will skip processing")
            return False
        
        return True
    
    def create_result(self, post_data: Dict[str, Any], status: str = "success", **extra_data) -> Dict[str, Any]:
        """
        Создает стандартизированный результат обработки
        
        Args:
            post_data: Данные поста
            status: Статус обработки
            **extra_data: Дополнительные данные результата
        """
        result = {
            'post_id': post_data.get('id'),
            'channel_id': post_data.get('channel_id'),
            'timestamp': time.time(),
            'status': status,
            **extra_data
        }
        
        return result
    
    def create_fallback_result(self, post_data: Dict[str, Any], error: str = "Processing failed") -> Dict[str, Any]:
        """
        Создает fallback результат при ошибке
        
        Args:
            post_data: Данные поста
            error: Описание ошибки
        """
        return self.create_result(
            post_data,
            status="error",
            error=error,
            categories=[],
            summary=None,
            importance=5,
            urgency=5,
            significance=5
        )
    
    def log_processing_stats(self, service_name: str, processed: int, total: int, duration: float):
        """Логирует статистику обработки"""
        logger.info(f"📊 {service_name} статистика:")
        logger.info(f"   Обработано: {processed}/{total}")
        logger.info(f"   Время: {duration:.2f} сек")
        logger.info(f"   Скорость: {processed/duration:.2f} постов/сек")
        
        if processed < total:
            logger.warning(f"⚠️ Не обработано: {total - processed} постов")


class BaseAITaskCelery(Task):
    """
    Базовый Celery Task для AI сервисов
    Ценный кусок из CELERY.md - BaseAITask класс
    """
    
    def __init__(self):
        self.settings_manager = None
        self.service = None
    
    def __call__(self, *args, **kwargs):
        """Инициализация при каждом вызове для корректной работы"""
        if self.settings_manager is None:
            try:
                from utils.settings_manager import SettingsManager
                self.settings_manager = SettingsManager()
                logger.info("✅ SettingsManager инициализирован в BaseAITaskCelery")
            except ImportError:
                logger.warning("⚠️ SettingsManager не найден, работаем без него")
                self.settings_manager = None
        
        return self.run(*args, **kwargs)
    
    def retry_on_failure(self, exc, context: Dict = None):
        """
        Правильная retry логика из CELERY.md
        
        Args:
            exc: Исключение
            context: Контекст для логирования
        """
        if isinstance(exc, requests.RequestException):
            # Retry только для сетевых ошибок
            logger.warning(f"🔄 Сетевая ошибка, retry через 60 сек: {exc}")
            raise self.retry(exc=exc, countdown=60, max_retries=3)
        else:
            # Не retry для остальных ошибок - нужно исправлять код
            logger.error(f"❌ Неисправимая ошибка: {exc}", extra=context)
            return {
                "status": "error", 
                "error": str(exc),
                "context": context
            } 