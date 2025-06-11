#!/usr/bin/env python3
"""
Быстрый тест подключения с исправленными параметрами
"""
import psycopg2
from urllib.parse import quote_plus

# Параметры как в Backend
DB_HOST = "127.0.0.1"  # IPv4
DB_PORT = "5432"
DB_NAME = "digest_bot"
DB_USER = "digest_bot"
DB_PASSWORD = "Demiurg12@"

print("🔍 ТЕСТ ПОДКЛЮЧЕНИЯ К POSTGRESQL")
print("=" * 40)
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")  
print(f"Database: {DB_NAME}")
print(f"User: {DB_USER}")
print(f"Password: {'*' * len(DB_PASSWORD)}")

try:
    # URL encoding
    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"\nURL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    # Прямое подключение
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT current_database(), current_user, version();")
    db_name, user, version = cursor.fetchone()
    
    print(f"\n✅ ПОДКЛЮЧЕНИЕ УСПЕШНОЕ!")
    print(f"   База данных: {db_name}")
    print(f"   Пользователь: {user}")
    print(f"   Версия: {version[:50]}...")
    
    cursor.close()
    conn.close()
    
    print(f"\n🎉 Backend должен подключиться с этими параметрами!")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    print(f"\n💡 Нужно проверить:")
    print(f"  • Пароль digest_bot")  
    print(f"  • Права доступа")
    print(f"  • pg_hba.conf") 