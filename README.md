# Telegram Digest Bot - Техническая документация

## Оглавление
1. [Описание проекта](#описание-проекта)
2. [Архитектура системы](#архитектура-системы)
3. [Компоненты системы](#компоненты-системы)
4. [Технологический стек](#технологический-стек)
5. [Структура базы данных](#структура-базы-данных)
6. [API и взаимодействие](#api-и-взаимодействие)
7. [Этапы реализации](#этапы-реализации)
8. [Настройка окружения](#настройка-окружения)
9. [Безопасность](#безопасность)
10. [Масштабирование](#масштабирование)

## Описание проекта

### Цель
Создание автоматизированной системы для агрегации контента из Telegram каналов с последующей обработкой через AI и доставкой персонализированных дайджестов пользователям.

### Ключевые возможности
- Автоматический сбор контента из выбранных Telegram каналов
- AI-обработка для создания кратких саммари
- Категоризация контента по темам
- Персонализированная доставка дайджестов
- Административная панель для управления каналами и категориями
- Публичный бот для пользователей

### Пользовательские роли
1. **Администратор** - управляет списком каналов, категориями, настройками фильтрации
2. **Пользователи** - подписываются на категории, получают дайджесты

## Архитектура системы

### Общая схема
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Telegram        │     │ Python       │     │    n8n      │
│ Channels        │────▶│ Userbot      │────▶│ Workflows   │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                      │
                                                      ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Users           │◀────│ Telegram Bot │◀────│  Database   │
└─────────────────┘     └──────────────┘     └─────────────┘
```

### Поток данных
1. Userbot собирает посты из каналов
2. Отправляет данные в n8n через webhook
3. n8n обрабатывает контент через AI
4. Сохраняет результаты в БД
5. Bot отправляет дайджесты пользователям

## Компоненты системы

### 1. Python Userbot
**Функции:**
- Авторизация через Telegram API
- Чтение сообщений из списка каналов
- Фильтрация по дате/времени
- Отправка данных в n8n

**Структура:**
```python
/userbot
├── bot.py           # Основная логика
├── config.py        # Конфигурация
├── channels.py      # Управление каналами
├── parser.py        # Парсинг сообщений
├── webhook.py       # Отправка в n8n
├── Dockerfile
└── requirements.txt
```

### 2. n8n Workflows
**Основные workflow:**
- **Data Ingestion** - прием данных от userbot
- **Content Processing** - AI обработка и категоризация
- **Digest Generation** - создание дайджестов
- **Distribution** - отправка пользователям

**Ноды:**
- Webhook (триггер)
- HTTP Request (AI API)
- Database operations
- Telegram Bot API
- Schedule triggers

### 3. Telegram Bot
**Команды пользователя:**
- `/start` - регистрация и онбординг
- `/categories` - список доступных категорий
- `/subscribe [category]` - подписка на категорию
- `/unsubscribe [category]` - отписка
- `/settings` - настройки доставки
- `/digest` - получить дайджест сейчас

**Команды администратора:**
- `/admin` - админ панель
- `/add_channel` - добавить канал
- `/add_category` - создать категорию
- `/stats` - статистика использования

### 4. База данных
**PostgreSQL/SQLite структура** (см. раздел Структура БД)

## Технологический стек

### Backend
- **Python 3.11** - userbot
- **Telethon** - Telegram userbot API
- **n8n** - workflow automation
- **PostgreSQL/SQLite** - база данных
- **Docker & Docker Compose** - контейнеризация

### AI/ML
- **OpenAI API** / **Claude API** - для саммаризации
- **LangChain** (опционально) - для сложной обработки

### Инфраструктура
- **Docker** - контейнеры
- **Nginx** (опционально) - reverse proxy
- **Redis** (опционально) - кеширование

## Структура базы данных

### Таблицы

#### users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ru',
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### categories
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    emoji VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    ai_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### channels
```sql
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    title VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_parsed TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### channel_categories
```sql
CREATE TABLE channel_categories (
    channel_id INTEGER REFERENCES channels(id),
    category_id INTEGER REFERENCES categories(id),
    PRIMARY KEY (channel_id, category_id)
);
```

#### user_subscriptions
```sql
CREATE TABLE user_subscriptions (
    user_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    frequency VARCHAR(50) DEFAULT 'daily',
    delivery_time TIME DEFAULT '09:00',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, category_id)
);
```

#### posts
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id),
    telegram_message_id BIGINT,
    content TEXT,
    media_type VARCHAR(50),
    media_url TEXT,
    summary TEXT,
    category_id INTEGER REFERENCES categories(id),
    posted_at TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### digests
```sql
CREATE TABLE digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    content TEXT,
    posts_included INTEGER[],
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API и взаимодействие

### Webhook endpoints (n8n)

#### POST /webhook/telegram-posts
```json
{
    "channel_id": 123456789,
    "messages": [
        {
            "id": 1234,
            "text": "Post content",
            "date": "2025-01-15T10:00:00Z",
            "media": {
                "type": "photo",
                "url": "https://..."
            }
        }
    ]
}
```

#### POST /webhook/trigger-digest
```json
{
    "user_id": 123456789,
    "category_id": 1,
    "type": "manual"
}
```

### Внутренние API

#### Userbot → n8n
- Метод: HTTP POST
- Аутентификация: Bearer token
- Формат: JSON
- Частота: каждые 30 минут

#### n8n → Telegram Bot
- Использует официальный Bot API
- Webhook или long polling

## Этапы реализации

### Этап 1: MVP (1-2 недели)
1. **Настройка инфраструктуры**
   - Docker окружение
   - База данных (SQLite для начала)
   - n8n установка

2. **Базовый userbot**
   - Авторизация
   - Чтение 2-3 тестовых каналов
   - Отправка в n8n

3. **Простой n8n workflow**
   - Прием данных
   - Сохранение в БД
   - Базовая AI обработка

4. **Минимальный бот**
   - Команды start, help
   - Ручная отправка дайджеста админу

### Этап 2: Основной функционал (2-3 недели)
1. **Расширение userbot**
   - Динамический список каналов
   - Обработка медиа
   - Обработка ошибок

2. **n8n workflows**
   - Категоризация
   - Дедупликация
   - Scheduled дайджесты

3. **Пользовательский бот**
   - Все базовые команды
   - Подписки на категории
   - Настройки доставки

### Этап 3: Продвинутые функции (2-3 недели)
1. **Админ панель**
   - Управление каналами
   - Создание категорий
   - Статистика

2. **Улучшенная AI обработка**
   - Кастомные промпты
   - Мультиязычность
   - Качество саммари

3. **Оптимизация**
   - Кеширование
   - Batch обработка
   - Мониторинг

### Этап 4: Продакшн (1-2 недели)
1. **Безопасность**
   - Шифрование сессий
   - Rate limiting
   - Валидация данных

2. **Масштабирование**
   - PostgreSQL миграция
   - Redis кеш
   - Логирование

3. **Документация**
   - Пользовательская
   - Техническая
   - API документация

## Настройка окружения

### Требования
- Docker & Docker Compose
- Python 3.11+
- 2GB RAM минимум
- 10GB диск

### Структура проекта
```
telegram-digest-bot/
├── docker-compose.yml
├── .env.example
├── userbot/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── n8n/
│   ├── workflows/
│   └── credentials/
├── bot/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── database/
│   ├── init.sql
│   └── migrations/
└── docs/
```

### Docker Compose
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: digest_bot
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n

  userbot:
    build: ./userbot
    environment:
      - API_ID=${TELEGRAM_API_ID}
      - API_HASH=${TELEGRAM_API_HASH}
      - PHONE=${TELEGRAM_PHONE}
      - N8N_WEBHOOK_URL=http://n8n:5678/webhook/telegram-posts
    volumes:
      - ./userbot/session:/app/session
    depends_on:
      - n8n

  telegram-bot:
    build: ./bot
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/digest_bot
    depends_on:
      - postgres

volumes:
  postgres_data:
  n8n_data:
```

### Переменные окружения (.env)
```bash
# Database
DB_USER=digest_bot
DB_PASSWORD=secure_password

# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
BOT_TOKEN=bot_token_from_botfather

# n8n
N8N_USER=admin
N8N_PASSWORD=secure_password

# AI
OPENAI_API_KEY=your_openai_key
```

## Безопасность

### Основные принципы
1. **Изоляция компонентов** - каждый сервис в отдельном контейнере
2. **Минимальные привилегии** - только необходимые права доступа
3. **Шифрование данных** - сессии и чувствительные данные
4. **Валидация входных данных** - защита от инъекций

### Меры безопасности
- Хранение сессий userbot в зашифрованном виде
- API токены в переменных окружения
- Rate limiting для защиты от спама
- Логирование всех административных действий
- Регулярное обновление зависимостей

### Telegram специфика
- Соблюдение лимитов API
- Ротация сессий
- Обработка флуда и спама
- Защита от бана аккаунта

## Масштабирование

### Вертикальное
- Увеличение ресурсов сервера
- Оптимизация запросов к БД
- Кеширование частых запросов

### Горизонтальное
- Несколько userbot инстансов
- Распределение каналов между инстансами
- Load balancing для бота
- Репликация БД

### Оптимизации
- Batch обработка сообщений
- Асинхронная обработка в n8n
- Индексы в БД
- CDN для медиа контента

## Мониторинг и логирование

### Метрики
- Количество обработанных сообщений
- Время генерации дайджестов
- Активные пользователи
- Ошибки обработки

### Инструменты
- Prometheus + Grafana для метрик
- ELK стек для логов
- Sentry для ошибок
- Telegram уведомления для критических событий

## Дополнительные возможности

### Будущие улучшения
1. **Веб-интерфейс** для администрирования
2. **Множественные языки** дайджестов
3. **Персонализация AI** под предпочтения пользователя
4. **Экспорт дайджестов** в PDF/Email
5. **Интеграция с другими источниками** (RSS, Twitter)
6. **Платные подписки** для премиум категорий

### Интеграции
- Email рассылка дайджестов
- Webhook для внешних систем
- API для сторонних разработчиков
- Интеграция с Notion/Obsidian

## Заключение

Данная архитектура обеспечивает гибкую и масштабируемую систему для создания персонализированных дайджестов из Telegram каналов. Модульная структура позволяет легко добавлять новые функции и интеграции по мере развития проекта.