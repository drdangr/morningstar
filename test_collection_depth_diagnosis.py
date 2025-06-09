import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

async def test_backend_api_config():
    """Тестирование получения настроек из Backend API"""
    
    print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ СБОРА НОВОСТЕЙ >1 ДНЯ")
    print("=" * 60)
    
    backend_url = "http://localhost:8000"
    
    # Тест 1: Проверяем настройку COLLECTION_DEPTH_DAYS
    print("\n1. 📋 Проверяем настройку COLLECTION_DEPTH_DAYS...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/config/COLLECTION_DEPTH_DAYS") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ COLLECTION_DEPTH_DAYS: {data}")
                    collection_days = data.get('value', 3)
                    print(f"📊 Значение: {collection_days} дней")
                    
                    # Проверяем конвертацию в часы
                    collection_hours = int(collection_days) * 24
                    print(f"⏰ В часах: {collection_hours} часов")
                    
                    # Проверяем временную метку
                    time_limit = datetime.now() - timedelta(hours=collection_hours)
                    print(f"📅 Временная граница: {time_limit}")
                    print(f"🕐 Текущее время: {datetime.now()}")
                    print(f"📊 Разница: {(datetime.now() - time_limit).total_seconds() / 3600:.1f} часов")
                    
                else:
                    print(f"❌ Backend API вернул статус: {response.status}")
                    response_text = await response.text()
                    print(f"📄 Ответ: {response_text}")
                    
    except Exception as e:
        print(f"💥 Ошибка при запросе Backend API: {e}")
    
    # Тест 2: Проверяем все настройки системы
    print("\n2. 📋 Проверяем все настройки системы...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/settings?category=system") as response:
                if response.status == 200:
                    settings = await response.json()
                    print(f"✅ Найдено настроек системы: {len(settings)}")
                    
                    for setting in settings:
                        if setting['key'] in ['COLLECTION_DEPTH_DAYS', 'MAX_POSTS_PER_CHANNEL']:
                            print(f"🔧 {setting['key']}: {setting['value']} ({setting['value_type']})")
                            print(f"   📝 {setting.get('description', 'Нет описания')}")
                else:
                    print(f"❌ Backend API settings вернул статус: {response.status}")
                    
    except Exception as e:
        print(f"💥 Ошибка при запросе настроек: {e}")
    
    # Тест 3: Проверяем доступность Backend API
    print("\n3. 🌐 Проверяем доступность Backend API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"✅ Backend API здоров: {health}")
                else:
                    print(f"⚠️ Backend API health check: {response.status}")
                    
    except Exception as e:
        print(f"💥 Backend API недоступен: {e}")
    
    # Тест 4: Симуляция логики userbot
    print("\n4. 🤖 Симуляция логики userbot...")
    
    try:
        collection_depth_days = 3  # По умолчанию
        
        # Получаем значение из API (как в userbot)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/config/COLLECTION_DEPTH_DAYS") as response:
                if response.status == 200:
                    data = await response.json()
                    collection_depth_days = data.get('value', 3)
        
        # Конвертируем как в userbot
        collection_hours = int(collection_depth_days) * 24
        time_limit = datetime.now() - timedelta(hours=collection_hours)
        
        print(f"📊 Итоговые настройки userbot:")
        print(f"   📅 Дни сбора: {collection_depth_days}")
        print(f"   ⏰ Часы сбора: {collection_hours}")
        print(f"   📅 Временная граница: {time_limit}")
        
        # Проверяем разные сценарии
        test_scenarios = [
            ("1 день назад", 1),
            ("2 дня назад", 2), 
            ("3 дня назад", 3),
            ("5 дней назад", 5),
            ("7 дней назад", 7)
        ]
        
        print(f"\n📊 Тестирование фильтрации постов:")
        for scenario_name, days_ago in test_scenarios:
            test_date = datetime.now() - timedelta(days=days_ago)
            would_pass = test_date >= time_limit
            status = "✅ ПРОЙДЕТ" if would_pass else "❌ ОТФИЛЬТРУЕТСЯ"
            print(f"   {scenario_name}: {test_date.strftime('%Y-%m-%d %H:%M')} → {status}")
            
    except Exception as e:
        print(f"💥 Ошибка в симуляции: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("1. Проверьте, что Backend API запущен и доступен")
    print("2. Убедитесь, что настройка COLLECTION_DEPTH_DAYS существует в БД")
    print("3. Проверьте логи userbot при сборе постов")
    print("4. Если настройка >3 дней, посты старше будут отфильтрованы")

async def main():
    await test_backend_api_config()

if __name__ == "__main__":
    asyncio.run(main()) 