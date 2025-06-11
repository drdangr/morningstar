#!/usr/bin/env python3
"""
Проверка URL encoding для пароля PostgreSQL
"""

from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

def test_url_encoding():
    load_dotenv()
    
    password = os.getenv('DB_PASSWORD', 'SecurePassword123!')
    encoded = quote_plus(password)
    
    print(f"Оригинальный пароль: {password}")
    print(f"URL-кодированный: {encoded}")
    print(f"URL подключения: postgresql://digest_bot:{encoded}@localhost:5432/digest_bot")
    
    # Проверим что происходит с символом @
    if '@' in password:
        print(f"⚠️ В пароле есть символ '@' - он должен быть закодирован как '%40'")
        print(f"Кодирование правильное: {'%40' in encoded}")

if __name__ == "__main__":
    test_url_encoding() 