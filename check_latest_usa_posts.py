import requests
import json
from datetime import datetime, timedelta

# Получаем все дайджесты
response = requests.get('http://localhost:8000/api/digests')
digests = response.json()

print(f"Всего дайджестов: {len(digests)}")

# Ищем последние дайджесты с постами категории "США"
usa_found_digests = []

for digest in digests[-10:]:  # Проверяем последние 10
    digest_id = digest['digest_id']
    
    # Получаем детальные данные дайджеста
    detail_response = requests.get(f"http://localhost:8000/api/digests/{digest_id}/data")
    if detail_response.status_code == 200:
        digest_data = detail_response.json()
        
        # Ищем посты с категорией "США"
        usa_posts = []
        
        if 'channels' in digest_data:
            for channel in digest_data['channels']:
                if 'posts' in channel:
                    for post in channel['posts']:
                        if post.get('post_category') == 'США':
                            usa_posts.append({
                                'title': post.get('title', 'Без заголовка')[:80] + '...',
                                'channel': channel.get('title', 'Неизвестный канал'),
                                'date': post.get('date'),
                                'category': post.get('post_category'),
                                'ai_assigned': post.get('ai_assigned_category')
                            })
        
        if usa_posts:
            usa_found_digests.append({
                'digest_id': digest_id,
                'processed_at': digest.get('processed_at'),
                'usa_posts_count': len(usa_posts),
                'usa_posts': usa_posts
            })

print(f"\n🇺🇸 Найдено дайджестов с категорией 'США': {len(usa_found_digests)}")

if usa_found_digests:
    for digest_info in usa_found_digests[-3:]:  # Последние 3
        print(f"\n📊 Дайджест: {digest_info['digest_id']}")
        print(f"   Дата: {digest_info['processed_at']}")
        print(f"   Постов с категорией 'США': {digest_info['usa_posts_count']}")
        
        for i, post in enumerate(digest_info['usa_posts'], 1):
            print(f"   {i}. {post['title']}")
            print(f"      Канал: {post['channel']}")
            print(f"      Категория: {post['category']} | AI: {post['ai_assigned']}")
            print(f"      Дата: {post['date']}")
else:
    print("❌ Дайджестов с категорией 'США' не найдено в Backend API")

# Проверим также пользователя с подпиской на "США"
print(f"\n👤 Проверяем пользователей с подпиской на 'США':")
users_response = requests.get('http://localhost:8000/api/users')
if users_response.status_code == 200:
    users = users_response.json()
    for user in users:
        subscriptions_response = requests.get(f"http://localhost:8000/api/users/{user['telegram_id']}/subscriptions")
        if subscriptions_response.status_code == 200:
            subscriptions = subscriptions_response.json()
            usa_subscribed = any(sub['category_name'] == 'США' for sub in subscriptions)
            if usa_subscribed:
                print(f"   📱 Пользователь {user['first_name']} (ID: {user['telegram_id']}) подписан на 'США'")
                print(f"      Подписки: {[sub['category_name'] for sub in subscriptions]}") 