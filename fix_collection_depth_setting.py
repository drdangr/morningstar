import asyncio
import aiohttp
import json

async def fix_collection_depth_setting():
    """Исправление настройки COLLECTION_DEPTH_DAYS"""
    
    print("🔧 ИСПРАВЛЕНИЕ НАСТРОЙКИ COLLECTION_DEPTH_DAYS")
    print("=" * 50)
    
    backend_url = "http://localhost:8000"
    
    # Шаг 1: Получаем текущее значение
    print("\n1. 📋 Проверяем текущее значение...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/config/COLLECTION_DEPTH_DAYS") as response:
                if response.status == 200:
                    data = await response.json()
                    current_value = data.get('value')
                    print(f"🔍 Текущее значение: {current_value} дней")
                else:
                    print(f"❌ Ошибка получения настройки: {response.status}")
                    return
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return
    
    # Шаг 2: Получаем ID настройки для обновления
    print("\n2. 🔍 Ищем ID настройки...")
    
    setting_id = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/settings") as response:
                if response.status == 200:
                    settings = await response.json()
                    for setting in settings:
                        if setting['key'] == 'COLLECTION_DEPTH_DAYS':
                            setting_id = setting['id']
                            print(f"✅ Найден ID настройки: {setting_id}")
                            break
                    
                    if not setting_id:
                        print("❌ Настройка COLLECTION_DEPTH_DAYS не найдена!")
                        return
                else:
                    print(f"❌ Ошибка получения списка настроек: {response.status}")
                    return
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return
    
    # Шаг 3: Обновляем значение на 3 дня
    print("\n3. 🔧 Обновляем значение на 3 дня...")
    
    new_value = "3"
    update_data = {
        "value": new_value,
        "description": "Сколько дней назад собирать посты из каналов (исправлено)"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{backend_url}/api/settings/{setting_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    updated_setting = await response.json()
                    print(f"✅ Настройка обновлена!")
                    print(f"📊 Новое значение: {updated_setting['value']} дней")
                    print(f"📝 Описание: {updated_setting['description']}")
                else:
                    response_text = await response.text()
                    print(f"❌ Ошибка обновления: {response.status}")
                    print(f"📄 Ответ: {response_text}")
                    return
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return
    
    # Шаг 4: Проверяем результат
    print("\n4. ✅ Проверяем результат...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/api/config/COLLECTION_DEPTH_DAYS") as response:
                if response.status == 200:
                    data = await response.json()
                    final_value = data.get('value')
                    print(f"🎉 Итоговое значение: {final_value} дней")
                    
                    # Показываем эффект
                    collection_hours = int(final_value) * 24
                    print(f"⏰ В часах: {collection_hours} часов")
                    print(f"📊 Теперь будут собираться посты за последние {final_value} дня!")
                    
                else:
                    print(f"❌ Ошибка финальной проверки: {response.status}")
    except Exception as e:
        print(f"💥 Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("💡 Теперь userbot будет собирать посты за последние 3 дня")
    print("🔄 Перезапустите userbot для применения изменений")

async def main():
    await fix_collection_depth_setting()

if __name__ == "__main__":
    asyncio.run(main()) 