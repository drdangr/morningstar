#!/usr/bin/env python3
"""
Тестирование multi-tenant database migration
Запускает SQL миграции и проверяет результат
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time

# Добавляем путь к backend для импорта конфигурации
sys.path.append('../../backend')

def get_db_connection():
    """Получение подключения к PostgreSQL БД"""
    
    # Настройки для локальной PostgreSQL (из .env файла)
    config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'digest_bot',
        'user': 'digest_bot',
        'password': 'SecurePassword123!'
    }
    
    try:
        print(f"🔄 Попытка подключения к PostgreSQL ({config['host']}:{config['port']})...")
        conn = psycopg2.connect(**config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print(f"✅ Подключен к PostgreSQL БД digest_bot")
        return conn
        
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL БД: {e}")
        return None

def run_sql_file(conn, filename):
    """Выполнение SQL файла"""
    try:
        print(f"📄 Выполняю {filename}...")
        
        with open(filename, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        
        # Для главного файла миграции используем специальную обработку
        if filename == '000_run_all_migrations.sql':
            # Разделяем на блоки по echo командам
            sql_blocks = sql_content.split('\\echo')
            
            for i, block in enumerate(sql_blocks):
                if block.strip():
                    # Убираем echo команды и \\i команды (include)
                    clean_block = []
                    for line in block.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('\\i') and not line.startswith('\\echo'):
                            clean_block.append(line)
                    
                    if clean_block:
                        block_sql = '\n'.join(clean_block)
                        try:
                            cursor.execute(block_sql)
                            print(f"  ✅ Блок {i+1} выполнен успешно")
                        except Exception as block_error:
                            print(f"  ⚠️ Ошибка в блоке {i+1}: {block_error}")
        else:
            # Обычное выполнение для отдельных файлов
            cursor.execute(sql_content)
            
        cursor.close()
        print(f"✅ {filename} выполнен успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка выполнения {filename}: {e}")
        return False

def run_individual_migrations(conn):
    """Запуск отдельных migration файлов в правильном порядке"""
    migration_files = [
        '001_create_public_bots.sql',
        '002_create_bot_relationships.sql', 
        '003_create_posts_cache.sql',
        '004_create_processed_data.sql',
        '005_create_multitenant_users.sql',
        '006_create_llm_management.sql'
    ]
    
    success_count = 0
    for filename in migration_files:
        if run_sql_file(conn, filename):
            success_count += 1
        time.sleep(0.5)  # Небольшая пауза между миграциями
    
    return success_count, len(migration_files)

def check_migration_results(conn):
    """Проверка результатов миграции"""
    print("\n🔍 Проверка результатов миграции...")
    
    cursor = conn.cursor()
    
    # Проверка созданных таблиц
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('public_bots', 'bot_channels', 'bot_categories', 
                          'posts_cache', 'processed_data', 'bot_users', 
                          'user_subscriptions', 'llm_providers', 'llm_settings',
                          'billing_transactions')
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"📋 Созданные таблицы ({len(tables)}):")
    for table in tables:
        print(f"  ✅ {table[0]}")
    
    # Проверка партиций posts_cache
    cursor.execute("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'posts_cache_%'
        ORDER BY tablename
    """)
    
    partitions = cursor.fetchall()
    print(f"\n📅 Партиции posts_cache ({len(partitions)}):")
    for partition in partitions:
        print(f"  ✅ {partition[1]}")
    
    # Проверка партиций processed_data
    cursor.execute("""
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'processed_data_p%'
        ORDER BY tablename
    """)
    
    partitions = cursor.fetchall()
    print(f"\n🔀 Партиции processed_data ({len(partitions)}):")
    for partition in partitions:
        print(f"  ✅ {partition[1]}")
    
    # Проверка LLM провайдеров
    cursor.execute("SELECT provider_name, is_active FROM llm_providers ORDER BY provider_name")
    providers = cursor.fetchall()
    print(f"\n🤖 LLM провайдеры ({len(providers)}):")
    for provider in providers:
        status = "🟢" if provider[1] else "🔴"
        print(f"  {status} {provider[0]}")
    
    # Проверка default PublicBot
    cursor.execute("SELECT bot_name, status, default_language FROM public_bots")
    bots = cursor.fetchall()
    print(f"\n🤖 PublicBots ({len(bots)}):")
    for bot in bots:
        print(f"  🤖 {bot[0]} (status: {bot[1]}, language: {bot[2]})")
    
    # Проверка связей bot-channel
    cursor.execute("""
        SELECT pb.bot_name, COUNT(bc.channel_id) as channels_count
        FROM public_bots pb
        LEFT JOIN bot_channels bc ON pb.id = bc.public_bot_id
        GROUP BY pb.bot_name
    """)
    bot_channels = cursor.fetchall()
    print(f"\n🔗 Связи бот-канал:")
    for bot_channel in bot_channels:
        print(f"  🤖 {bot_channel[0]}: {bot_channel[1]} каналов")
    
    cursor.close()

def main():
    """Главная функция тестирования"""
    print("🚀 Начало тестирования Multi-tenant Database Migration")
    print("=" * 60)
    
    # Подключение к БД
    conn = get_db_connection()
    if not conn:
        print("❌ Не удалось подключиться к БД. Проверьте настройки.")
        return False
    
    print("✅ Подключение к PostgreSQL установлено")
    
    # Запуск индивидуальных миграций
    print("\n📦 Запуск migration файлов...")
    success_count, total_count = run_individual_migrations(conn)
    
    if success_count == total_count:
        print(f"✅ Все {total_count} миграций выполнены успешно!")
    else:
        print(f"⚠️ Выполнено {success_count} из {total_count} миграций")
    
    # Проверка результатов
    check_migration_results(conn)
    
    conn.close()
    print("\n🎉 Тестирование migration завершено!")
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 