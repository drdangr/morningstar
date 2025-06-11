import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Подключение к базе данных
DATABASE_URL = f"postgresql://postgres:{os.getenv('DB_PASSWORD')}@localhost:5432/digest_bot"
engine = create_engine(DATABASE_URL)

print("=== ДИАГНОСТИКА РАЗМЕРОВ ТАБЛИЦ ===")

with engine.connect() as conn:
    # 1. Общий размер всей базы данных
    result = conn.execute(text("""
        SELECT pg_size_pretty(pg_database_size('digest_bot'))
    """))
    total_db_size = result.fetchone()[0]
    print(f"1. Общий размер базы digest_bot: {total_db_size}")
    
    # 2. Размер таблицы posts_cache (в байтах)
    result = conn.execute(text("""
        SELECT pg_total_relation_size('posts_cache')
    """))
    posts_cache_bytes = result.fetchone()[0]
    print(f"2. Размер posts_cache (байты): {posts_cache_bytes}")
    
    # 3. Размер таблицы posts_cache (красиво)
    result = conn.execute(text("""
        SELECT pg_size_pretty(pg_total_relation_size('posts_cache'))
    """))
    posts_cache_pretty = result.fetchone()[0]
    print(f"3. Размер posts_cache (pretty): {posts_cache_pretty}")
    
    # 4. Количество записей в posts_cache
    result = conn.execute(text("""
        SELECT count(*) FROM posts_cache
    """))
    posts_count = result.fetchone()[0]
    print(f"4. Количество записей в posts_cache: {posts_count}")
    
    # 5. Размер данных в строках posts_cache
    result = conn.execute(text("""
        SELECT pg_size_pretty(sum(pg_column_size(posts_cache.*))::bigint) FROM posts_cache
    """))
    posts_data_size = result.fetchone()[0]
    print(f"5. Размер данных в строках posts_cache: {posts_data_size}")
    
    # 6. Все таблицы и их размеры
    result = conn.execute(text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """))
    
    print("\n6. Размеры всех таблиц:")
    for row in result:
        print(f"   {row[1]}: {row[2]} ({row[3]} bytes)")

print("\n=== ПАРСИНГ СТРОКИ posts_cache_pretty ===")
size_str = posts_cache_pretty
print(f"Исходная строка: '{size_str}'")

# Парсим как в функции get_filtered_data_size
if "GB" in size_str:
    size_mb = float(size_str.split(" ")[0]) * 1024
    print(f"Парсинг GB: {size_mb} MB")
elif "MB" in size_str:
    size_mb = float(size_str.split(" ")[0])
    print(f"Парсинг MB: {size_mb} MB")
elif "kB" in size_str:
    size_mb = float(size_str.split(" ")[0]) / 1024
    print(f"Парсинг kB: {size_mb} MB")
elif "bytes" in size_str:
    bytes_count = float(size_str.split(" ")[0])
    size_mb = bytes_count / (1024 * 1024)
    print(f"Парсинг bytes: {bytes_count} -> {size_mb} MB")
else:
    size_mb = 0.0
    print(f"Не удалось распарсить, используем 0.0 MB")

print(f"Итоговый размер: {round(size_mb, 2)} MB") 