FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование entrypoint скрипта
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Копирование всех файлов AI сервисов
COPY . .

# Создание директории для логов
RUN mkdir -p /app/logs

# Установка переменных окружения
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV CELERY_BROKER_URL="redis://redis:6379/0"
ENV CELERY_RESULT_BACKEND="redis://redis:6379/0"
ENV CELERY_WORKER_LOGLEVEL="INFO"
ENV CELERY_WORKER_CONCURRENCY="4"

# Expose порт для мониторинга (если нужно)
EXPOSE 5555

# Health check временно отключен для тестирования
# HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
#     CMD celery -A celery_app inspect ping || exit 1

# Запуск через entry point
ENTRYPOINT ["/app/entrypoint.sh"] 