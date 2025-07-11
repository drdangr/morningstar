#!/usr/bin/env python3
"""
SettingsManager - Централизованное управление настройками AI сервисов
Загружает настройки из Backend API с кэшированием и fallback механизмами
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
from loguru import logger
import os

class SettingsManager:
    """Менеджер настроек для AI сервисов"""
    
    def __init__(self, backend_url: str = None, cache_ttl: int = 300):
        if backend_url is None:
            backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
        """
        Инициализация SettingsManager
        
        Args:
            backend_url: URL Backend API
            cache_ttl: Время жизни кэша в секундах (по умолчанию 5 минут)
        """
        self.backend_url = backend_url
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamp = 0
        self.logger = logger.bind(component="SettingsManager")
        
        self.logger.info(f"🔧 SettingsManager инициализирован: {backend_url}")
    
    async def get_ai_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Получает конфигурацию AI сервиса из Backend API
        
        Args:
            service_name: Имя сервиса (categorization, summarization, analysis)
            
        Returns:
            Словарь с настройками: model, max_tokens, temperature
            Для summarization дополнительно: top_p
        """
        try:
            # Проверяем кэш
            cached_settings = await self.get_cached_settings()
            if cached_settings:
                config = self._extract_service_config(cached_settings, service_name)
                if config:
                    self.logger.debug(f"🎯 Настройки {service_name} получены из кэша")
                    return config
            
            # Загружаем из API если кэш пуст или устарел
            fresh_settings = await self._load_settings_from_api()
            if fresh_settings:
                config = self._extract_service_config(fresh_settings, service_name)
                if config:
                    self.logger.info(f"✅ Настройки {service_name} загружены из API")
                    return config
            
            # Fallback если API недоступен
            fallback_config = self.get_fallback_config(service_name)
            self.logger.warning(f"⚠️ Используются fallback настройки для {service_name}")
            return fallback_config
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения настроек {service_name}: {e}")
            return self.get_fallback_config(service_name)
    
    async def get_cached_settings(self) -> Optional[Dict[str, Any]]:
        """
        Возвращает кэшированные настройки если они актуальны
        
        Returns:
            Словарь настроек или None если кэш устарел
        """
        current_time = time.time()
        
        if (self._cache and 
            self._cache_timestamp > 0 and 
            (current_time - self._cache_timestamp) < self.cache_ttl):
            
            self.logger.debug(f"📦 Возвращаем кэшированные настройки (возраст: {int(current_time - self._cache_timestamp)}с)")
            return self._cache
        
        return None
    
    async def _load_settings_from_api(self) -> Optional[Dict[str, Any]]:
        """
        Загружает настройки из Backend API и обновляет кэш
        
        Returns:
            Словарь настроек или None при ошибке
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/settings") as response:
                    if response.status == 200:
                        settings_list = await response.json()
                        
                        # Преобразуем список в словарь key->value
                        settings_dict = {s['key']: s['value'] for s in settings_list}
                        
                        # Обновляем кэш
                        self._cache = settings_dict
                        self._cache_timestamp = time.time()
                        
                        ai_settings_count = len([k for k in settings_dict.keys() if k.startswith('ai_')])
                        self.logger.info(f"🔄 Настройки обновлены из API: {ai_settings_count} AI настроек")
                        
                        return settings_dict
                    else:
                        self.logger.error(f"❌ Backend API недоступен: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки настроек из API: {e}")
            return None
    
    def _extract_service_config(self, settings: Dict[str, Any], service_name: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает настройки для конкретного AI сервиса из общих настроек
        
        Args:
            settings: Общие настройки системы
            service_name: Имя сервиса
            
        Returns:
            Конфигурация сервиса или None
        """
        try:
            model_key = f"ai_{service_name}_model"
            tokens_key = f"ai_{service_name}_max_tokens"
            temp_key = f"ai_{service_name}_temperature"
            
            # Основные настройки для всех сервисов
            base_keys = [model_key, tokens_key, temp_key]
            
            if all(key in settings for key in base_keys):
                config = {
                    'model': settings[model_key],
                    'max_tokens': int(settings[tokens_key]),
                    'temperature': float(settings[temp_key])
                }
                
                # Дополнительные настройки для summarization
                if service_name == 'summarization':
                    top_p_key = f"ai_{service_name}_top_p"
                    if top_p_key in settings:
                        config['top_p'] = float(settings[top_p_key])
                        self.logger.debug(f"🎯 Добавлен параметр top_p: {config['top_p']}")
                    else:
                        # Fallback значение для top_p
                        config['top_p'] = 1.0
                        self.logger.debug(f"⚠️ Параметр {top_p_key} не найден, используется fallback: 1.0")
                
                # Валидация настроек
                if self._validate_config(config, service_name):
                    return config
                else:
                    self.logger.warning(f"⚠️ Настройки {service_name} не прошли валидацию")
                    return None
            else:
                missing_keys = [key for key in base_keys if key not in settings]
                self.logger.warning(f"⚠️ Отсутствуют настройки для {service_name}: {missing_keys}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения настроек {service_name}: {e}")
            return None
    
    def _validate_config(self, config: Dict[str, Any], service_name: str) -> bool:
        """
        Валидирует настройки AI сервиса
        
        Args:
            config: Конфигурация для валидации
            service_name: Имя сервиса
            
        Returns:
            True если настройки валидны
        """
        try:
            # Проверяем модель
            valid_models = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo', 'gpt-4']
            if config['model'] not in valid_models:
                self.logger.warning(f"⚠️ Неизвестная модель {config['model']} для {service_name}")
                return False
            
            # Проверяем max_tokens
            if not (100 <= config['max_tokens'] <= 8000):
                self.logger.warning(f"⚠️ max_tokens {config['max_tokens']} вне диапазона 100-8000 для {service_name}")
                return False
            
            # Проверяем temperature
            if not (0.0 <= config['temperature'] <= 2.0):
                self.logger.warning(f"⚠️ temperature {config['temperature']} вне диапазона 0.0-2.0 для {service_name}")
                return False
            
            # Проверяем top_p для summarization
            if service_name == 'summarization' and 'top_p' in config:
                if not (0.0 <= config['top_p'] <= 1.0):
                    self.logger.warning(f"⚠️ top_p {config['top_p']} вне диапазона 0.0-1.0 для {service_name}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации настроек {service_name}: {e}")
            return False
    
    def get_fallback_config(self, service_name: str) -> Dict[str, Any]:
        """
        Возвращает fallback настройки при недоступности API
        
        Args:
            service_name: Имя сервиса
            
        Returns:
            Fallback конфигурация
        """
        fallback_configs = {
            'categorization': {
                'model': 'gpt-4o-mini',
                'max_tokens': 1000,
                'temperature': 0.3
            },
            'summarization': {
                'model': 'gpt-4o',
                'max_tokens': 2000,
                'temperature': 0.7,
                'top_p': 1.0
            },
            'analysis': {
                'model': 'gpt-4o-mini', 
                'max_tokens': 1500,
                'temperature': 0.5
            }
        }
        
        config = fallback_configs.get(service_name, fallback_configs['categorization'])
        self.logger.info(f"🔄 Fallback настройки для {service_name}: {config}")
        return config
    
    async def refresh_cache(self) -> bool:
        """
        Принудительно обновляет кэш настроек
        
        Returns:
            True если обновление успешно
        """
        self.logger.info("🔄 Принудительное обновление кэша настроек...")
        fresh_settings = await self._load_settings_from_api()
        return fresh_settings is not None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о состоянии кэша
        
        Returns:
            Информация о кэше
        """
        current_time = time.time()
        cache_age = int(current_time - self._cache_timestamp) if self._cache_timestamp > 0 else -1
        
        return {
            'cache_size': len(self._cache),
            'cache_age_seconds': cache_age,
            'cache_ttl_seconds': self.cache_ttl,
            'is_cache_valid': cache_age >= 0 and cache_age < self.cache_ttl,
            'ai_settings_count': len([k for k in self._cache.keys() if k.startswith('ai_')]) if self._cache else 0
        } 