# Integration Scenarios - MorningStarBot3

## 📋 Обзор

Практические сценарии использования и реальные примеры payload'ов для **Stage 2: N8N Integration**.

---

## 1. Базовый сценарий работы

### 1.1 Полный цикл обработки

```
Admin Panel → Backend API → Userbot → N8N → Backend API → Result
```

**Шаги:**
1. Админ добавляет каналы через веб-интерфейс
2. Backend API сохраняет каналы в базу данных
3. Userbot читает каналы через `/api/channels?active_only=true`
4. Userbot собирает посты и отправляет в N8N webhook
5. N8N обрабатывает данные согласно конфигурации
6. N8N отправляет результат обратно в Backend API
7. Результат доступен в системе

### 1.2 Временные интервалы

- **Сбор данных:** каждые 6/12/24 часа (настраивается)
- **Обработка N8N:** мгновенно после получения данных
- **Глубина сбора:** последние 24 часа (по умолчанию)

---

## 2. Реальные Payload примеры

### 2.1 Userbot → N8N (реальный пример)

#### Успешный сбор (91 пост из 2 каналов):
```json
{
  "timestamp": "2025-06-07T18:20:33Z",
  "collection_stats": {
    "total_posts": 91,
    "successful_channels": 2,
    "failed_channels": 0,
    "channels_processed": ["@breakingmash", "@durov"],
    "collection_duration_ms": 15247,
    "collection_mode": "production"
  },
  "posts": [
    {
      "id": 2342,
      "channel_id": 1001006503122,
      "channel_username": "@durov",
      "channel_title": "Pavel Durov",
      "text": "🆒 In case you missed it, here are some of the coolest features we added to Telegram throughout 2023...",
      "date": "2025-06-07T17:30:00Z",
      "views": 1247,
      "forwards": 12,
      "replies": 8,
      "url": "https://t.me/durov/2342",
      "media_type": "text"
    },
    {
      "id": 15823,
      "channel_id": 1001312395,
      "channel_username": "@breakingmash",
      "channel_title": "Mash",
      "text": "В Москве на Арбате открылась новая кофейня...",
      "date": "2025-06-07T18:15:00Z",
      "views": 456,
      "forwards": 3,
      "replies": 1,
      "url": "https://t.me/breakingmash/15823",
      "media_type": "photo"
    }
  ]
}
```

#### Обработка с ошибками:
```json
{
  "timestamp": "2025-06-07T18:20:33Z",
  "collection_stats": {
    "total_posts": 45,
    "successful_channels": 1,
    "failed_channels": 1,
    "channels_processed": ["@durov"],
    "failed_channels_details": [
      {
        "channel": "@nonexistent_channel",
        "error": "Channel not found",
        "error_code": "CHANNEL_NOT_FOUND"
      }
    ]
  },
  "posts": [...]
}
```

### 2.2 N8N Processing результаты

#### После базовой фильтрации:
```json
{
  "timestamp": "2025-06-07T18:20:33Z",
  "processed_at": "2025-06-07T18:20:34Z",
  "stats": {
    "total_posts": 91,
    "successful_channels": 2
  },
  "processed_channels": {
    "@durov": {
      "channel_title": "Pavel Durov",
      "posts": [
        {
          "id": 2342,
          "text": "🆒 In case you missed it...",
          "views": 1247,
          "url": "https://t.me/durov/2342",
          "date": "2025-06-07T17:30:00Z"
        }
      ],
      "filtered_count": 2,
      "original_count": 2
    },
    "@breakingmash": {
      "channel_title": "Mash",
      "posts": [...],
      "filtered_count": 15,
      "original_count": 89
    }
  },
  "total_selected_posts": 17,
  "configuration": {
    "max_posts_limit": 20,
    "min_post_length": 50,
    "min_views_threshold": 100,
    "processing_mode": "basic"
  },
  "filtering_stats": {
    "original": 91,
    "after_basic_filter": 67,
    "after_smart_filter": 17
  }
}
```

