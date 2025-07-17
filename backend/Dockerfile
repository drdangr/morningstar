FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для PostgreSQL и Redis
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем директории для логов
RUN mkdir -p /app/logs

# Порт для FastAPI
EXPOSE 8000

# Команда запуска (слушаем на всех интерфейсах)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 