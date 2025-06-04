FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY src/ .

# Создание директорий для сессий и логов
RUN mkdir -p /app/session /app/logs

# Запуск бота
CMD ["python", "-u", "bot.py"]