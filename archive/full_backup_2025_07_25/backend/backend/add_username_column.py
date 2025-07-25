#!/usr/bin/env python3
"""
Миграция: Добавить колонку username в таблицу channels
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def add_username_column():
    """Добавить колонку username в таблицу channels"""
    
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="digest_bot",
            user="postgres",
            password="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже колонка username
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'channels' AND column_name = 'username'
        """)
        
        if cursor.fetchone():
            print("✅ Колонка 'username' уже существует в таблице 'channels'")
            return
        
        # Добавляем колонку username
        cursor.execute("""
            ALTER TABLE channels 
            ADD COLUMN username VARCHAR;
        """)
        
        print("✅ Колонка 'username' успешно добавлена в таблицу 'channels'")
        
        # Проверяем структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'channels' 
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Структура таблицы 'channels':")
        for row in cursor.fetchall():
            column_name, data_type, is_nullable = row
            print(f"  - {column_name}: {data_type} {'(nullable)' if is_nullable == 'YES' else '(not null)'}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении колонки: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Добавление колонки username в таблицу channels...")
    add_username_column() 