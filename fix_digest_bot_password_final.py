#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сброс пароля digest_bot
"""
import psycopg2

# Подключаемся как суперпользователь postgres
POSTGRES_PASSWORD = "Demiurg12@"  # Точно работает
NEW_DIGEST_BOT_PASSWORD = "Demiurg12@"  # Устанавливаем тот же пароль

print("🔧 СБРОС ПАРОЛЯ digest_bot")
print("=" * 40)

try:
    # Подключение под postgres
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres", 
        password=POSTGRES_PASSWORD,
        database="postgres"
    )
    
    cursor = conn.cursor()
    
    # Проверяем существование пользователя
    cursor.execute("SELECT usename FROM pg_user WHERE usename = 'digest_bot';")
    user_exists = cursor.fetchone()
    
    if user_exists:
        print("✅ Пользователь digest_bot существует")
        
        # Сбрасываем пароль
        print(f"🔄 Сбрасываем пароль digest_bot...")
        cursor.execute(f"ALTER USER digest_bot PASSWORD '{NEW_DIGEST_BOT_PASSWORD}';")
        
        print(f"✅ Пароль digest_bot изменен!")
        
    else:
        print("❌ Пользователь digest_bot НЕ СУЩЕСТВУЕТ!")
        print("🔄 Создаем пользователя digest_bot...")
        
        cursor.execute(f"""
            CREATE USER digest_bot 
            WITH PASSWORD '{NEW_DIGEST_BOT_PASSWORD}'
            CREATEDB;
        """)
        
        print("✅ Пользователь digest_bot создан!")
    
    # Даем права на базу digest_bot
    print("🔄 Даем права на базу digest_bot...")
    cursor.execute("GRANT ALL PRIVILEGES ON DATABASE digest_bot TO digest_bot;")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n🎉 УСПЕХ! Теперь digest_bot может подключиться с паролем: {NEW_DIGEST_BOT_PASSWORD}")
    
    # Тестируем новое подключение
    print(f"\n🔍 ТЕСТ НОВОГО ПОДКЛЮЧЕНИЯ:")
    test_conn = psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        user="digest_bot",
        password=NEW_DIGEST_BOT_PASSWORD,
        database="digest_bot"
    )
    
    test_cursor = test_conn.cursor()
    test_cursor.execute("SELECT current_user, current_database();")
    user, db = test_cursor.fetchone()
    
    print(f"✅ ПОДКЛЮЧЕНИЕ РАБОТАЕТ!")
    print(f"   Пользователь: {user}")
    print(f"   База данных: {db}")
    
    test_cursor.close()
    test_conn.close()
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    print(f"\n💡 Возможные причины:")
    print(f"  • Неверный пароль postgres: {POSTGRES_PASSWORD}")
    print(f"  • PostgreSQL не запущен") 
    print(f"  • Проблемы с pg_hba.conf") 