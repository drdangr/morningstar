#!/usr/bin/env python3
"""
Тестовый скрипт для Stage 3 - AI Processing & Topic-based Filtering
Использует РЕАЛЬНУЮ структуру данных как от userbot в Stage 2
"""

import requests
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

def test_ai_workflow():
    """Тестирует AI workflow с реальной структурой данных"""
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'MorningStarUserbot/1.0',
        'Authorization': 'Bearer bWLIbaQtoha0sm58OQVHeVSwHZNTszAXJK7ma9vmbEE'
    }
    
    print("🧪 Тестирование AI Workflow с реальной структурой данных...")
    print(f"📍 URL: {WEBHOOK_URL}")
    print(f"📊 Отправляем {len(real_format_data['posts'])} постов из {len(real_format_data['collection_stats']['channels_processed'])} каналов")
    
    try:
        # Отправляем данные НАПРЯМУЮ без обертки "body"
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=real_format_data,  # Отправляем напрямую, как userbot
            timeout=30
        )
        
        print(f"📤 Status Code: {response.status_code}")
        print(f"📤 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook вызван успешно!")
            print("🔍 Проверьте логи N8N для деталей обработки")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")

if __name__ == "__main__":
    test_ai_workflow() 