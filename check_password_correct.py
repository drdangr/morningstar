#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

# Пароль из .env
password_from_env = os.getenv("DB_PASSWORD", "")
correct_password = "Demiurg12@"

print(f"🔍 ПРАВИЛЬНАЯ ДИАГНОСТИКА ПАРОЛЕЙ")
print("=" * 40)
print(f"Пароль из .env: '{password_from_env}' ({len(password_from_env)} символов)")
print(f"Правильный:     '{correct_password}' ({len(correct_password)} символов)")
print(f"Совпадают:      {'✅ ДА' if password_from_env == correct_password else '❌ НЕТ'}")

if password_from_env == correct_password:
    print(f"\n🎉 ПАРОЛЬ ПРАВИЛЬНЫЙ! Backend должен работать с PostgreSQL")
else:
    print(f"\n❌ Пароли не совпадают!")
    print(f"   Ожидался: '{correct_password}'")
    print(f"   Получен:  '{password_from_env}'") 