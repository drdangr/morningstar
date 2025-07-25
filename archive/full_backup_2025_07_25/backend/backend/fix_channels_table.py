#!/usr/bin/env python3
"""
Исправление: Добавить колонку username в таблицу channels используя SQLAlchemy
"""

from main import engine, SessionLocal
from sqlalchemy import text

def fix_channels_table():
    """Добавить отсутствующую колонку username в таблицу channels"""
    
    print("🔧 Исправление таблицы channels...")
    
    try:
        db = SessionLocal()
        
        # Проверяем, существует ли колонка username
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'channels' AND column_name = 'username'
        """))
        
        if result.fetchone():
            print("✅ Колонка 'username' уже существует в таблице 'channels'")
        else:
            # Добавляем колонку username
            db.execute(text("""
                ALTER TABLE channels 
                ADD COLUMN username VARCHAR
            """))
            db.commit()
            print("✅ Колонка 'username' успешно добавлена в таблицу 'channels'")
        
        # Показываем структуру таблицы
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'channels' 
            ORDER BY ordinal_position
        """))
        
        print("\n📋 Текущая структура таблицы 'channels':")
        for row in result:
            column_name, data_type, is_nullable = row
            print(f"  - {column_name}: {data_type} {'(nullable)' if is_nullable == 'YES' else '(not null)'}")
        
        db.close()
        
        print("\n🎉 Исправление завершено!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении таблицы: {e}")
        return False

if __name__ == "__main__":
    fix_channels_table() 