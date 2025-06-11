#!/usr/bin/env python3
"""
Простейший тест .env файла
"""

import os
from dotenv import load_dotenv
from pathlib import Path

print("🔍 ПРОСТОЙ ТЕСТ .env ФАЙЛА")
print("=" * 40)

# Находим .env файл
env_path = Path(__file__).parent.parent / '.env'
print(f"📁 Путь к .env: {env_path}")
print(f"📁 Файл существует: {env_path.exists()}")

if env_path.exists():
    print(f"📁 Размер файла: {env_path.stat().st_size} байт")
    
    # Ищем ВСЕ строки с DB_HOST
    print("🔍 Поиск ВСЕХ строк с DB_HOST:")
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if 'DB_HOST' in line_clean:
                print(f"  Строка {i+1}: {line_clean}")
    
    # Читаем первые строки файла
    print("\n📄 Первые 15 строк файла:")
    for i, line in enumerate(lines[:15]):
        line = line.strip()
        if line and not line.startswith('#'):
            # Скрываем пароли
            if 'PASSWORD' in line:
                parts = line.split('=')
                if len(parts) == 2:
                    line = f"{parts[0]}=***СКРЫТО***"
            print(f"  {i+1}: {line}")
    
    # Проверяем load_dotenv
    print("\n🔄 Тестируем load_dotenv...")
    result = load_dotenv(env_path)
    print(f"   load_dotenv результат: {result}")
    
    # Проверяем что загрузилось
    print("\n📋 После load_dotenv:")
    for key in ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER']:
        value = os.getenv(key, "НЕ НАЙДЕНА")
        print(f"   {key}: {value}")
else:
    print("❌ .env файл не найден!") 