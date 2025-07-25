FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для PostgreSQL и Redis
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Установка Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
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