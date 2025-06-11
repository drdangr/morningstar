#!/usr/bin/env python3
"""
Создание пользователя digest_bot и базы данных в PostgreSQL
"""

from sqlalchemy import create_engine, text

def main():
    print("🔧 НАСТРОЙКА POSTGRESQL - СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ И БД")
    print("=" * 60)
    
    # Попробуем разные пароли для postgres
    passwords = ["password", "", "admin", "postgres", "root"]
    
    for pwd in passwords:
        postgres_url = f"postgresql://postgres:{pwd}@localhost:5432/postgres?sslmode=disable"
        print(f"🔍 Пробую пароль: {pwd if pwd else '(пустой)'}")
        
        try:
            engine = create_engine(postgres_url, echo=False, isolation_level="AUTOCOMMIT")
            
            with engine.connect() as conn:
                print("✅ Подключение к PostgreSQL как postgres успешно!")
                
                # Создаем пользователя digest_bot
                print("👤 Создаю пользователя digest_bot...")
                conn.execute(text("DROP USER IF EXISTS digest_bot CASCADE"))
                conn.execute(text("CREATE USER digest_bot WITH PASSWORD 'SecurePassword123!'"))
                
                # Создаем базу данных
                print("🗄️ Создаю базу данных digest_bot...")
                conn.execute(text("DROP DATABASE IF EXISTS digest_bot"))
                conn.execute(text("CREATE DATABASE digest_bot OWNER digest_bot"))
                conn.execute(text("GRANT ALL PRIVILEGES ON DATABASE digest_bot TO digest_bot"))
                
                print("🎉 POSTGRESQL НАСТРОЕН УСПЕШНО!")
                return
                
        except Exception as e:
            print(f"❌ Ошибка с паролем '{pwd}': {e}")
            continue
    
    print("❌ Не удалось подключиться ни с одним паролем")

if __name__ == "__main__":
    main()
