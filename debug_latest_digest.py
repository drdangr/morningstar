#!/usr/bin/env python3

import requests
import json
import sys

def debug_latest_digest():
    """Детальная диагностика последнего дайджеста"""
    
    # Получаем последний дайджест
    try:
        response = requests.get('http://localhost:8000/api/digests?limit=1')
        response.raise_for_status()
        digests = response.json()
        
        if not digests:
            print("❌ Дайджестов не найдено")
            return
            
        latest_digest = digests[0]
        print(f"🔍 Последний дайджест: {latest_digest['digest_id']}")
        print(f"📅 Создан: {latest_digest['created_at']}")
        print(f"📊 Всего постов: {latest_digest['total_posts']}")
        print(f"🎯 Релевантных: {latest_digest['relevant_posts']}")
        print(f"📈 Средняя важность: {latest_digest.get('avg_importance', 'N/A')}")
        print(f"🚨 Средняя срочность: {latest_digest.get('avg_urgency', 'N/A')}")
        print(f"⭐ Средняя значимость: {latest_digest.get('avg_significance', 'N/A')}")
        print(f"🤖 Batch processing: {latest_digest.get('batch_processing_applied', 'N/A')}")
        print()
        
        # Получаем полные данные дайджеста
        digest_data_response = requests.get(f'http://localhost:8000/api/digests/{latest_digest["digest_id"]}/data')
        digest_data_response.raise_for_status()
        full_data = digest_data_response.json()
        
        print("📋 ДЕТАЛЬНЫЙ АНАЛИЗ ПОСТОВ:")
        print("=" * 50)
        
        channels = full_data.get('channels', [])
        total_ai_processed = 0
        total_with_categories = 0
        ai_analysis_examples = []
        
        for i, channel in enumerate(channels[:3]):  # Первые 3 канала
            print(f"\n📺 Канал {i+1}: {channel.get('title', 'Unknown')}")
            print(f"👤 Username: {channel.get('username', 'N/A')}")
            print(f"🏷️ Категории канала: {channel.get('categories', [])}")
            print(f"📰 Постов в дайджесте: {len(channel.get('posts', []))}")
            
            posts = channel.get('posts', [])
            for j, post in enumerate(posts[:2]):  # Первые 2 поста
                print(f"\n  📄 Пост {j+1}:")
                print(f"    📝 Заголовок: {post.get('title', 'N/A')[:100]}...")
                print(f"    🎯 AI важность: {post.get('ai_importance', 'N/A')}")
                print(f"    🚨 AI срочность: {post.get('ai_urgency', 'N/A')}")
                print(f"    ⭐ AI значимость: {post.get('ai_significance', 'N/A')}")
                print(f"    🏷️ Post категория: {post.get('post_category', 'N/A')}")
                print(f"    📋 AI summary: {post.get('summary', 'N/A')[:150]}...")
                print(f"    👁️ Просмотры: {post.get('views', 'N/A')}")
                
                # Статистика
                if post.get('ai_importance', 0) > 0:
                    total_ai_processed += 1
                if post.get('post_category') and post.get('post_category') != 'Unknown':
                    total_with_categories += 1
                    
                ai_analysis_examples.append({
                    'channel': channel.get('title'),
                    'ai_importance': post.get('ai_importance', 0),
                    'post_category': post.get('post_category', 'N/A'),
                    'summary': post.get('summary', 'N/A')[:100]
                })
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА AI ОБРАБОТКИ:")
        print(f"🤖 Постов с AI метриками: {total_ai_processed}")
        print(f"🏷️ Постов с категориями: {total_with_categories}")
        print(f"📈 Процент AI обработки: {(total_ai_processed/max(latest_digest['total_posts'], 1)*100):.1f}%")
        
        print(f"\n🔍 ПРИМЕРЫ AI АНАЛИЗА:")
        for example in ai_analysis_examples[:3]:
            print(f"  📺 {example['channel']}: важность={example['ai_importance']}, категория='{example['post_category']}', summary='{example['summary']}...'")
            
        # Проверяем наличие batch processing данных
        if full_data.get('batch_processing_applied'):
            print(f"\n🔄 BATCH PROCESSING DATA:")
            summary = full_data.get('summary', {})
            print(f"  📦 Батчей обработано: {summary.get('batches_processed', 'N/A')}")
            print(f"  📊 Исходных постов: {summary.get('original_posts', 'N/A')}")
            print(f"  🎯 Релевантных найдено: {summary.get('relevant_posts', 'N/A')}")
            print(f"  📈 Средние AI метрики: imp={summary.get('avg_importance', 'N/A'):.1f}, urg={summary.get('avg_urgency', 'N/A'):.1f}, sig={summary.get('avg_significance', 'N/A'):.1f}")
        
    except requests.RequestException as e:
        print(f"❌ Ошибка API: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    debug_latest_digest() 