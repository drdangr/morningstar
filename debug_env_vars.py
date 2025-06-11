#!/usr/bin/env python3
"""
Диагностика переменных окружения для Backend
"""
import os
from dotenv import load_dotenv

print("🔍 ДИАГНОСТИКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 50)

# Загружаем .env как делает Backend
load_dotenv()

# Переменные БД
db_vars = {
    "DB_HOST": os.getenv("DB_HOST", "localhost"),
    "DB_PORT": os.getenv("DB_PORT", "5432"), 
    "DB_NAME": os.getenv("DB_NAME", "digest_bot"),
    "DB_USER": os.getenv("DB_USER", "digest_bot"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD", "SecurePassword123!")
}

print("📋 Переменные базы данных:")
for key, value in db_vars.items():
    if "PASSWORD" in key:
        masked_value = "*" * len(value) if value else "(пустое)"
        print(f"  {key}: {masked_value}")
        print(f"    Реальная длина: {len(value)} символов")
        print(f"    Из .env?: {'ДА' if key in os.environ else 'НЕТ (дефолт)'}")
    else:
        print(f"  {key}: {value}")
        print(f"    Из .env?: {'ДА' if key in os.environ else 'НЕТ (дефолт)'}")

print("\n🔑 ТЕСТИРОВАНИЕ ПАРОЛЕЙ:")
print("-" * 30)

# Тестируем текущий пароль
current_password = db_vars["DB_PASSWORD"]
print(f"Текущий пароль из переменных: {'*' * len(current_password)}")

# Известные рабочие пароли
working_passwords = {
    "digest_bot": "SecurePassword123!",
    "postgres": "Demiurg12@"
}

print("\nИзвестные рабочие пароли:")
for user, password in working_passwords.items():
    match_status = "✅ СОВПАДАЕТ" if (user == "digest_bot" and password == current_password) else "❌ НЕ СОВПАДАЕТ"
    print(f"  {user}: {'*' * len(password)} - {match_status}")

print("\n💡 РЕКОМЕНДАЦИЯ:")
if current_password == "SecurePassword123!":
    print("✅ Пароль ПРАВИЛЬНЫЙ! Проблема может быть в другом.")
else:
    print(f"❌ Пароль НЕПРАВИЛЬНЫЙ!")
    print(f"   Текущий: {'*' * len(current_password)} ({len(current_password)} символов)")
    print(f"   Нужный:  {'*' * len('SecurePassword123!')} ({len('SecurePassword123!')} символов)")
    print("   Исправьте в .env файле: DB_PASSWORD=SecurePassword123!") 