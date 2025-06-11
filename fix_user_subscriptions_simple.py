#!/usr/bin/env python3
"""
Простое исправление таблицы user_subscriptions через SQLite
"""

import sqlite3

def main():
    print("🔧 ИСПРАВЛЕНИЕ user_subscriptions В SQLITE")
    print("=" * 50)
    
    # Используем SQLite базу данных backend
    db_path = "backend/morningstar.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ Подключение к SQLite успешно")
        
        # Проверяем существование таблицы
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_subscriptions'
        """)
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Проверяем структуру таблицы
            cursor.execute("PRAGMA table_info(user_subscriptions)")
            columns = cursor.fetchall()
            print("🔍 Текущие колонки:")
            for col in columns:
                print(f"  • {col[1]}: {col[2]}")
            
            # Проверяем есть ли колонка user_id
            has_user_id = any(col[1] == 'user_id' for col in columns)
            
            if not has_user_id:
                print("❌ Колонка user_id отсутствует!")
                print("🔧 Пересоздаю таблицу с правильной структурой...")
                
                # Удаляем старую таблицу
                cursor.execute("DROP TABLE user_subscriptions")
                
                # Создаем правильную таблицу
                cursor.execute("""
                    CREATE TABLE user_subscriptions (
                        user_id INTEGER NOT NULL,
                        category_id INTEGER NOT NULL,
                        PRIMARY KEY (user_id, category_id)
                    )
                """)
                
                conn.commit()
                print("✅ Таблица пересоздана с правильной структурой")
            else:
                print("✅ Колонка user_id уже существует")
        else:
            print("📋 Создаю новую таблицу user_subscriptions...")
            cursor.execute("""
                CREATE TABLE user_subscriptions (
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, category_id)
                )
            """)
            conn.commit()
            print("✅ Таблица создана")
        
        # Проверяем финальную структуру
        cursor.execute("PRAGMA table_info(user_subscriptions)")
        columns = cursor.fetchall()
        print("\n✅ ФИНАЛЬНАЯ СТРУКТУРА:")
        for col in columns:
            print(f"  • {col[1]}: {col[2]} ({'NULL' if col[3] == 0 else 'NOT NULL'})")
        
        conn.close()
        
        print("\n🎉 SQLITE ИСПРАВЛЕН!")
        print("Теперь можно запускать backend для тестирования")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 