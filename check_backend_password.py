#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

# Как в Backend
DB_PASSWORD = os.getenv("DB_PASSWORD", "Demiurg12@")

print(f"Backend пароль: {'*' * len(DB_PASSWORD)} ({len(DB_PASSWORD)} символов)")
print(f"Источник: {'из .env' if 'DB_PASSWORD' in os.environ else 'дефолт'}")

if len(DB_PASSWORD) == 10:
    print("❌ Использует НЕПРАВИЛЬНЫЙ пароль из .env!")
    print("💡 Нужно исправить .env: DB_PASSWORD=Demiurg12@")
elif DB_PASSWORD == "Demiurg12@":
    print("✅ Использует ПРАВИЛЬНЫЙ пароль!")
else:
    print("⚠️ Неизвестный пароль") 