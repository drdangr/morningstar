#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def check_active_topics():
    """Проверяем активные категории в системе"""
    print("🔍 ПРОВЕРКА АКТИВНЫХ КАТЕГОРИЙ В СИСТЕМЕ")
    print("=" * 50)
    
    # Пробуем разные endpoints
    endpoints_to_try = [
        'http://localhost:8000/api/topics',
        'http://localhost:8000/api/categories'
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"🔗 Проверяем: {endpoint}")
            response = requests.get(endpoint)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                topics = response.json()
                active_topics = [topic for topic in topics if topic.get('is_active', False)]
                
                print(f"📊 Всего категорий: {len(topics)}")
                print(f"🎯 Активных категорий: {len(active_topics)}")
                print("\n🏷️ АКТИВНЫЕ КАТЕГОРИИ:")
                
                for topic in active_topics:
                    name = topic.get('name', 'Unknown')
                    description = topic.get('description', 'Нет описания')
                    print(f"   • {name}: {description}")
                
                return active_topics
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Исключение: {e}")
    
    print("❌ НИ ОДИН ENDPOINT НЕ РАБОТАЕТ!")
    return []

def check_channels_metadata():
    """Проверяем метаданные каналов"""
    print("\n🔍 ПРОВЕРКА МЕТАДАННЫХ КАНАЛОВ")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:8000/api/channels?active_only=true')
        if response.status_code == 200:
            channels = response.json()
            print(f"📺 Активных каналов: {len(channels)}")
            
            for channel in channels:
                name = channel.get('title', 'Unknown')
                username = channel.get('username', 'N/A')
                categories = channel.get('categories', [])
                
                print(f"   📺 {name} (@{username})")
                print(f"      🏷️ Категории: {[cat.get('name') for cat in categories if cat.get('is_active')]}")
                
            return channels
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return []

def simulate_ai_prompt():
    """Симулируем формирование AI промпта"""
    print("\n🤖 СИМУЛЯЦИЯ AI ПРОМПТА")
    print("=" * 50)
    
    active_topics = check_active_topics()
    
    if not active_topics:
        print("❌ НЕТ АКТИВНЫХ КАТЕГОРИЙ - ЭТО ПРОБЛЕМА!")
        return None
    
    # Формируем промпт как в workflow
    topics_description = []
    for topic in active_topics:
        name = topic.get('name', '')
        description = topic.get('description', name)
        topics_description.append(f"{name} ({description})")
    
    topics_str = ', '.join(topics_description)
    categories_list = [topic.get('name') for topic in active_topics]
    
    prompt = f"""Отфильтруй посты по темам: {topics_str}.

Правило: summary = "NULL" если текст поста НЕ имеет отношения НИ К ОДНОЙ из перечисленных тем.

Возвращай JSON: {{"results": [{{"id": "post_id", "summary": "резюме или NULL", "importance": 8, "urgency": 6, "significance": 7, "category": "Точное название темы"}}]}}

ВАЖНО: category должно быть одним из: {', '.join(categories_list)} или "NULL"

Анализируй по СМЫСЛУ."""
    
    print("📝 СФОРМИРОВАННЫЙ ПРОМПТ:")
    print("-" * 30)
    print(prompt)
    print("-" * 30)
    
    return prompt

def main():
    print("🚀 ДИАГНОСТИКА AI PROCESSING ПРОБЛЕМ")
    print("=" * 60)
    
    # Проверяем категории
    active_topics = check_active_topics()
    
    # Проверяем каналы
    channels = check_channels_metadata()
    
    # Симулируем промпт
    prompt = simulate_ai_prompt() if active_topics else None
    
    print("\n🔧 АНАЛИЗ ПРОБЛЕМ:")
    print("=" * 50)
    
    if not active_topics:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет активных категорий!")
        print("   💡 Решение: Исправить API endpoint для категорий")
        print("   💡 Либо использовать категории из каналов")
    
    if not channels:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет активных каналов!")
        print("   💡 Решение: Активировать каналы в админ-панели")
    
    if not prompt and active_topics:
        print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Невозможно сформировать AI промпт!")
    
    # СОЗДАЕМ WORKAROUND - используем категории из каналов
    if not active_topics and channels:
        print("\n🔧 WORKAROUND: Собираем категории из каналов")
        print("=" * 50)
        
        all_categories = set()
        for channel in channels:
            categories = channel.get('categories', [])
            for cat in categories:
                if cat.get('is_active'):
                    all_categories.add(cat.get('name'))
        
        print(f"🏷️ Найденные категории из каналов: {list(all_categories)}")
        
        if all_categories:
            topics_str = ', '.join(all_categories)
            
            workaround_prompt = f"""Отфильтруй посты по темам: {topics_str}.

Правило: summary = "NULL" если текст поста НЕ имеет отношения НИ К ОДНОЙ из перечисленных тем.

Возвращай JSON: {{"results": [{{"id": "post_id", "summary": "резюме или NULL", "importance": 8, "urgency": 6, "significance": 7, "category": "Точное название темы"}}]}}

ВАЖНО: category должно быть одним из: {topics_str} или "NULL"

Анализируй по СМЫСЛУ."""
            
            print("\n📝 WORKAROUND ПРОМПТ:")
            print("-" * 30)
            print(workaround_prompt)
            print("-" * 30)
    
    print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    main() 