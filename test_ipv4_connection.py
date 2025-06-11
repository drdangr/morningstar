#!/usr/bin/env python3
"""
Тестирование подключения к PostgreSQL через IPv4 vs IPv6
"""

import psycopg2

def test_connection_types():
    print("🔍 Тестирование типов подключения к PostgreSQL...")
    
    # Тест IPv4
    print("\n1️⃣ Тест IPv4 (127.0.0.1)...")
    try:
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5432,
            database='digest_bot',
            user='digest_bot',
            password='Demiurg12@'
        )
        print('   ✅ IPv4 (127.0.0.1): подключение успешно!')
        cursor = conn.cursor()
        cursor.execute("SELECT current_user, current_database()")
        user, db = cursor.fetchone()
        print(f'   👤 Пользователь: {user}, База: {db}')
        cursor.close()
        conn.close()
        return '127.0.0.1'
    except Exception as e:
        print(f'   ❌ IPv4 (127.0.0.1): {e}')
    
    # Тест IPv6/localhost
    print("\n2️⃣ Тест localhost (IPv6)...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='digest_bot',
            user='digest_bot',
            password='Demiurg12@'
        )
        print('   ✅ localhost: подключение успешно!')
        cursor = conn.cursor()
        cursor.execute("SELECT current_user, current_database()")
        user, db = cursor.fetchone()
        print(f'   👤 Пользователь: {user}, База: {db}')
        cursor.close()
        conn.close()
        return 'localhost'
    except Exception as e:
        print(f'   ❌ localhost: {e}')
    
    print("\n❌ Оба типа подключения не работают!")
    return None

if __name__ == "__main__":
    working_host = test_connection_types()
    if working_host:
        print(f"\n🎉 Рабочий хост: {working_host}")
        print(f"💡 Нужно изменить DB_HOST в .env на: {working_host}")
    else:
        print("\n⚠️ Проблема с настройками PostgreSQL") 