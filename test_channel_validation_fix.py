import requests
import json

def test_channel_validation():
    """Тестирование API валидации каналов"""
    
    print("🔍 Тестирование валидации канала @GPTMainNew...")
    
    # Тест 1: @GPTMainNew
    test_data = {"channel_input": "@GPTMainNew"}
    
    try:
        response = requests.post(
            "http://localhost:8000/api/channels/validate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print("Ответ API:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            print("✅ Канал найден!")
            print(f"Название: {result['data']['title']}")
            print(f"Username: {result['data']['username']}")
            print(f"Telegram ID: {result['data']['telegram_id']}")
        else:
            print(f"❌ Ошибка: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    print("\n" + "="*50)
    
    # Тест 2: Другие варианты написания
    test_cases = [
        "@gptmainnew",  # в нижнем регистре
        "GPTMainNew",   # без @
        "gptmainnew",   # без @ в нижнем регистре
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Тестирую: {test_case}")
        try:
            response = requests.post(
                "http://localhost:8000/api/channels/validate",
                json={"channel_input": test_case},
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            if result.get('success'):
                print(f"✅ Найден: {result['data']['title']} ({result['data']['username']})")
            else:
                print(f"❌ Ошибка: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    # Тест 3: Проверим известный рабочий канал для сравнения
    print(f"\n🔍 Тестирую известный канал @durov для сравнения...")
    try:
        response = requests.post(
            "http://localhost:8000/api/channels/validate",
            json={"channel_input": "@durov"},
            headers={"Content-Type": "application/json"}
        )
        
        result = response.json()
        if result.get('success'):
            print(f"✅ @durov найден: {result['data']['title']}")
        else:
            print(f"❌ Даже @durov не работает: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Ошибка с @durov: {e}")

if __name__ == "__main__":
    test_channel_validation() 