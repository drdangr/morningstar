#!/usr/bin/env python3
"""
Полная миграция: Исправление структуры таблицы channels
"""

from main import engine, SessionLocal
from sqlalchemy import text

def fix_channels_schema():
    """Полная миграция структуры таблицы channels"""
    
    print("🔧 Полное исправление структуры таблицы channels...")
    
    try:
        db = SessionLocal()
        
        # Получаем текущую структуру таблицы
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'channels' 
            ORDER BY ordinal_position
        """))
        
        current_columns = {row[0]: row for row in result}
        print(f"\n📋 Найдено колонок: {len(current_columns)}")
        for col_name in current_columns.keys():
            print(f"  - {col_name}")
        
        # Список необходимых колонок согласно модели SQLAlchemy
        required_columns = {
            'id': 'INTEGER NOT NULL',
            'telegram_id': 'BIGINT NOT NULL',
            'username': 'VARCHAR',
            'title': 'VARCHAR NOT NULL',  # Это поле отсутствует!
            'description': 'TEXT',
            'is_active': 'BOOLEAN DEFAULT TRUE',
            'last_parsed': 'TIMESTAMP',
            'error_count': 'INTEGER DEFAULT 0',
            'created_at': 'TIMESTAMP DEFAULT NOW()',
            'updated_at': 'TIMESTAMP DEFAULT NOW()'
        }
        
        print(f"\n🎯 Требуется колонок: {len(required_columns)}")
        
        # Добавляем недостающие колонки
        migrations = []
        
        if 'title' not in current_columns:
            migrations.append("ADD COLUMN title VARCHAR NOT NULL DEFAULT 'Unknown Channel'")
            
        if 'description' not in current_columns:
            migrations.append("ADD COLUMN description TEXT")
            
        if 'last_parsed' not in current_columns:
            migrations.append("ADD COLUMN last_parsed TIMESTAMP")
            
        if 'error_count' not in current_columns:
            migrations.append("ADD COLUMN error_count INTEGER DEFAULT 0")
        
        # Если channel_name существует, переименуем в title
        if 'channel_name' in current_columns and 'title' not in current_columns:
            migrations.append("RENAME COLUMN channel_name TO title")
        
        # Выполняем миграции
        if migrations:
            print(f"\n🔄 Выполняем {len(migrations)} изменений...")
            
            for i, migration in enumerate(migrations, 1):
                print(f"  {i}. {migration}")
                try:
                    db.execute(text(f"ALTER TABLE channels {migration}"))
                    db.commit()
                    print(f"     ✅ Выполнено")
                except Exception as e:
                    print(f"     ❌ Ошибка: {e}")
                    db.rollback()
        else:
            print("\n✅ Все необходимые колонки уже существуют")
        
        # Проверяем финальную структуру
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'channels' 
            ORDER BY ordinal_position
        """))
        
        print(f"\n📋 Финальная структура таблицы 'channels':")
        for row in result:
            column_name, data_type, is_nullable, default = row
            nullable_str = '(nullable)' if is_nullable == 'YES' else '(not null)'
            default_str = f' DEFAULT {default}' if default else ''
            print(f"  - {column_name}: {data_type} {nullable_str}{default_str}")
        
        # Проверяем данные в таблице
        result = db.execute(text("SELECT COUNT(*) FROM channels"))
        count = result.scalar()
        print(f"\n📊 Записей в таблице: {count}")
        
        if count > 0:
            result = db.execute(text("SELECT id, telegram_id, title, username FROM channels LIMIT 3"))
            print("📝 Примеры записей:")
            for row in result:
                print(f"  - ID: {row[0]}, Telegram: {row[1]}, Title: {row[2]}, Username: {row[3]}")
        
        db.close()
        
        print("\n🎉 Миграция завершена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        return False

if __name__ == "__main__":
    fix_channels_schema() 