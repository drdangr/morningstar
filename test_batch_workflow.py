import requests
import json

def test_batch_workflow():
    """Тестирование batch workflow для решения проблемы OpenAI перегрузки"""
    
    print("🔄 ТЕСТИРОВАНИЕ BATCH WORKFLOW v7.3")
    print("=" * 60)
    
    # Проверяем Backend API
    print("\n1. 📋 Проверяем Backend API...")
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("✅ Backend API работает")
        else:
            print(f"❌ Backend API недоступен: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к Backend API: {e}")
        return
    
    # Проверяем N8N
    print("\n2. 🔄 Проверяем N8N...")
    try:
        # Проверяем доступность N8N
        response = requests.get("http://localhost:5678/rest/login")
        if response.status_code in [200, 401]:  # 401 тоже означает что N8N работает
            print("✅ N8N доступен")
        else:
            print(f"❌ N8N недоступен: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения к N8N: {e}")
        return
        
    print("\n3. 📊 Проверяем количество постов в последнем дайджесте...")
    try:
        response = requests.get("http://localhost:8000/api/digests?limit=1")
        if response.status_code == 200:
            digests = response.json()
            if digests:
                latest = digests[0]
                print(f"🔍 Последний дайджест: {latest['digest_id']}")
                print(f"📈 Всего постов: {latest['total_posts']}")
                print(f"📊 Релевантных: {latest['relevant_posts']}")
                print(f"⏰ Время: {latest['processed_at']}")
                
                if latest['total_posts'] == 0:
                    print("🎯 ПРОБЛЕМА ПОДТВЕРЖДЕНА: OpenAI не обработал посты")
                    print("🔧 РЕШЕНИЕ: Используем batch workflow v7.3")
                else:
                    print(f"✅ Посты обрабатываются нормально ({latest['total_posts']} постов)")
            else:
                print("📝 Дайджестов нет, нужно запустить сбор")
        else:
            print(f"❌ Ошибка получения дайджестов: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n4. 🚀 ИНСТРУКЦИИ ПО АКТИВАЦИИ BATCH WORKFLOW:")
    print("   1. Открыть N8N в браузере: http://localhost:5678")
    print("   2. Импортировать новый workflow:")
    print("      - Copy/paste содержимое файла:")
    print("        n8n/workflows/telegram_digest_workflow_v7_3_with_batches.json")
    print("   3. Деактивировать старый workflow (telegram_digest_workflow_v7_3_compact)")
    print("   4. Активировать новый workflow (telegram_digest_workflow_v7_3_with_batches)")
    print("   5. Запустить userbot для тестирования")
    
    print("\n🎯 КЛЮЧЕВЫЕ УЛУЧШЕНИЯ BATCH WORKFLOW:")
    print("   ✅ Разбивка постов на батчи по 30 штук")
    print("   ✅ Автоматические циклы обработки в N8N")
    print("   ✅ Сборка результатов всех батчей")  
    print("   ✅ Предотвращение перегрузки OpenAI API")
    print("   ✅ Сохранение всей функциональности v7.3")
    
    print("\n📊 АРХИТЕКТУРА BATCH WORKFLOW:")
    print("   Prepare for AI → Split In Batches (30) → OpenAI API → Process Batch → Merge Results")
    print("                         ↑                                    ↓")
    print("                         └─────────── LOOP ──────────────────┘")

if __name__ == "__main__":
    test_batch_workflow() 