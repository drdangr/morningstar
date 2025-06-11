#!/usr/bin/env python3

import psycopg2
import sys
import os
from dotenv import load_dotenv

def check_digest_bot_database():
    """Проверяем базу digest_bot"""
    
    # Загружаем переменные из .env файла
    load_dotenv()
    password = os.getenv("DB_PASSWORD")
    
    if not password:
        print("❌ Пароль не найден в .env файле!")
        print("Добавьте DB_PASSWORD=ваш_пароль в .env файл")
        return False
    
    try:
        # Сначала проверим, существует ли база digest_bot
        print("🔍 Проверяем существование базы digest_bot...")
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',
            user='postgres',
            password=password
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'digest_bot';")
        digest_db_exists = cursor.fetchone()
        
        if digest_db_exists:
            print("✅ База данных digest_bot существует!")
        else:
            print("❌ База данных digest_bot НЕ существует")
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        
        # Теперь подключаемся к digest_bot
        print("🔄 Подключаемся к базе digest_bot...")
        conn = psycopg2.connect(
            host='localhost',
            database='digest_bot',
            user='postgres',
            password=password
        )
        cursor = conn.cursor()
        
        print("✅ Подключение к digest_bot успешно!")
        
        # Проверяем какие таблицы есть
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"\n📋 Найдено {len(tables)} таблиц в digest_bot:")
        for table in tables:
            print(f"  {table[0]}")
        
        # Проверяем количество данных в ключевых таблицах
        tables_to_check = ['categories', 'channels', 'posts_cache', 'users', 'digests']
        
        has_important_data = False
        
        print("\n=== ДАННЫЕ В ТАБЛИЦАХ ===")
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"📋 Таблица {table}: {count} записей")
                
                if count > 0:
                    has_important_data = True
                    
                    # Показываем примеры данных
                    if table == 'categories':
                        cursor.execute(f"SELECT id, category_name, description FROM {table} LIMIT 3;")
                        rows = cursor.fetchall()
                        for row in rows:
                            print(f"   📝 {row[0]}: {row[1]} - {row[2]}")
                    
                    elif table == 'channels':
                        cursor.execute(f"SELECT id, title, username, telegram_id FROM {table} LIMIT 3;")
                        rows = cursor.fetchall()
                        for row in rows:
                            print(f"   📺 {row[0]}: {row[1]} (@{row[2]}) - {row[3]}")
                    
                    elif table == 'posts_cache':
                        cursor.execute(f"SELECT COUNT(*), MIN(collected_at), MAX(collected_at) FROM {table};")
                        row = cursor.fetchone()
                        print(f"   📮 Посты от {row[1]} до {row[2]}")
                        
            except Exception as e:
                print(f"   ❌ Ошибка проверки таблицы {table}: {e}")
        
        # Проверяем структуру таблицы categories
        print("\n=== СТРУКТУРА ТАБЛИЦЫ CATEGORIES ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'categories' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[0]} - {col[1]} - Nullable: {col[2]} - Default: {col[3]}")
        
        cursor.close()
        conn.close()
        
        # Выводим рекомендацию
        print("\n" + "="*50)
        if has_important_data:
            print("🎯 РЕКОМЕНДАЦИЯ: В базе есть важные данные!")
            print("   Безопаснее ОБНОВИТЬ КОД под существующую структуру БД")
            print("\n📝 Нужно изменить в backend/main.py:")
            print("   - name → category_name в модели Category")
        else:
            print("💡 В базе нет важных данных")
            print("   Можно безопасно пересоздать таблицы с правильной структурой")
        
        return has_important_data
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    check_digest_bot_database() 