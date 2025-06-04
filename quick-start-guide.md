# MorningStar Bot - Быстрый старт

## Предварительные требования

1. **Docker & Docker Compose** установлены
2. **Telegram API credentials**:
   - Получи на https://my.telegram.org
   - Нужны: API ID и API Hash
3. **Telegram Bot Token**:
   - Создай бота через @BotFather
   - Получи токен

## Шаг 1: Клонирование и настройка

```bash
# Клонируй репозиторий
git clone https://github.com/drdangr/morningstar.git
cd morningstar

# Создай .env из примера
cp .env.example .env

# Отредактируй .env файл с твоими данными
nano .env  # или используй любой редактор
```

## Шаг 2: Создание структуры папок

```bash
# Windows PowerShell
mkdir userbot\src, userbot\session, userbot\logs
mkdir bot\src, bot\logs  
mkdir database\migrations
mkdir n8n\workflows

# Linux/Mac
mkdir -p userbot/{src,session,logs}
mkdir -p bot/{src,logs}
mkdir -p database/migrations
mkdir -p n8n/workflows
```

## Шаг 3: Создание Dockerfile для userbot

Создай файл `userbot/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

CMD ["python", "bot.py"]
```

## Шаг 4: Создание requirements.txt для userbot

Создай файл `userbot/requirements.txt`:

```
telethon==1.34.0
python-dotenv==1.0.0
aiohttp==3.9.3
asyncio==3.4.3
```

## Шаг 5: Базовый userbot код

Создай файл `userbot/src/bot.py`:

```python
import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
phone = os.getenv('PHONE')

client = TelegramClient('/app/session/morningstar', api_id, api_hash)

async def main():
    await client.start(phone)
    print("Userbot started successfully!")
    
    # Тестовое чтение каналов
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f"Channel: {dialog.name}")
            break

if __name__ == '__main__':
    asyncio.run(main())
```

## Шаг 6: Запуск

```bash
# Запусти все сервисы
docker-compose up -d

# Проверь логи
docker-compose logs -f

# При первом запуске userbot попросит код подтверждения
docker-compose logs -f userbot
```

## Шаг 7: Доступ к сервисам

- **n8n**: http://localhost:5678
- **PostgreSQL**: localhost:5432
- **Логи**: `docker-compose logs [service_name]`

## Следующие шаги

1. Настрой n8n workflow для приема данных
2. Добавь каналы для мониторинга
3. Настрой AI обработку
4. Запусти Telegram бота

## Полезные команды

```bash
# Остановить все сервисы
docker-compose down

# Перезапустить сервис
docker-compose restart userbot

# Обновить код и перезапустить
docker-compose build userbot
docker-compose up -d userbot

# Войти в контейнер
docker exec -it morningstar_userbot bash
```

## Проблемы?

1. **Ошибка авторизации**: Проверь API credentials
2. **n8n не доступен**: Проверь порт 5678
3. **База не создается**: Проверь права доступа

Подробная документация в [README.md](README.md)