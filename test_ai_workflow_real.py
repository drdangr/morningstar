#!/usr/bin/env python3
"""
Тестовый скрипт для Stage 3 - AI Processing & Topic-based Filtering
Использует РЕАЛЬНУЮ структуру данных как от userbot в Stage 2
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# N8N webhook URL
WEBHOOK_URL = "http://localhost:5678/webhook/telegram-posts"

# Данные в ТОЧНО ТАКОЙ ЖЕ структуре как от userbot Stage 2
real_format_data = {
    "timestamp": "2025-12-07T22:32:15.271042",
    "collection_stats": {
        "total_posts": 4,
        "successful_channels": 2,
        "failed_channels": 0,
        "channels_processed": [
            "@ai_news",
            "@tech_trends"
        ]
    },
    "posts": [
        {
            "id": 12345,
            "channel_id": 1001,
            "channel_username": "@ai_news",
            "channel_title": "AI News",
            "text": "OpenAI выпустил новую модель GPT-5, которая превосходит предыдущие версии по всем метрикам. Модель способна решать сложные математические задачи и писать код на профессиональном уровне. Доступ к модели получат разработчики через API уже в следующем месяце.",
            "date": "2025-12-07T20:00:00+00:00",
            "views": 125000,
            "forwards": 890,
            "replies": 45,
            "url": "https://t.me/ai_news/12345",
            "media_type": "text"
        },
        {
            "id": 12346,
            "channel_id": 1001,
            "channel_username": "@ai_news",
            "channel_title": "AI News",
            "text": "Сегодня у меня было вкусное мороженое 🍦 А еще я пошел в спортзал. Тренировка была тяжелой!",
            "date": "2025-12-07T19:30:00+00:00",
            "views": 500,
            "forwards": 2,
            "replies": 1,
            "url": "https://t.me/ai_news/12346",
            "media_type": "text"
        },
        {
            "id": 54321,
            "channel_id": 1002,
            "channel_username": "@tech_trends",
            "channel_title": "Tech Trends",
            "text": "Анализ рынка криптовалют показывает рост Bitcoin на 15% за последнюю неделю. Эксперты связывают это с принятием новых регулятивных мер в Европе и увеличением институциональных инвестиций. Прогнозы на следующий квартал остаются оптимистичными.",
            "date": "2025-12-07T18:45:00+00:00",
            "views": 87500,
            "forwards": 520,
            "replies": 78,
            "url": "https://t.me/tech_trends/54321",
            "media_type": "text"
        },
        {
            "id": 54322,
            "channel_id": 1002,
            "channel_username": "@tech_trends",
            "channel_title": "Tech Trends",
            "text": "🎁🎉 СУПЕР АКЦИЯ!!! 🎉🎁 Только сегодня скидка 90% на курс по заработку в интернете!!! 💰💰💰 Жми ссылку быстрее!!! Осталось всего 3 места!!!",
            "date": "2025-12-07T17:15:00+00:00",
            "views": 1200,
            "forwards": 5,
            "replies": 0,
            "url": "https://t.me/tech_trends/54322",
            "media_type": "text"
        }
    ],
    "webhookUrl": "http://localhost:5678/webhook/telegram-posts",
    "executionMode": "production"
}

async def test_ai_workflow_diagnosis():
    """Диагностика проблемы с OpenAI узлом в N8N workflow"""
    
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ OpenAI УЗЛА")
    print("=" * 60)
    
    backend_url = "http://localhost:8000"
    
    # Шаг 1: Проверяем настройку COLLECTION_DEPTH_DAYS
    print("\n1. 📋 Проверяем настройку COLLECTION_DEPTH_DAYS...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/config/COLLECTION_DEPTH_DAYS") as response:
                if response.status == 200:
                    data = await response.json()
                    collection_days = data.get('value', 1)
                    print(f"✅ COLLECTION_DEPTH_DAYS: {collection_days} дней")
                    
                    # Оценка объема данных за указанный период
                    estimated_posts_per_day = 50  # Примерная оценка
                    estimated_total_posts = estimated_posts_per_day * int(collection_days)
                    print(f"📊 Ожидаемое количество постов: ~{estimated_total_posts}")
                    
                    if estimated_total_posts > 100:
                        print(f"⚠️ ПОТЕНЦИАЛЬНАЯ ПРОБЛЕМА: Слишком много постов для OpenAI API")
                        print(f"   Рекомендация: добавить лимит MAX_POSTS_FOR_AI_ANALYSIS")
                else:
                    print(f"❌ Ошибка получения настройки: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Шаг 2: Проверяем последние дайджесты
    print("\n2. 📈 Анализ последних дайджестов...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/digests?limit=3") as response:
                if response.status == 200:
                    digests = await response.json()
                    print(f"✅ Найдено {len(digests)} последних дайджестов")
                    
                    for i, digest in enumerate(digests):
                        print(f"\n  📄 Дайджест {i+1}:")
                        print(f"     ID: {digest.get('digest_id', 'N/A')}")
                        print(f"     Общий постов: {digest.get('total_posts', 0)}")
                        print(f"     Релевантных: {digest.get('relevant_posts', 0)}")
                        print(f"     Каналов: {digest.get('channels_processed', 0)}")
                        print(f"     Время: {digest.get('processed_at', 'N/A')}")
                        
                        # Анализ данных дайджеста
                        try:
                            digest_data = json.loads(digest.get('digest_data', '{}'))
                            original_posts = digest_data.get('summary', {}).get('original_posts', 0)
                            if original_posts > 0:
                                print(f"     📊 Исходных постов собрано: {original_posts}")
                                if original_posts > 100:
                                    print(f"     ⚠️ Много постов - возможна перегрузка OpenAI")
                        except:
                            pass
                            
                else:
                    print(f"❌ Ошибка получения дайджестов: {response.status}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Шаг 3: Рекомендации по решению
    print("\n3. 🛠️ РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ:")
    print("\nПроблема: OpenAI API захлебывается от большого количества постов")
    print("\nВарианты решения:")
    print("1. 📉 ДОБАВИТЬ ЛИМИТ в 'Prepare for AI' node:")
    print("   - Ограничить до 50-100 постов максимум")
    print("   - Код: postsForAI = postsForAI.slice(0, 50)")
    
    print("\n2. 📊 УВЕЛИЧИТЬ maxTokens в OpenAI node:")
    print("   - Сейчас: 2000 tokens")
    print("   - Попробовать: 4000-8000 tokens")
    
    print("\n3. 🎯 ФИЛЬТРАЦИЯ ПО КАЧЕСТВУ:")
    print("   - Отбирать посты с views > 1000")
    print("   - Фильтровать по длине текста")
    
    print("\n4. 📝 РАЗБИТЬ НА БАТЧИ:")
    print("   - Обрабатывать по 25-30 постов за раз")
    print("   - Использовать несколько OpenAI вызовов")

if __name__ == "__main__":
    asyncio.run(test_ai_workflow_diagnosis()) 