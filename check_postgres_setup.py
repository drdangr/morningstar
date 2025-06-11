#!/usr/bin/env python3
"""
Проверка настройки PostgreSQL: существует ли пользователь digest_bot и база digest_bot
"""

import psycopg2
import os
from dotenv import load_dotenv

def check_postgres_setup():
    load_dotenv()
    
    print("🔍 Проверка настройки PostgreSQL...")
    
    # Пробуем разные варианты подключения к системной базе
    admin_configs = [
        {"user": "postgres", "password": "postgres", "database": "postgres"},
        {"user": "postgres", "password": "", "database": "postgres"},
        {"user": "postgres", "password": "admin", "database": "postgres"},
        {"user": "postgres", "password": "password", "database": "postgres"},
    ]
    
    conn = None
    for config in admin_configs:
        try:
            print(f"Пробуем подключиться как {config['user']}...")
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database=config['database'],
                user=config['user'],
                password=config['password']
            )
            print(f"✅ Подключение как {config['user']} успешно!")
            break
        except psycopg2.Error as e:
            print(f"❌ {config['user']}: {e}")
            continue
    
    if not conn:
        print("❌ Не удалось подключиться к PostgreSQL ни одним способом")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Проверяем пользователя digest_bot
        print("\n🔍 Проверяем пользователя digest_bot...")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'digest_bot'")
        user_exists = cursor.fetchone() is not None
        print(f"Пользователь digest_bot: {'✅ существует' if user_exists else '❌ не найден'}")
        
        # Проверяем базу digest_bot
        print("🔍 Проверяем базу данных digest_bot...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'digest_bot'")
        db_exists = cursor.fetchone() is not None
        print(f"База digest_bot: {'✅ существует' if db_exists else '❌ не найдена'}")
        
        if user_exists and db_exists:
            print("\n🎉 PostgreSQL настроен правильно!")
            
            # Тестируем подключение к digest_bot
            print("🔍 Тестируем подключение к digest_bot...")
            try:
                test_conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="digest_bot",
                    user="digest_bot",
                    password="Demiurg12@"
                )
                print("✅ Подключение к digest_bot успешно!")
                test_conn.close()
                return True
            except psycopg2.Error as e:
                print(f"❌ Ошибка подключения к digest_bot: {e}")
                return False
        else:
            print(f"\n⚠️ Нужно создать:")
            if not user_exists:
                print("  - Пользователя digest_bot")
            if not db_exists:
                print("  - База данных digest_bot")
            return False
            
    except psycopg2.Error as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_postgres_setup() 