#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import openai
import json
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

def test_openai_direct():
    """Тестируем прямое обращение к OpenAI API"""
    print("🤖 ТЕСТ ПРЯМОГО ОБРАЩЕНИЯ К OPENAI API")
    print("=" * 50)
    
    # Проверяем API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY не найден в .env!")
        return False
    
    print(f"🔑 API ключ найден: {api_key[:8]}...{api_key[-4:]}")
    
    # Настраиваем клиент
    client = openai.OpenAI(api_key=api_key)
    
    # Тестовые категории
    categories = ['AI и нейросети', 'Технологии', 'Война', 'Культура', 'Наука']
    topics_str = ', '.join(categories)
    
    # Тестовый промпт (как в N8N)
    prompt = f"""Отфильтруй посты по темам: {topics_str}.

Правило: summary = "NULL" если текст поста НЕ имеет отношения НИ К ОДНОЙ из перечисленных тем.

Возвращай JSON: {{"results": [{{"id": "post_id", "summary": "резюме или NULL", "importance": 8, "urgency": 6, "significance": 7, "category": "Точное название темы"}}]}}

ВАЖНО: category должно быть одним из: {topics_str} или "NULL"

Анализируй по СМЫСЛУ."""

    # Тестовые посты
    test_posts = [
        {
            "id": "test_1",
            "text": "OpenAI выпустила новую версию GPT-4o с улучшенной обработкой изображений",
            "channel": "Tech News",
            "views": 1000,
            "date": "2025-06-10",
            "url": "https://t.me/test/1"
        },
        {
            "id": "test_2", 
            "text": "Украинские дроны атаковали военную базу в России, есть жертвы",
            "channel": "War News",
            "views": 5000,
            "date": "2025-06-10",
            "url": "https://t.me/test/2"
        }
    ]
    
    print(f"\n📝 ТЕСТИРУЕМ ПРОМПТ:")
    print("-" * 30)
    print(prompt)
    print("-" * 30)
    
    print(f"\n📄 ТЕСТОВЫЕ ПОСТЫ:")
    for post in test_posts:
        print(f"   {post['id']}: {post['text'][:50]}...")
    
    try:
        print(f"\n🔄 Отправляю запрос к OpenAI...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Проанализируй эти посты:\n\n{json.dumps(test_posts, ensure_ascii=False)}"}
            ],
            max_tokens=6000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        print(f"✅ Ответ получен!")
        print(f"📊 Использовано токенов: {response.usage.total_tokens}")
        
        # Парсим ответ
        content = response.choices[0].message.content
        print(f"\n📋 RAW ОТВЕТ:")
        print("-" * 30)
        print(content)
        print("-" * 30)
        
        # Пытаемся распарсить JSON
        try:
            parsed = json.loads(content)
            results = parsed.get('results', [])
            
            print(f"\n✅ JSON успешно распарсен!")
            print(f"📊 Найдено результатов: {len(results)}")
            
            for i, result in enumerate(results):
                print(f"\n📄 Результат {i+1}:")
                print(f"   ID: {result.get('id')}")
                print(f"   Summary: {result.get('summary')}")
                print(f"   Category: {result.get('category')}")
                print(f"   Importance: {result.get('importance')}")
                print(f"   Urgency: {result.get('urgency')}")
                print(f"   Significance: {result.get('significance')}")
                
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка OpenAI API: {e}")
        return False

def main():
    success = test_openai_direct()
    
    print(f"\n🎯 РЕЗУЛЬТАТ ТЕСТА:")
    if success:
        print("✅ OpenAI API работает корректно!")
        print("💡 Проблема может быть в N8N workflow или парсинге ответов")
    else:
        print("❌ Проблема с OpenAI API!")
        print("💡 Проверьте API ключ, лимиты, или настройки")

if __name__ == "__main__":
    main() 