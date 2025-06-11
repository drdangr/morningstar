#!/usr/bin/env python3
"""
Диагностика структуры базы данных PostgreSQL
Проверяет соответствие реальной структуры таблиц моделям SQLAlchemy
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def get_db_connection():
    """Подключение к PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'digest_bot'),
        user=os.getenv('DB_USER', 'digest_bot'),
        password=os.getenv('DB_PASSWORD', 'SecurePassword123!')
    )

def get_table_structure(cursor, table_name):
    """Получает структуру таблицы"""
    cursor.execute("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table_name,))
    return cursor.fetchall()

def get_foreign_keys(cursor, table_name):
    """Получает внешние ключи таблицы"""
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_name = %s;
    """, (table_name,))
    return cursor.fetchall()

def check_table_exists(cursor, table_name):
    """Проверяет существование таблицы"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 ДИАГНОСТИКА СТРУКТУРЫ БАЗЫ ДАННЫХ")
        print("=" * 50)
        
        # Список важных таблиц
        tables_to_check = [
            'users',
            'user_subscriptions', 
            'categories',
            'channels',
            'channel_categories',
            'posts_cache',
            'digests',
            'system_settings'
        ]
        
        for table_name in tables_to_check:
            print(f"\n📋 ТАБЛИЦА: {table_name}")
            print("-" * 30)
            
            if not check_table_exists(cursor, table_name):
                print("❌ Таблица не существует!")
                continue
                
            # Структура таблицы
            columns = get_table_structure(cursor, table_name)
            print("📊 Столбцы:")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  • {col['column_name']}: {col['data_type']} {nullable}{default}")
            
            # Внешние ключи
            fkeys = get_foreign_keys(cursor, table_name)
            if fkeys:
                print("🔗 Внешние ключи:")
                for fk in fkeys:
                    print(f"  • {fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            
            # Подсчет записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📈 Записей в таблице: {count}")
        
        # СПЕЦИАЛЬНАЯ ПРОВЕРКА user_subscriptions
        print("\n🔍 ДЕТАЛЬНАЯ ПРОВЕРКА user_subscriptions")
        print("=" * 40)
        
        if check_table_exists(cursor, 'user_subscriptions'):
            # Проверяем структуру
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                ORDER BY ordinal_position;
            """)
            cols = cursor.fetchall()
            
            print("Реальная структура user_subscriptions:")
            for col in cols:
                print(f"  • {col['column_name']}: {col['data_type']}")
            
            # Проверяем наличие user_id
            user_id_exists = any(col['column_name'] == 'user_id' for col in cols)
            print(f"\nСтолбец user_id существует: {'✅ ДА' if user_id_exists else '❌ НЕТ'}")
            
            if not user_id_exists:
                print("🚨 ПРОБЛЕМА: Столбец user_id отсутствует!")
                print("Это объясняет ошибки при удалении категорий.")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Диагностика завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка при диагностике: {e}")

if __name__ == "__main__":
    main() 