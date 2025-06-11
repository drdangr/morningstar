#!/usr/bin/env python3
"""
Скрипт для настройки PostgreSQL базы данных digest_bot
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def setup_postgres_database():
    load_dotenv()
    
    # Параметры подключения
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "digest_bot")
    DB_USER = os.getenv("DB_USER", "digest_bot")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "SecurePassword123!")
    
    print(f"🔧 Настройка PostgreSQL:")
    print(f"   База данных: {DB_NAME}")
    print(f"   Пользователь: {DB_USER}")
    print(f"   Хост: {DB_HOST}:{DB_PORT}")
    print()
    
    try:
        # Подключаемся к postgres базе (системная)
        print("1️⃣ Подключение к системной базе postgres...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",  # Системная база
            user="postgres",      # Суперпользователь
            password="postgres"   # Попробуем стандартный пароль
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("   ✅ Подключен к postgres")
        
        # Проверяем/создаем пользователя
        print(f"\n2️⃣ Проверяем пользователя {DB_USER}...")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (DB_USER,))
        if cursor.fetchone():
            print(f"   ✅ Пользователь {DB_USER} существует")
        else:
            print(f"   🔧 Создаем пользователя {DB_USER}...")
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD %s", (DB_PASSWORD,))
            print(f"   ✅ Пользователь {DB_USER} создан")
        
        # Проверяем/создаем базу данных
        print(f"\n3️⃣ Проверяем базу данных {DB_NAME}...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
        if cursor.fetchone():
            print(f"   ✅ База данных {DB_NAME} существует")
        else:
            print(f"   🔧 Создаем базу данных {DB_NAME}...")
            cursor.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER}")
            print(f"   ✅ База данных {DB_NAME} создана")
        
        # Даем права
        print(f"\n4️⃣ Настраиваем права для {DB_USER}...")
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        cursor.execute(f"ALTER USER {DB_USER} CREATEDB")
        print(f"   ✅ Права настроены")
        
        cursor.close()
        conn.close()
        
        # Проверяем подключение к целевой базе
        print(f"\n5️⃣ Тестируем подключение к {DB_NAME}...")
        test_conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT version()")
        version = test_cursor.fetchone()[0]
        print(f"   ✅ Подключение успешно: {version[:50]}...")
        test_cursor.close()
        test_conn.close()
        
        print("\n🎉 PostgreSQL настроен успешно!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка PostgreSQL: {e}")
        print(f"   Код ошибки: {e.pgcode}")
        return False
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        return False

if __name__ == "__main__":
    setup_postgres_database() 