#!/usr/bin/env python3
"""
Диагностика PostgreSQL аутентификации
Тестируем разные пароли и пользователей
"""
import psycopg2
from urllib.parse import quote_plus

# Возможные пароли (из истории проекта)
POSSIBLE_PASSWORDS = [
    "Demiurg12@",           # Текущий из памяти
    "SecurePassword123!",   # Старый из backend/main.py  
    "password",             # Дефолтный
    "postgres",             # Стандартный
    "12345",                # Простой
    "",                     # Пустой
]

# Тестируемые пользователи
USERS = ["digest_bot", "postgres"]

def test_connection(user, password, database="postgres"):
    """Тестирует подключение к PostgreSQL"""
    try:
        # URL encoding для пароля
        encoded_password = quote_plus(password) if password else ""
        
        print(f"🔍 Тестируем: {user} / {'*' * len(password) if password else '(пустой)'} → {database}")
        
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user=user,
            password=password,
            database=database
        )
        
        # Тестовый запрос
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✅ УСПЕХ! {user}:{password} → {database}")
        print(f"   PostgreSQL версия: {version[:50]}...")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка: {str(e)}")
        return False
    except Exception as e:
        print(f"⚠️  Неожиданная ошибка: {str(e)}")
        return False

def main():
    print("🔧 ДИАГНОСТИКА POSTGRESQL АУТЕНТИФИКАЦИИ")
    print("=" * 50)
    
    success_combinations = []
    
    # Тестируем все комбинации
    for user in USERS:
        print(f"\n👤 ПОЛЬЗОВАТЕЛЬ: {user}")
        print("-" * 30)
        
        for password in POSSIBLE_PASSWORDS:
            if test_connection(user, password):
                success_combinations.append((user, password))
                
                # Если успешно с базовой БД, проверяем digest_bot БД
                if user == "postgres":
                    print(f"   🔍 Проверяем доступ к digest_bot БД...")
                    if test_connection(user, password, "digest_bot"):
                        print(f"   ✅ {user} имеет доступ к digest_bot!")
        
        print()
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ:")
    
    if success_combinations:
        print("✅ Успешные подключения:")
        for user, password in success_combinations:
            print(f"   • {user} : {password}")
            
        # Проверяем существование пользователя digest_bot
        print(f"\n🔍 Проверяем существование пользователя digest_bot...")
        for user, password in success_combinations:
            if user == "postgres":
                try_check_digest_bot_user(password)
                break
    else:
        print("❌ НЕТ УСПЕШНЫХ ПОДКЛЮЧЕНИЙ!")
        print("Проблема может быть в:")
        print("  • pg_hba.conf настройках")
        print("  • Службе PostgreSQL")
        print("  • Все пароли неверные")

def try_check_digest_bot_user(postgres_password):
    """Проверяет существование пользователя digest_bot через postgres суперпользователя"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password=postgres_password,
            database="postgres"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT usename FROM pg_user WHERE usename = 'digest_bot';")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Пользователь digest_bot СУЩЕСТВУЕТ")
            
            # Проверяем права
            cursor.execute("SELECT datname FROM pg_database WHERE datname = 'digest_bot';")
            db_result = cursor.fetchone()
            
            if db_result:
                print(f"✅ База данных digest_bot СУЩЕСТВУЕТ")
            else:
                print(f"❌ База данных digest_bot НЕ СУЩЕСТВУЕТ")
        else:
            print(f"❌ Пользователь digest_bot НЕ СУЩЕСТВУЕТ")
            print(f"💡 Нужно создать пользователя digest_bot")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки digest_bot: {e}")

if __name__ == "__main__":
    main() 