#!/usr/bin/env python3
"""
Простая проверка подключения к PostgreSQL и структуры user_subscriptions
"""

from sqlalchemy import create_engine, text
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

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def main():
    try:
        print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К POSTGRESQL")
        print("=" * 50)
        print(f"Host: {DB_HOST}")
        print(f"Port: {DB_PORT}")
        print(f"Database: {DB_NAME}")
        print(f"User: {DB_USER}")
        
        engine = create_engine(DATABASE_URL, echo=False)
        
        with engine.connect() as conn:
            # Тестируем подключение
            result = conn.execute(text("SELECT 1 as test"))
            print(f"✅ Подключение успешно: {result.fetchone()}")
            
            # Проверяем существование таблицы user_subscriptions
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_subscriptions'
                )
            """))
            table_exists = result.fetchone()[0]
            print(f"📋 Таблица user_subscriptions существует: {'✅ ДА' if table_exists else '❌ НЕТ'}")
            
            if table_exists:
                # Получаем структуру таблицы
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'user_subscriptions' 
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                print("\n📊 СТРУКТУРА ТАБЛИЦЫ user_subscriptions:")
                for col in columns:
                    print(f"  • {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                
                # Проверяем наличие user_id
                user_id_exists = any(col[0] == 'user_id' for col in columns)
                print(f"\n🔍 Столбец user_id: {'✅ ЕСТЬ' if user_id_exists else '❌ ОТСУТСТВУЕТ'}")
                
                if not user_id_exists:
                    print("\n🚨 НАЙДЕНА ПРОБЛЕМА!")
                    print("SQLAlchemy модель ожидает столбец user_id, но его нет в базе.")
                    print("Это объясняет ошибки при удалении категорий.")
                    
                    # Проверяем что именно есть в таблице
                    result = conn.execute(text("SELECT COUNT(*) FROM user_subscriptions"))
                    count = result.fetchone()[0]
                    print(f"📈 Записей в таблице: {count}")
                    
                    if count > 0:
                        result = conn.execute(text("SELECT * FROM user_subscriptions LIMIT 3"))
                        rows = result.fetchall()
                        print("📋 Первые записи:")
                        for row in rows:
                            print(f"  • {row}")
            
            # Проверяем другие таблицы, связанные с проблемой
            for table in ['users', 'categories']:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.fetchone()[0]
                print(f"📋 Таблица {table} существует: {'✅ ДА' if exists else '❌ НЕТ'}")
                
                if exists:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    print(f"  📈 Записей: {count}")
        
        print("\n✅ Диагностика завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка при подключении: {e}")
        print("\n🔧 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
        print("1. Проверьте, запущен ли PostgreSQL")
        print("2. Проверьте настройки в .env файле")
        print("3. Убедитесь, что пользователь digest_bot существует")

if __name__ == "__main__":
    main() 