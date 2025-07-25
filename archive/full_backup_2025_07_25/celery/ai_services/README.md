# AI Services для MorningStarBot3

## Архитектура

```
ai_services/
├── services/                 # Основные AI сервисы
│   ├── summarization.py     # Сервис суммаризации постов
│   ├── categorization.py    # Сервис категоризации постов
│   └── base.py             # Базовый класс для AI сервисов
├── models/                  # Модели данных
│   ├── post.py             # Модель поста
│   ├── digest.py           # Модель дайджеста
│   └── bot.py              # Модель бота
├── api/                    # FastAPI endpoints
│   ├── routes.py           # API маршруты
│   └── middleware.py       # Middleware (auth, logging)
├── config/                 # Конфигурация
│   ├── settings.py         # Настройки приложения
│   └── prompts.py          # Шаблоны промптов
├── utils/                  # Утилиты
│   ├── logging.py          # Настройка логирования
│   └── metrics.py          # Метрики производительности
└── tests/                  # Тесты
    ├── test_summarization.py
    └── test_categorization.py
```

## Основные компоненты

### 1. SummarizationService
- Генерация краткого содержания постов
- Поддержка множественных языков
- Настраиваемая длина резюме
- Кастомные промпты для каждого бота

### 2. CategorizationService
- Категоризация постов по темам
- Бинарная релевантность для каждой категории
- Метрики importance/urgency/significance
- Индивидуальные промпты для каждого бота

### 3. API Endpoints
- POST /api/v1/summarize - Суммаризация поста
- POST /api/v1/categorize - Категоризация поста
- POST /api/v1/process-batch - Пакетная обработка
- GET /api/v1/health - Проверка работоспособности

## Установка и запуск

1. Создать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Настроить переменные окружения:
```bash
cp .env.example .env
# Отредактировать .env файл
```

4. Запустить сервис:
```bash
uvicorn api.main:app --reload
```

## Тестирование

```bash
pytest tests/
```

## Метрики

- Время обработки поста
- Токены использованы
- Качество категоризации
- Длина резюме
- Ошибки и исключения 