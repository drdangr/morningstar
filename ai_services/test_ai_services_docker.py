#!/usr/bin/env python3
"""
Тест AI Services в Docker контейнере с обновленным OpenAI ключом
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Добавляем пути для импорта
sys.path.append('/app')
sys.path.append('/app/services')
sys.path.append('/app/utils')

async def test_ai_services():
    """Тестируем AI Services в Docker контейнере"""
    
    print("🚀 Тест AI Services в Docker контейнере")
    print("=" * 50)
    
    try:
        # Импорт модулей
        from services.categorization import CategorizationService
        from utils.settings_manager import SettingsManager
        
        print("✅ Модули успешно импортированы")
        
        # Тестируем SettingsManager
        settings = SettingsManager()
        openai_key = await settings.get_openai_key()
        
        if openai_key:
            masked_key = f"{openai_key[:8]}...{openai_key[-4:]}" if len(openai_key) > 12 else "***"
            print(f"🔑 OpenAI ключ получен: {masked_key}")
        else:
            print("❌ OpenAI ключ не найден в SettingsManager")
            return False
        
        # Тестируем CategorizationService
        print("\n🤖 Тестируем CategorizationService...")
        service = CategorizationService(openai_key, backend_url="http://backend:8000")
        
        # Создаем тестовый пост
        from models.post import Post
        
        test_post = Post(
            id=999,
            content="Новая технология искусственного интеллекта революционизирует медицину",
            channel_telegram_id=12345,
            telegram_message_id=67890,
            post_date=datetime.fromisoformat("2025-07-18T10:00:00"),
            collected_at=datetime.fromisoformat("2025-07-18T10:00:00")
        )
        
        test_bot_id = 1  # Используем реальный бот "MorningStarPublic"
        
        print(f"📝 Тестовый пост: {test_post.content}")
        print(f"🤖 Bot ID: {test_bot_id}")
        
        # Выполняем категоризацию
        result = await service.process_with_bot_config([test_post], test_bot_id)
        
        print(f"\n📊 Результат категоризации:")
        print(f"   Количество обработанных постов: {len(result)}")
        
        if result and len(result) > 0:
            first_result = result[0]
            print(f"   Первый результат: {first_result}")
            
            # Проверяем, что есть хотя бы один результат
            if 'category' in first_result or 'categories' in first_result:
                print("\n✅ УСПЕХ: AI Services работают корректно!")
                return True
            else:
                print("\n⚠️ ЧАСТИЧНЫЙ УСПЕХ: Категоризация выполнена, но формат результата отличается")
                return True
        else:
            print("\n❌ ОШИБКА: Категоризация не вернула результат")
            return False
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_services())
    sys.exit(0 if success else 1) 