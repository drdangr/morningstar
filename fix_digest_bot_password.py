#!/usr/bin/env python3
"""
Исправление пароля пользователя digest_bot в PostgreSQL
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_digest_bot_password():
    print("🔧 Исправление пароля digest_bot...")
    
    try:
        # Подключаемся как postgres
        print("1️⃣ Подключение как postgres...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="Demiurg12@"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("   ✅ Подключение успешно!")
        
        # Обновляем пароль digest_bot
        print("\n2️⃣ Обновляем пароль digest_bot...")
        cursor.execute("ALTER USER digest_bot PASSWORD 'Demiurg12@'")
        print("   ✅ Пароль обновлен!")
        
        # Даем дополнительные права
        print("\n3️⃣ Проверяем права digest_bot...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE digest_bot TO digest_bot")
        cursor.execute("ALTER USER digest_bot CREATEDB")
        cursor.execute("ALTER USER digest_bot CREATEROLE")
        print("   ✅ Права обновлены!")
        
        cursor.close()
        conn.close()
        
        # Тестируем подключение
        print("\n4️⃣ Тестируем подключение digest_bot...")
        test_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="digest_bot",
            user="digest_bot",
            password="Demiurg12@"
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT current_user, current_database()")
        user, db = test_cursor.fetchone()
        print(f"   ✅ Подключение успешно! Пользователь: {user}, База: {db}")
        test_cursor.close()
        test_conn.close()
        
        print("\n🎉 Пароль digest_bot исправлен! PostgreSQL готов!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    fix_digest_bot_password() 