#!/usr/bin/env python3
"""
Тестирование N8N workflow с несколькими темами
"""

import json
import requests

# Тестовые посты для проверки фильтрации по нескольким темам
test_posts = [
    {
        "id": "test1",
        "text": "OpenAI выпустила новую версию GPT-5 с улучшенными возможностями программирования",
        "channel": "tech_news",
        "views": 1500
    },
    {
        "id": "test2", 
        "text": "В Туле открылся новый IT-парк для стартапов и технологических компаний",
        "channel": "tula_news",
        "views": 800
    },
    {
        "id": "test3",
        "text": "Сборная России по футболу победила Бразилию со счетом 3:1 в товарищеском матче",
        "channel": "sport_news", 
        "views": 2200
    },
    {
        "id": "test4",
        "text": "Новый ресторан McDonald's открылся в центре Нью-Йорка",
        "channel": "world_news",
        "views": 300
    },
    {
        "id": "test5",
        "text": "Тульский оружейный завод представил новую модель спортивного карабина",
        "channel": "tula_industry",
        "views": 650
    },
    {
        "id": "test6",
        "text": "Tesla анонсировала полностью автономные роботакси на базе ИИ",
        "channel": "auto_tech",
        "views": 1800
    }
]

# Имитация метаданных каналов с разными категориями
channels_metadata = {
    "tech_news": {
        "categories": [
            {"name": "Технологии", "is_active": True, "ai_prompt": "новости о IT, искусственном интеллекте, разработке"}
        ]
    },
    "tula_news": {
        "categories": [
            {"name": "Тула", "is_active": True, "ai_prompt": "новости в которых упоминается Тульская область или Тула"},
            {"name": "Технологии", "is_active": True, "ai_prompt": "новости о IT, искусственном интеллекте, разработке"}
        ]
    },
    "sport_news": {
        "categories": [
            {"name": "Спорт", "is_active": True, "ai_prompt": "спортивные новости и события"}
        ]
    },
    "world_news": {
        "categories": []
    },
    "tula_industry": {
        "categories": [
            {"name": "Тула", "is_active": True, "ai_prompt": "новости в которых упоминается Тульская область или Тула"}
        ]
    },
    "auto_tech": {
        "categories": [
            {"name": "Технологии", "is_active": True, "ai_prompt": "новости о IT, искусственном интеллекте, разработке"}
        ]
    }
}

# Подготовка данных для отправки в N8N webhook
webhook_data = {
    "posts": test_posts,
    "channels_metadata": channels_metadata,
    "collection_stats": {
        "total_posts": len(test_posts),
        "channels_count": len(channels_metadata),
        "collection_time": "2025-12-08T15:30:00Z"
    }
}

def test_workflow():
    """Тестирование workflow с несколькими темами"""
    
    print("🧪 Тестирование N8N workflow с несколькими темами...")
    print(f"📊 Тестовые данные: {len(test_posts)} постов, {len(channels_metadata)} каналов")
    
    # Показываем какие темы будут в промпте
    all_categories = set()
    for channel_meta in channels_metadata.values():
        for cat in channel_meta.get("categories", []):
            if cat.get("is_active"):
                all_categories.add(f"{cat['name']} ({cat['ai_prompt']})")
    
    print("\n🎯 Ожидаемые темы в промпте:")
    for topic in sorted(all_categories):
        print(f"  • {topic}")
    
    print("\n📝 Тестовые посты:")
    for post in test_posts:
        print(f"  {post['id']}: {post['text'][:60]}...")
    
    # Ожидаемые результаты
    print("\n💭 Ожидаемые результаты семантического анализа:")
    print("  test1 (OpenAI GPT-5) → Технологии ✅")
    print("  test2 (IT-парк в Туле) → Тула ✅ + Технологии ✅") 
    print("  test3 (футбол Россия-Бразилия) → Спорт ✅")
    print("  test4 (McDonald's в Нью-Йорке) → NULL ❌")
    print("  test5 (Тульский оружейный завод) → Тула ✅")
    print("  test6 (Tesla роботакси) → Технологии ✅")
    
    # Сохраняем данные для ручной отправки
    with open("test_multiple_topics_data.json", "w", encoding="utf-8") as f:
        json.dump(webhook_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Данные сохранены в test_multiple_topics_data.json")
    print("🚀 Для тестирования отправьте эти данные на N8N webhook:")
    print("   POST http://localhost:5678/webhook/telegram-posts")
    
    return webhook_data

if __name__ == "__main__":
    test_workflow() 