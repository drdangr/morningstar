#!/usr/bin/env python3
"""
Тест подключения к PostgreSQL с параметрами Backend
"""

import os
from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine, text

def test_postgres_connection():
    # Загружаем переменные
    load_dotenv()
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "digest_bot")
    DB_USER = os.getenv("DB_USER", "digest_bot") 
    DB_PASSWORD = os.getenv("DB_PASSWORD", "SecurePassword123!")
    
    print(f"🔍 Тестируем подключение к PostgreSQL:")
    print(f"   Host: {DB_HOST}")
    print(f"   Port: {DB_PORT}")
    print(f"   Database: {DB_NAME}")
    print(f"   User: {DB_USER}")
    print(f"   Password: {'*' * len(DB_PASSWORD)}")
    print()
    
    # Тест 1: Прямое подключение psycopg2
    try:
        print("1️⃣ Тест psycopg2...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ psycopg2: {version[:50]}...")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"   ❌ psycopg2 ошибка: {e}")
    
    # Тест 2: SQLAlchemy подключение (как в Backend)
    try:
        print("\n2️⃣ Тест SQLAlchemy...")
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        print(f"   URL: {DATABASE_URL}")
        
        engine = create_engine(DATABASE_URL, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"   ✅ SQLAlchemy: Подключение успешно")
    except Exception as e:
        print(f"   ❌ SQLAlchemy ошибка: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")

if __name__ == "__main__":
    test_postgres_connection() 