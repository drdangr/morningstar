#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def check_latest_digest_details():
    """Детальная проверка последнего дайджеста"""
    print("🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА ПОСЛЕДНЕГО ДАЙДЖЕСТА")
    print("=" * 60)
    
    try:
        # Получаем последний дайджест
        response = requests.get('http://localhost:8000/api/digests?limit=1')
        if response.status_code == 200:
            digests = response.json()
            if digests:
                latest = digests[0]
                digest_id = latest['digest_id']
                
                print(f"📄 Дайджест ID: {digest_id}")
                print(f"📊 Исходных постов: {latest.get('original_posts', 'N/A')}")
                print(f"🎯 Релевантных: {latest['relevant_posts']}")
                print(f"📦 Обработано каналов: {latest['channels_processed']}")
                print(f"📈 Avg importance: {latest['avg_importance']}")
                
                # Получаем полные данные дайджеста
                data_response = requests.get(f'http://localhost:8000/api/digests/{digest_id}/data')
                if data_response.status_code == 200:
                    digest_data = data_response.json()
                    
                    print(f"\n📋 ПОЛНЫЕ ДАННЫЕ ДАЙДЖЕСТА:")
                    print(f"   Версия: {digest_data.get('relevance_parsing_version', 'Unknown')}")
                    print(f"   Батчевая обработка: {digest_data.get('batch_processing_applied', False)}")
                    
                    # Проверяем AI статистику
                    ai_stats = digest_data.get('ai_analysis_stats', {})
                    if ai_stats:
                        print(f"\n🤖 AI СТАТИСТИКА:")
                        print(f"   Всего проанализировано: {ai_stats.get('total_analyzed', 0)}")
                        print(f"   Релевантных найдено: {ai_stats.get('relevant_posts', 0)}")
                        print(f"   Батчей обработано: {ai_stats.get('batches_processed', 0)}")
                        print(f"   Avg importance: {ai_stats.get('avg_importance', 0)}")
                        print(f"   Avg urgency: {ai_stats.get('avg_urgency', 0)}")
                        print(f"   Avg significance: {ai_stats.get('avg_significance', 0)}")
                    
                    # Проверяем обработанные каналы
                    processed_channels = digest_data.get('processed_channels', {})
                    print(f"\n📺 ОБРАБОТАННЫЕ КАНАЛЫ ({len(processed_channels)}):")
                    
                    for channel_key, channel_data in processed_channels.items():
                        title = channel_data.get('channel_title', 'Unknown')
                        total_posts = channel_data.get('all_processed_posts', 0)
                        relevant_posts = channel_data.get('relevant_posts', 0)
                        ai_processed = channel_data.get('ai_processed', False)
                        
                        print(f"   📺 {title}:")
                        print(f"      Всего постов: {total_posts}")
                        print(f"      Релевантных: {relevant_posts}")
                        print(f"      AI обработка: {ai_processed}")
                        
                        # Показываем несколько постов для анализа
                        posts = channel_data.get('posts', [])
                        if posts:
                            print(f"      📝 Примеры постов:")
                            for i, post in enumerate(posts[:2]):
                                summary = post.get('ai_summary', 'No summary')
                                category = post.get('post_category', 'No category')
                                importance = post.get('ai_importance', 0)
                                print(f"         {i+1}. Category: {category}, Importance: {importance}")
                                print(f"            Summary: {summary[:100]}...")
                
                else:
                    print(f"❌ Не удалось получить данные дайджеста: {data_response.status_code}")
                    
                return True
            else:
                print("❌ Дайджесты не найдены")
                return False
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    print("🚀 ДИАГНОСТИКА N8N WORKFLOW РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    success = check_latest_digest_details()
    
    if success:
        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Проверьте логи N8N workflow для OpenAI node")
        print("2. Убедитесь что данные правильно передаются в OpenAI")
        print("3. Проверьте API ключ OpenAI в N8N")
        print("4. Проверьте настройки OpenAI node (JSON output, model, etc.)")
    else:
        print(f"\n❌ Не удалось получить детальную информацию")

if __name__ == "__main__":
    main() 