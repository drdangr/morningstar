FROM python:3.11-slim

WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY src/ .

# Создание директории для логов
RUN mkdir -p /app/logs

# Запуск бота
CMD ["python", "-u", "bot.py"]