#### Финальный дайджест:
```json
{
  "id": "digest_1701970833000",
  "created_at": "2025-06-07T18:20:33Z",
  "processed_at": "2025-06-07T18:20:34Z",
  "channels": [
    {
      "title": "Pavel Durov",
      "username": "@durov",
      "posts_count": 2,
      "posts": [
        {
          "title": "🆒 In case you missed it, here are some of the coolest features we added to Telegram...",
          "url": "https://t.me/durov/2342",
          "views": 1247,
          "date": "2025-06-07T17:30:00Z",
          "media_type": "text"
        }
      ]
    },
    {
      "title": "Mash",
      "username": "@breakingmash", 
      "posts_count": 15,
      "posts": [...]
    }
  ],
  "total_posts": 17,
  "configuration": {
    "max_posts_limit": 20,
    "min_post_length": 50,
    "min_views_threshold": 100,
    "processing_mode": "basic"
  },
  "summary": {
    "channels_processed": 2,
    "original_posts": 91,
    "filtered_posts": 17,
    "filtering_stages": {
      "original": 91,
      "after_basic_filter": 67,
      "after_smart_filter": 17
    }
  }
}
```

---

## 3. Конфигурационные сценарии

### 3.1 Режим разработки (TEST_MODE=true)

```bash
# .env настройки
TEST_MODE=true
N8N_WEBHOOK_URL=http://localhost:5678/webhook/telegram-digest
```

**Поведение:**
- Userbot НЕ отправляет данные в N8N
- Все логирование в консоль
- Возможность отладки без влияния на N8N

### 3.2 Продакшн режим (TEST_MODE=false)

```bash
# .env настройки  
TEST_MODE=false
N8N_WEBHOOK_URL=http://localhost:5678/webhook/telegram-digest
```

**Поведение:**
- Userbot отправляет реальные данные в N8N
- Полная цепочка обработки активна
- Результаты сохраняются

### 3.3 N8N конфигурации

#### Базовая обработка:
```env
MAX_POSTS_PER_DIGEST=20
MIN_POST_LENGTH=50
MIN_VIEWS_THRESHOLD=100
COLLECTION_HOURS=24
DEBUG_MODE=false
ENABLE_BACKEND_SAVE=false
```

#### Строгая фильтрация:
```env
MAX_POSTS_PER_DIGEST=10
MIN_POST_LENGTH=100
MIN_VIEWS_THRESHOLD=500
COLLECTION_HOURS=12
DEBUG_MODE=true
ENABLE_BACKEND_SAVE=true
```

#### Мягкая фильтрация:
```env
MAX_POSTS_PER_DIGEST=50
MIN_POST_LENGTH=20
MIN_VIEWS_THRESHOLD=50
COLLECTION_HOURS=48
DEBUG_MODE=false
ENABLE_BACKEND_SAVE=true
```

---

## 4. Сценарии ошибок и их обработка

### 4.1 Backend API недоступен

**Userbot поведение:**
```javascript
// Fallback на каналы из .env
const fallbackChannels = process.env.CHANNELS.split(',');
console.log('⚠️ Backend API недоступен, используем fallback каналы');
```

**Пример лога:**
```
⚠️ Ошибка получения каналов из API: fetch failed
📋 Используем fallback каналы из .env: @durov,@breakingmash
```

### 4.2 N8N недоступен

**Userbot поведение:**
```javascript
try {
  await fetch(N8N_WEBHOOK_URL, {method: 'POST', body: data});
} catch (error) {
  console.error('❌ N8N недоступен:', error.message);
  // Сохранение данных локально для повторной отправки
}
```

### 4.3 Некорректные данные в N8N

**N8N обработка:**
```javascript
// Валидация входных данных
if (!payload.posts || !Array.isArray(payload.posts)) {
  console.error('❌ Некорректная структура данных');
  return {success: false, error: 'Invalid payload structure'};
}
```

---

## 5. Производительность и ограничения

### 5.1 Лимиты обработки

