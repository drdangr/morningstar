FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка Python пакетов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создание пользователя без root прав
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Создание директорий
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Переключение на пользователя
USER appuser

# Копирование исходного кода
COPY --chown=appuser:appuser src/ .

# Проверка работоспособности (исправленная)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from telegram.ext import Application; print('OK')" || exit 1

# Запуск приложения
CMD ["python", "-u", "bot.py"]