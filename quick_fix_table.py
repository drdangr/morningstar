#!/usr/bin/env python3
"""
Быстрое исправление через SQLAlchemy
Использует те же настройки что и backend
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из корня проекта
load_dotenv("../.env")

# Настройки как в main.py
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "digest_bot")
DB_USER = os.getenv("DB_USER", "digest_bot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "SecurePassword123!")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def main():
    print("🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ user_subscriptions")
    print("=" * 50)
    print(f"Подключение: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as conn:
            print("✅ Подключение успешно")
            
            # Проверяем текущую структуру
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            if columns:
                print("\n📊 Текущие столбцы:")
                for col in columns:
                    print(f"  • {col[0]}: {col[1]}")
            
            # Удаляем и пересоздаем таблицу
            print("\n🗑️ Удаление старой таблицы...")
            conn.execute(text("DROP TABLE IF EXISTS user_subscriptions CASCADE"))
            
            print("📋 Создание новой таблицы...")
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
            
            # Финальная проверка
            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'user_subscriptions' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            print("\n✅ НОВАЯ СТРУКТУРА:")
            for col in columns:
                print(f"  • {col[0]}: {col[1]}")
            
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("Можно запускать backend")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 