| Параметр | Значение | Настройка |
|----------|----------|-----------|
| Максимум постов в дайджесте | 20 | `MAX_POSTS_PER_DIGEST` |
| Минимальная длина поста | 50 символов | `MIN_POST_LENGTH` |
| Минимальные просмотры | 100 | `MIN_VIEWS_THRESHOLD` |
| Время обработки N8N | 300 сек | `N8N_WORKFLOW_TIMEOUT` |
| Размер одного поста | ~2KB | - |

### 5.2 Типичные объемы данных

**Малый канал (100-500 подписчиков):**
- Постов в день: 1-5
- Размер payload: 5-25KB
- Время обработки: <1 сек

**Средний канал (10K-100K подписчиков):**
- Постов в день: 10-50
- Размер payload: 50-250KB  
- Время обработки: 1-3 сек

**Крупный канал (1M+ подписчиков):**
- Постов в день: 50-200
- Размер payload: 250KB-1MB
- Время обработки: 3-10 сек

---

## 6. Мониторинг и диагностика

### 6.1 Ключевые логи для отслеживания

#### Userbot логи:
```
📊 Statistics: 91 posts from 2 channels
✅ Данные успешно отправлены в n8n: 200
⚠️ Backend API недоступен, используем fallback каналы
```

#### N8N логи:
```
🔧 Configuration loaded: {"maxPostsPerDigest":20,"minPostLength":50}
📊 Basic filtering: 91 → 67 posts
🤖 Smart processing with configuration...
✅ Configurable digest ready: Posts: 17/20 (limit)
```

### 6.2 Индикаторы проблем

**Проблемы сбора:**
- `successful_channels < expected`
- `total_posts = 0`
- `collection_duration_ms > 30000`

**Проблемы обработки:**
- `after_basic_filter = 0`
- `total_selected_posts = 0`
- `processing_mode != expected`

**Проблемы сохранения:**
- `save_enabled = false` (когда ожидается true)
- `backend_url != configured`

---

## 7. Примеры тестирования

### 7.1 Тест userbot интеграции

```bash
# В userbot/
python src/bot.py

# Ожидаемый результат:
# 📋 Загружен список каналов из Backend API: 2 каналов
# 📊 Statistics: X posts from Y channels  
# ✅ Данные успешно отправлены в n8n: 200
```

### 7.2 Тест N8N webhook

```bash
curl -X POST http://localhost:5678/webhook/telegram-digest \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-06-07T18:00:00Z",
    "collection_stats": {
      "total_posts": 2,
      "successful_channels": 1
    },
    "posts": [
      {
        "id": 123,
        "channel_username": "@test",
        "text": "Test post with enough length to pass filtering",
        "views": 150,
        "date": "2025-06-07T17:00:00Z"
      }
    ]
  }'
```

### 7.3 Проверка конфигурации N8N

```env
# Установить debug режим
DEBUG_MODE=true

# Запустить workflow и проверить логи:
# 🔧 Configuration loaded: {...}
# 📊 Basic filtering: 2 → 1 posts
# ✅ Configurable digest ready: Posts: 1/20 (limit)
```

---

## 8. Готовность к Stage 3

### 8.1 Подготовленная структура для AI

**Текущий формат готов для расширения:**
```json
{
  "posts": [
    {
      "text": "Post content",
      "categories": [],  // ← Готово для AI категоризации
      "quality_score": 0, // ← Готово для AI оценки
      "summary": "" // ← Готово для AI summary
    }
  ]
}
```

### 8.2 Environment variables для AI

```env
# Уже подготовлены в n8n-config.env.example:
ENABLE_AI_PROCESSING=false  # Включить для Stage 3
AI_PROVIDER=openai
AI_MODEL=gpt-4
QUALITY_THRESHOLD=0.7
```

---

## 📊 Заключение

**Stage 2: N8N Integration** полностью задокументирован и готов к продакшн использованию:

- ✅ Реальные примеры payload'ов
- ✅ Сценарии обработки ошибок  
- ✅ Конфигурационные варианты
- ✅ Производительность и лимиты
- ✅ Мониторинг и диагностика
- ✅ Готовность к Stage 3

**Система готова к масштабированию и внедрению AI обработки!** 🚀 