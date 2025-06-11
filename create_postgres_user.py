#!/usr/bin/env python3
"""
Создание пользователя digest_bot и базы данных в PostgreSQL
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_digest_bot_setup():
    print("🔧 Создание пользователя digest_bot и базы данных...")
    
    try:
        # Подключаемся к postgres с паролем Demiurg12@
        print("1️⃣ Подключение к PostgreSQL как postgres...")
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",  # Системная база
            user="postgres",      # Суперпользователь
            password="Demiurg12@" # Тот же пароль
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("   ✅ Подключение успешно!")
        
        # Проверяем/создаем пользователя digest_bot
        print("\n2️⃣ Проверяем пользователя digest_bot...")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'digest_bot'")
        if cursor.fetchone():
            print("   ✅ Пользователь digest_bot уже существует")
        else:
            print("   🔧 Создаем пользователя digest_bot...")
            cursor.execute("CREATE USER digest_bot WITH PASSWORD 'Demiurg12@'")
            cursor.execute("ALTER USER digest_bot CREATEDB")
            print("   ✅ Пользователь digest_bot создан")
        
        # Проверяем/создаем базу данных digest_bot
        print("\n3️⃣ Проверяем базу данных digest_bot...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'digest_bot'")
        if cursor.fetchone():
            print("   ✅ База данных digest_bot уже существует")
        else:
            print("   🔧 Создаем базу данных digest_bot...")
            cursor.execute("CREATE DATABASE digest_bot OWNER digest_bot")
            print("   ✅ База данных digest_bot создана")
        
        # Даем права
        print("\n4️⃣ Настраиваем права...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE digest_bot TO digest_bot")
        print("   ✅ Права настроены")
        
        cursor.close()
        conn.close()
        
        # Тестируем подключение к digest_bot
        print("\n5️⃣ Тестируем подключение к digest_bot...")
        test_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="digest_bot",
            user="digest_bot",
            password="Demiurg12@"
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT version()")
        version = test_cursor.fetchone()[0]
        print(f"   ✅ Подключение успешно: {version[:50]}...")
        test_cursor.close()
        test_conn.close()
        
        print("\n🎉 PostgreSQL настроен! digest_bot готов к использованию!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    create_digest_bot_setup() 