#!/usr/bin/env python3
"""
СРОЧНОЕ исправление структуры таблицы user_subscriptions
Выполняется пока backend остановлен
"""

import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def main():
    print("🔧 СРОЧНОЕ ИСПРАВЛЕНИЕ ТАБЛИЦЫ user_subscriptions")
    print("=" * 60)
    
    try:
        # Подключение с настройками из .env
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'digest_bot'),
            user=os.getenv('DB_USER', 'digest_bot'),
            password=os.getenv('DB_PASSWORD')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Подключение к PostgreSQL успешно")
        
        # Проверяем текущую структуру
        print("\n📊 Проверка текущей структуры...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'user_subscriptions' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        if columns:
            print("Текущие столбцы:")
            for col in columns:
                print(f"  • {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        else:
            print("❌ Таблица user_subscriptions не найдена")
        
        # Пересоздаем таблицу с правильной структурой
        print("\n🗑️ Удаление старой таблицы...")
        cursor.execute("DROP TABLE IF EXISTS user_subscriptions CASCADE")
        print("✅ Старая таблица удалена")
        
        print("\n📋 Создание новой таблицы...")
        cursor.execute("""
            CREATE TABLE user_subscriptions (
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, category_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        print("✅ Новая таблица создана")
        
        # Проверяем финальную структуру
        print("\n✅ ФИНАЛЬНАЯ ПРОВЕРКА:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'user_subscriptions' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  • {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # Проверяем ограничения
        cursor.execute("""
            SELECT conname, contype 
            FROM pg_constraint 
            WHERE conrelid = 'user_subscriptions'::regclass
        """)
        constraints = cursor.fetchall()
        
        print("\n🔗 Ограничения:")
        for constraint in constraints:
            constraint_type = {
                'p': 'PRIMARY KEY',
                'f': 'FOREIGN KEY', 
                'u': 'UNIQUE',
                'c': 'CHECK'
            }.get(constraint[1], constraint[1])
            print(f"  • {constraint[0]}: {constraint_type}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("Теперь можно запускать backend")
        print("Структура таблицы user_subscriptions исправлена")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Проверьте настройки подключения в .env файле")

if __name__ == "__main__":
    main() 