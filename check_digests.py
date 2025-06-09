import requests
import json

# Получаем все дайджесты
response = requests.get('http://localhost:8000/api/digests')
digests = response.json()

print(f"Всего дайджестов: {len(digests)}")

# Найдем дайджесты с реальными названиями (не debug/test)
real_digests = [d for d in digests if not any(word in d['digest_id'].lower() for word in ['debug', 'test', 'simple'])]

print(f"Реальных дайджестов: {len(real_digests)}")
print("\nПоследние 3 реальных дайджеста:")

# Проверяем последние реальные дайджесты
for digest in real_digests[-3:]:
    print(f"\n🔍 Дайджест ID: {digest['digest_id']}")
    print(f"Дата: {digest.get('processed_at', 'Не указана')}")
    print(f"Всего постов: {digest.get('total_posts', 0)}")
    print(f"Релевантных: {digest.get('relevant_posts', 0)}")
    
    # Получаем детальные данные дайджеста
    detail_response = requests.get(f"http://localhost:8000/api/digests/{digest['digest_id']}/data")
    if detail_response.status_code == 200:
        digest_data = detail_response.json()
        
        # Ищем посты с категорией "США"
        usa_posts = []
        all_categories = set()
        all_posts_info = []
        
        if 'channels' in digest_data:
            for channel in digest_data['channels']:
                if 'posts' in channel:
                    for post in channel['posts']:
                        post_category = post.get('post_category', 'Не указана')
                        all_categories.add(post_category)
                        
                        all_posts_info.append({
                            'title': post.get('title', 'Без заголовка')[:50] + '...',
                            'channel': channel.get('name', 'Неизвестный канал'),
                            'category': post_category,
                            'ai_assigned_category': post.get('ai_assigned_category', 'Нет')
                        })
                        
                        if post_category == 'США':
                            usa_posts.append(all_posts_info[-1])
        
        if usa_posts:
            print(f"  ✅ Найдены посты с категорией США: {len(usa_posts)}")
            for post in usa_posts:
                print(f"    - {post['title']}")
                print(f"      Канал: {post['channel']}, AI категория: {post['ai_assigned_category']}")
        else:
            print("  ❌ Постов с категорией 'США' не найдено")
            
        print(f"  📊 Все категории в дайджесте: {', '.join(sorted(all_categories))}")
        
        # Покажем первые несколько постов для понимания структуры
        if all_posts_info:
            print(f"  📰 Примеры постов (первые 3):")
            for i, post in enumerate(all_posts_info[:3]):
                print(f"    {i+1}. {post['title']}")
                print(f"       Категория: '{post['category']}' | AI: '{post['ai_assigned_category']}'")

# Проверим также какие каналы активны
print(f"\n🔍 Проверяем активные каналы:")
channels_response = requests.get('http://localhost:8000/api/channels?active_only=true')
if channels_response.status_code == 200:
    channels = channels_response.json()
    for channel in channels:
        topics = [t['name'] for t in channel.get('topics', [])]
        print(f"  📺 {channel['title']} (@{channel.get('username', 'unknown')})")
        print(f"     Категории: {', '.join(topics)}") 