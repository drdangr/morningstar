#!/usr/bin/env python3
"""
Упрощенный тест OpenAI connection через SettingsManager
"""

import asyncio
import sys
sys.path.append('/app')

from utils.settings_manager import SettingsManager

async def test_openai_connection():
    """Тест OpenAI connection через SettingsManager"""
    print("🔌 Testing OpenAI connection through SettingsManager...")
    
    try:
        # Создаем SettingsManager
        settings_manager = SettingsManager()
        print("✅ SettingsManager created")
        
        # Получаем OpenAI ключ
        print("🔑 Getting OpenAI key...")
        openai_key = await settings_manager.get_openai_key()
        print(f"✅ OpenAI key received: {openai_key[:20]}...")
        
        # Тестируем OpenAI API
        print("🚀 Testing OpenAI API...")
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print(f"✅ OpenAI API response: {response.choices[0].message.content}")
        print("🎉 OpenAI connection test SUCCESS!")
        
    except Exception as e:
        print(f"❌ OpenAI connection test FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_openai_connection()) 