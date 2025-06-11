#!/usr/bin/env python3
"""
Принудительная установка переменных для локального PostgreSQL
Запустить ПЕРЕД main.py
"""

import os

# Принудительно устанавливаем переменные для локального PostgreSQL
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "digest_bot"
os.environ["DB_USER"] = "digest_bot"
os.environ["DB_PASSWORD"] = "SecurePassword123!"

print("🔧 Переменные окружения принудительно установлены для localhost PostgreSQL")
print(f"   DB_HOST: {os.environ.get('DB_HOST')}")
print(f"   DB_PORT: {os.environ.get('DB_PORT')}")
print(f"   DB_NAME: {os.environ.get('DB_NAME')}")
print(f"   DB_USER: {os.environ.get('DB_USER')}")

# Импортируем main после установки переменных
if __name__ == "__main__":
    print("🚀 Запускаем Backend с локальными PostgreSQL настройками...")
    import main 