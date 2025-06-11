#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ исправление структуры таблицы user_subscriptions
Исправляем раз и навсегда, без временных костылей
"""

from sqlalchemy import create_engine, text, MetaData
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройки как в backend/main.py
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "digest_bot")
DB_USER = os.getenv("DB_USER", "digest_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "SecurePassword123!")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

def main():
    print("🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ СТРУКТУРЫ БД")
    print("=" * 50)
    
    # Отладочная информация
    print(f"🔍 DEBUG: DB_HOST = {DB_HOST}")
    print(f"🔍 DEBUG: DB_PORT = {DB_PORT}")
    print(f"🔍 DEBUG: DB_NAME = {DB_NAME}")
    print(f"🔍 DEBUG: DB_USER = {DB_USER}")
    print(f"🔍 DEBUG: DB_PASSWORD = {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'NOT SET'}")
    print(f"🔍 DEBUG: DATABASE_URL = {DATABASE_URL}")
    print()
    
    try:
        # Принудительно используем TCP/IP соединение
        connect_args = {"host": DB_HOST, "port": int(DB_PORT)}
        engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
        
        with engine.connect() as conn:
            print("✅ Подключение к PostgreSQL успешно")
            
            # Проверяем существование таблицы user_subscriptions
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_subscriptions'
                )
            """))
            table_exists = result.fetchone()[0]
            
            if table_exists:
                print("🗑️ Удаляю старую таблицу user_subscriptions...")
                conn.execute(text("DROP TABLE IF EXISTS user_subscriptions CASCADE"))
                conn.commit()
                print("✅ Старая таблица удалена")
            
            # Создаем правильную таблицу
            print("📋 Создаю правильную таблицу user_subscriptions...")
            conn.execute(text("""
                CREATE TABLE user_subscriptions (
                    user_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, category_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                )
            """))
            conn.commit()
            print("✅ Правильная таблица создана")
            
            # Проверяем финальную структуру
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print("\n✅ ФИНАЛЬНАЯ СТРУКТУРА:")
            for col in columns:
                print(f"  • {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # Проверяем ограничения
            result = conn.execute(text("""
                SELECT conname, contype 
                FROM pg_constraint 
                WHERE conrelid = 'user_subscriptions'::regclass
            """))
            constraints = result.fetchall()
            
            print("\n🔗 Ограничения:")
            for constraint in constraints:
                constraint_type = {
                    'p': 'PRIMARY KEY',
                    'f': 'FOREIGN KEY'
                }.get(constraint[1], constraint[1])
                print(f"  • {constraint[0]}: {constraint_type}")
        
        print("\n🎉 ПРОБЛЕМА РЕШЕНА НАВСЕГДА!")
        print("Теперь можно запускать backend - все CRUD операции будут работать")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 