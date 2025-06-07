# N8N Integration для MorningStarBot3

## 📋 Обзор

N8N служит промежуточным слоем для обработки данных между userbot и backend. Workflow получает посты от userbot, обрабатывает их (фильтрация, группировка, AI анализ) и отправляет в backend для дальнейшего использования.

## 🔄 Архитектура workflow

```
Userbot → N8N Webhook → Обработка → Backend API
```

## 📋 Доступные Workflows

### 1. Базовый workflow: `telegram-digest-workflow.json`
Простая обработка с захардкоженными параметрами (Stage 2)

### 2. Конфигурируемый workflow: `telegram-digest-workflow-configurable.json` 
Продвинутая обработка с настройками через environment variables (Stage 2+)

## ⚙️ Конфигурируемый Workflow

**Этапы обработки:**

1. **Webhook - Receive Posts** 
   - Принимает POST запросы от userbot на `/webhook/telegram-digest`

2. **Load Config & Process Data**
   - Загружает конфигурацию из environment variables
   - Логирует полученные данные с учетом DEBUG_MODE
   - Подготавливает данные для обработки

3. **Has Posts?** (условие)
   - Проверяет наличие постов для обработки

4. **Basic Filtering**
   - **Конфигурируемая фильтрация** по `MIN_POST_LENGTH`, `MIN_VIEWS_THRESHOLD`, `COLLECTION_HOURS`
   - Статистика фильтрации на каждом этапе

5. **Group & Sort by Channels**
   - Группирует посты по каналам
   - Сортирует по просмотрам
   - Готовит настройки для каждого канала

6. **Smart Processing**
   - **Умная обработка** с лимитом `MAX_POSTS_PER_DIGEST`
   - Пропорциональное распределение между каналами
   - Контроль общего количества постов

7. **Prepare Configurable Digest**
   - Финальная подготовка с конфигурацией
   - Детальная статистика фильтрации

8. **Save to Backend (Configurable)**
   - Конфигурируемое сохранение через `ENABLE_BACKEND_SAVE`
   - Отправка в Backend API или только логирование

## ⚙️ Настройка

### 1. Импорт workflow

1. Откройте N8N интерфейс (обычно http://localhost:5678)
2. Перейдите в Workflows → Import from File
3. Выберите файл `telegram-digest-workflow.json`
4. Активируйте workflow

### 2. Настройка webhook URL

После импорта workflow webhook будет доступен по адресу:
```
http://your-n8n-domain:5678/webhook/telegram-digest
```

### 3. Конфигурация environment variables

#### Создайте файл конфигурации:
```bash
cp n8n/n8n-config.env.example n8n/n8n-config.env
```

#### Базовые настройки:
```env
# Processing Settings
MAX_POSTS_PER_DIGEST=20
MIN_POST_LENGTH=50
MIN_VIEWS_THRESHOLD=100
COLLECTION_HOURS=24
DEBUG_MODE=false

# Backend Integration
BACKEND_API_URL=http://localhost:8000
ENABLE_BACKEND_SAVE=false
```

#### Обновите userbot настройки:
В `.env` файле проекта добавьте/обновите:
```env
N8N_WEBHOOK_URL=http://localhost:5678/webhook/telegram-digest
TEST_MODE=false
```

## 🧪 Тестирование

### 1. Тест с userbot в production режиме

```bash
cd userbot
python src/bot.py
```

### 2. Мониторинг в N8N

- Откройте N8N UI
- Перейдите в Executions
- Следите за выполнением workflow
- Проверяйте логи каждого шага

### 3. Ручной тест webhook

```bash
curl -X POST http://localhost:5678/webhook/telegram-digest \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-06-07T18:00:00Z",
    "collection_stats": {
      "total_posts": 2,
      "successful_channels": 1,
      "failed_channels": 0,
      "channels_processed": ["@durov"]
    },
    "posts": [
      {
        "id": 123,
        "channel_id": 1001006503122,
        "channel_username": "@durov",
        "channel_title": "Pavel Durov",
        "text": "Test post content",
        "date": "2025-06-07T17:00:00Z",
        "views": 1000,
        "url": "https://t.me/durov/123"
      }
    ]
  }'
```

## 📊 Мониторинг и логи

### Логи в N8N
- Каждый шаг workflow логирует свои действия
- Проверяйте Console Output в каждой ноде
- Следите за Execution History

### Ключевые метрики
- Количество обработанных постов
- Время выполнения workflow
- Ошибки обработки
- Статистика фильтрации AI

## 🔧 Кастомизация

### Изменение логики AI обработки

Отредактируйте ноду **AI Processing (Mock)**:
- Измените критерии фильтрации
- Добавьте новые алгоритмы ранжирования
- Интегрируйте реальные AI сервисы

### Добавление новых этапов

Можно добавить:
- Дедупликацию постов
- Генерацию саммари
- Отправку уведомлений
- Сохранение в дополнительные БД

## 🚀 Production настройки

### Переменные окружения

```env
N8N_WEBHOOK_URL=https://your-n8n-domain/webhook/telegram-digest
N8N_WEBHOOK_TOKEN=your-secure-token
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password
```

### Безопасность
- Используйте HTTPS для webhook
- Настройте аутентификацию
- Добавьте rate limiting
- Проверяйте входящие данные

## 🐛 Troubleshooting

### Workflow не запускается
- Проверьте что workflow активен
- Убедитесь что webhook URL корректный
- Проверьте логи N8N

### Userbot не может отправить данные
- Проверьте доступность N8N
- Убедитесь что `TEST_MODE=false`
- Проверьте формат отправляемых данных

### Ошибки в обработке
- Проверьте логи каждой ноды
- Убедитесь в корректности JSON структуры
- Проверьте доступность Backend API

## 📈 Следующие шаги

1. **Интеграция с Backend API** - настройка реальной отправки дайджестов
2. **AI обработка** - интеграция с OpenAI/другими сервисами
3. **Персонализация** - учет пользовательских предпочтений
4. **Масштабирование** - оптимизация для больших объемов данных 