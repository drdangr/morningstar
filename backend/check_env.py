#!/usr/bin/env python3
"""
Диагностический скрипт для проверки переменных окружения
и подключения к базе данных
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env в корне проекта
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)
print(f"📁 Читаем .env из: {os.path.abspath(env_path)}")

print("🔍 ДИАГНОСТИКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 50)

# Проверяем все DB переменные
db_vars = [
    "DB_HOST",
    "DB_PORT", 
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DATABASE_URL"
]

print("📋 Переменные базы данных:")
for var in db_vars:
    value = os.getenv(var, "НЕ НАЙДЕНА")
    # Скрываем пароль для безопасности
    if "PASSWORD" in var and value != "НЕ НАЙДЕНА":
        masked_value = "*" * len(value)
        print(f"  {var}: {masked_value}")
    else:
        print(f"  {var}: {value}")

print("\n🔗 Тестируем подключение к PostgreSQL:")

try:
    import psycopg2
    
    # Формируем строку подключения
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "digest_bot")
    user = os.getenv("DB_USER", "digest_bot")
    password = os.getenv("DB_PASSWORD", "SecurePassword123!")
    
    print(f"  Пытаемся подключиться к: {host}:{port}/{database} как {user}")
    
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    
    print(f"  ✅ УСПЕХ! PostgreSQL версия: {version[:50]}...")
    
    # Проверяем наличие наших таблиц
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('public_bots', 'posts_cache', 'processed_data')
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    print(f"  📋 Найдено multi-tenant таблиц: {len(tables)}")
    for table in tables:
        print(f"    ✅ {table[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"  ❌ ОШИБКА: {e}")

print("\n" + "=" * 50)
print("🎯 РЕКОМЕНДАЦИИ:")

host = os.getenv("DB_HOST", "НЕ НАЙДЕНА")
if host == "postgres":
    print("  ⚠️  DB_HOST=postgres (для Docker)")
    print("  🔧 Нужно: DB_HOST=localhost (для локального PostgreSQL)")
elif host == "localhost":
    print("  ✅ DB_HOST=localhost (правильно для локального PostgreSQL)")
else:
    print(f"  ❓ DB_HOST={host} (неожиданное значение)") 