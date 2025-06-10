#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Диагностика батчевого workflow - почему посты "исчезают"
"""

import json
import requests
from datetime import datetime, timezone

# Проверяем последний дайджест с подробной диагностикой
def check_latest_digest():
    """Проверяем последний дайджест и анализируем структуру данных"""
    print("🔍 ДИАГНОСТИКА ПОСЛЕДНЕГО ДАЙДЖЕСТА:")
    print("=" * 60)
    
    try:
        # Получаем последние дайджесты
        response = requests.get("http://localhost:8000/api/digests?limit=1")
        if response.status_code != 200:
            print(f"❌ Ошибка API: {response.status_code}")
            return
            
        digests = response.json()
        if not digests:
            print("❌ Нет дайджестов в системе")
            return
            
        latest_digest = digests[0]
        digest_id = latest_digest['digest_id']
        print(f"📄 Последний дайджест: {digest_id}")
        
        # Получаем полные данные дайджеста
        detail_response = requests.get(f"http://localhost:8000/api/digests/{digest_id}/data")
        if detail_response.status_code != 200:
            print(f"❌ Ошибка получения данных: {detail_response.status_code}")
            return
            
        full_data = detail_response.json()
        
        # Анализируем структуру
        print("\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего каналов: {len(full_data.get('channels', []))}")
        print(f"   Всего постов: {full_data.get('total_posts', 0)}")
        print(f"   Батчевая обработка: {full_data.get('batch_processing_applied', False)}")
        
        summary = full_data.get('summary', {})
        print(f"   Обработано каналов: {summary.get('channels_processed', 0)}")
        print(f"   Оригинальных постов: {summary.get('original_posts', 0)}")
        print(f"   Релевантных постов: {summary.get('relevant_posts', 0)}")
        print(f"   Батчей обработано: {summary.get('batches_processed', 0)}")
        
        # Анализируем каналы
        print("\n📺 ДЕТАЛИЗАЦИЯ ПО КАНАЛАМ:")
        for channel in full_data.get('channels', []):
            print(f"   📺 {channel.get('title', 'Unknown')}")
            print(f"      Username: {channel.get('username', 'N/A')}")
            print(f"      Категории: {channel.get('categories', [])}")
            print(f"      Постов: {channel.get('posts_count', 0)}")
            print(f"      Постов в массиве: {len(channel.get('posts', []))}")
            
            # Анализируем структуру постов
            posts = channel.get('posts', [])
            if posts:
                print(f"      📝 Пример поста:")
                sample_post = posts[0]
                print(f"         Title: {sample_post.get('title', 'N/A')[:50]}...")
                print(f"         URL: {sample_post.get('url', 'N/A')}")
                print(f"         AI важность: {sample_post.get('ai_importance', 'N/A')}")
                print(f"         AI срочность: {sample_post.get('ai_urgency', 'N/A')}")
                print(f"         AI значимость: {sample_post.get('ai_significance', 'N/A')}")
                print(f"         Категория поста: {sample_post.get('post_category', 'N/A')}")
                print(f"         Summary: {sample_post.get('summary', 'N/A')[:50]}...")
            else:
                print(f"      ❌ ПРОБЛЕМА: Массив постов пуст!")
            print()
        
        return full_data
        
    except Exception as e:
        print(f"❌ Ошибка диагностики: {e}")
        return None

def analyze_batch_processing_issue(data):
    """Анализируем возможные проблемы в батчевой обработке"""
    if not data:
        return
        
    print("\n🔍 АНАЛИЗ ПРОБЛЕМ БАТЧЕВОЙ ОБРАБОТКИ:")
    print("=" * 60)
    
    # 1. Проверяем соотношение исходных и финальных постов
    original_posts = data.get('summary', {}).get('original_posts', 0)
    relevant_posts = data.get('summary', {}).get('relevant_posts', 0)
    total_posts = data.get('total_posts', 0)
    
    print(f"📊 ПОТЕРЯ ДАННЫХ:")
    print(f"   Исходных постов: {original_posts}")
    print(f"   Релевантных постов: {relevant_posts}")
    print(f"   Финальных постов: {total_posts}")
    
    if original_posts > 0 and relevant_posts == 0:
        print("   ❌ ПРОБЛЕМА: ВСЕ ПОСТЫ ПОТЕРЯНЫ НА ЭТАПЕ AI АНАЛИЗА")
        print("   💡 Возможные причины:")
        print("      1. AI возвращает все посты как 'NULL' (нерелевантные)")
        print("      2. Проблема парсинга результатов AI в 'Process Batch Results'")
        print("      3. Неправильное сопоставление ID постов и AI результатов")
        print("      4. Ошибка в логике фильтрации в 'Merge Batch Results'")
    elif relevant_posts > 0 and total_posts == 0:
        print("   ❌ ПРОБЛЕМА: ПОСТЫ ПОТЕРЯНЫ НА ЭТАПЕ PREPARE DIGEST")
        print("   💡 Возможные причины:")
        print("      1. Ошибка в ноде 'Prepare Digest'")
        print("      2. Проблема доступа к processed_channels")
    
    # 2. Проверяем структуру каналов
    channels = data.get('channels', [])
    empty_channels = [ch for ch in channels if ch.get('posts_count', 0) == 0]
    
    print(f"\n📺 АНАЛИЗ КАНАЛОВ:")
    print(f"   Всего каналов: {len(channels)}")
    print(f"   Пустых каналов: {len(empty_channels)}")
    
    if len(empty_channels) == len(channels) and len(channels) > 0:
        print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: ВСЕ КАНАЛЫ ПУСТЫЕ")
        print("   💡 Это указывает на проблему в ноде 'Merge Batch Results'")
    
    # 3. Анализируем метрики AI
    avg_importance = data.get('summary', {}).get('avg_importance', 0)
    avg_urgency = data.get('summary', {}).get('avg_urgency', 0)
    avg_significance = data.get('summary', {}).get('avg_significance', 0)
    
    print(f"\n🤖 AI МЕТРИКИ:")
    print(f"   Средняя важность: {avg_importance}")
    print(f"   Средняя срочность: {avg_urgency}")
    print(f"   Средняя значимость: {avg_significance}")
    
    if avg_importance == 0 and avg_urgency == 0 and avg_significance == 0:
        print("   ❌ ПРОБЛЕМА: AI НЕ ВЕРНУЛ МЕТРИКИ")
        print("   💡 Это может означать проблему в 'Process Batch Results'")

def suggest_fixes():
    """Предлагаем варианты исправления"""
    print("\n🔧 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
    print("=" * 60)
    print("1. 🔍 ПРОВЕРИТЬ НОДУ 'Process Batch Results':")
    print("   - Проверить парсинг OpenAI ответа")
    print("   - Убедиться что AI результаты извлекаются корректно")
    print("   - Проверить структуру batch_results")
    print()
    print("2. 🔍 ПРОВЕРИТЬ НОДУ 'Merge Batch Results':")
    print("   - Проверить логику allAIAnalysis.find(item => item.id == post.id)")
    print("   - Убедиться что ID постов и AI результатов совпадают")
    print("   - Проверить условие isRelevant = analysis && analysis.summary !== 'NULL'")
    print()
    print("3. 🔍 ПРОВЕРИТЬ НОДУ 'Prepare Digest':")
    print("   - Проверить доступ к processedData.processed_channels")
    print("   - Убедиться что каналы и посты корректно переносятся")
    print()
    print("4. 🧪 ДОБАВИТЬ ОТЛАДКУ:")
    print("   - Добавить console.log в каждую ноду для отслеживания данных")
    print("   - Проверить количество AI результатов на каждом этапе")

if __name__ == "__main__":
    print("🚀 ЗАПУСК ДИАГНОСТИКИ БАТЧЕВОГО WORKFLOW")
    print("=" * 60)
    
    # Диагностика последнего дайджеста
    latest_data = check_latest_digest()
    
    # Анализ проблем
    analyze_batch_processing_issue(latest_data)
    
    # Рекомендации
    suggest_fixes()
    
    print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА") 