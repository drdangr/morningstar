import requests
import json

def debug_batch_issue():
    """Диагностика проблемы с batch processing в N8N"""
    
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ BATCH WORKFLOW")
    print("=" * 50)
    
    # Проверяем что userbot отправляет правильные данные
    print("\n1. 📊 Анализ структуры данных из последнего дайджеста...")
    
    try:
        response = requests.get("http://localhost:8000/api/digests?limit=1")
        if response.status_code == 200:
            digests = response.json()
            if digests:
                latest = digests[0]
                print(f"🔍 Последний дайджест: {latest['digest_id']}")
                print(f"📈 Всего постов: {latest['total_posts']}")
                print(f"📊 Релевантных: {latest['relevant_posts']}")
                
                if latest['total_posts'] == 0:
                    print("🎯 ПОДТВЕРЖДЕНИЕ: Batch workflow не обработал посты")
                    print("❌ Проблема в N8N ноде Split Posts Into Batches")
            else:
                print("📝 Нет дайджестов для анализа")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n🔧 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
    print("1. **N8N Split Node Configuration:**")
    print("   - Batch Size: 30")
    print("   - Input Field: posts_for_ai")
    print("   - Reset node and reconfigure")
    
    print("\n2. **Структура данных должна быть:**")
    print("   {")
    print("     'posts_for_ai': [array of posts],")
    print("     'total_posts_for_ai': number,")
    print("     'dynamic_prompt': string")
    print("   }")
    
    print("\n3. **Если проблема в поле:**")
    print("   - Проверить что 'Prepare for AI' возвращает posts_for_ai")
    print("   - Убедиться что это массив, а не объект")
    
    print("\n🚨 СРОЧНЫЕ ДЕЙСТВИЯ:")
    print("1. В N8N нажать на Split Posts Into Batches node")
    print("2. Проверить Configuration → Input Field = 'posts_for_ai'")
    print("3. Если не помогло - пересоздать ноду Split In Batches")
    print("4. Переактивировать workflow")
    
    print("\n💡 АЛЬТЕРНАТИВА:")
    print("Если проблема не решается - можно временно:")
    print("- Увеличить maxTokens в OpenAI node до 4000")
    print("- Обработать все посты без батчей")
    print("- Потом вернуться к batch решению")

if __name__ == "__main__":
    debug_batch_issue() 