#!/usr/bin/env python3
"""
Пересоздание таблиц SQLAlchemy с правильной структурой
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.main import Base, engine, SessionLocal
from sqlalchemy import text

def main():
    print("🔧 ПЕРЕСОЗДАНИЕ ТАБЛИЦ SQLALCHEMY")
    print("=" * 50)
    
    try:
        # Создаем все таблицы заново
        print("📋 Создание таблиц...")
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы/обновлены")
        
        # Проверяем структуру user_subscriptions
        with engine.connect() as conn:
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
            
            # Проверяем наличие нужных столбцов
            column_names = [col[0] for col in columns]
            user_id_exists = 'user_id' in column_names
            category_id_exists = 'category_id' in column_names
            
            print(f"\n🔍 Проверка столбцов:")
            print(f"  • user_id: {'✅ ЕСТЬ' if user_id_exists else '❌ ОТСУТСТВУЕТ'}")
            print(f"  • category_id: {'✅ ЕСТЬ' if category_id_exists else '❌ ОТСУТСТВУЕТ'}")
            
            if user_id_exists and category_id_exists:
                print("\n🎉 СТРУКТУРА ТАБЛИЦЫ ИСПРАВЛЕНА!")
                print("Теперь можно перезапустить backend")
            else:
                print("\n❌ ПРОБЛЕМА НЕ РЕШЕНА")
                print("Возможно, нужно вручную создать таблицу")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 