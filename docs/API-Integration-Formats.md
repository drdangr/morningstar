# API Integration Formats - MorningStarBot3

## 📋 Обзор

Этот документ описывает форматы данных, передаваемых между компонентами системы на **Stage 2: N8N Integration**.

## 🔄 Архитектура передачи данных

```
Admin Panel → Backend API → Userbot → N8N → Backend API
```

---

## 1. Admin Panel ↔ Backend API

### 1.1 Categories (Топики)

#### GET /api/categories
**Response:**
```json
[
  {
    "id": 1,
    "name": "Технологии",
    "description": "Новости технологий и IT",
    "emoji": "💻",
    "is_active": true,
    "ai_prompt": "Фильтруй посты о технологиях, программировании, AI",
    "sort_order": 0,
    "created_at": "2025-06-07T10:00:00Z",
    "updated_at": "2025-06-07T10:00:00Z"
  }
]
```

#### POST /api/categories
**Request:**
```json
{
  "name": "Технологии",
  "description": "Новости технологий и IT",
  "emoji": "💻",
  "is_active": true,
  "ai_prompt": "Фильтруй посты о технологиях, программировании, AI",
  "sort_order": 0
}
```

### 1.2 Channels (Каналы)

#### GET /api/channels?active_only=true
**Response:**
```json
[
  {
    "id": 1,
    "telegram_id": 1001006503122,
    "username": "durov",
    "title": "Pavel Durov",
    "description": "Канал Павла Дурова",
    "is_active": true,
    "last_parsed": "2025-06-07T18:00:00Z",
    "error_count": 0,
    "created_at": "2025-06-07T10:00:00Z",
    "updated_at": "2025-06-07T18:00:00Z",
    "categories": [
      {
        "id": 1,
        "name": "Технологии",
        "emoji": "💻"
      }
    ]
  }
]
```

---

## 2. Backend API → Userbot

### 2.1 Каналы для сбора

#### GET /api/channels?active_only=true
**Userbot получает:**
- Список активных каналов
- **Топики каждого канала** (categories)
- Метаданные для фильтрации

**Текущая обработка Userbot:**
```python
# Извлекает только username
api_channels = []
for channel in channels_data:
    if channel.get('is_active', False):
        username = channel.get('username')
        if username:
            api_channels.append(f"@{username}")
```

**Планируемая обработка (Stage 3):**
```python
# Будет извлекать топики тоже
channel_data = {
    'username': f"@{channel['username']}",
    'categories': channel.get('categories', []),
    'ai_settings': {}
}
```

---

## 3. Userbot → N8N

### 3.1 Текущий формат (Stage 2)

#### POST /webhook/telegram-digest
**Payload:**
```json
{
  "timestamp": "2025-06-07T18:20:00Z",
  "collection_stats": {
    "total_posts": 91,
    "successful_channels": 2,
    "failed_channels": 0,
    "channels_processed": ["@breakingmash", "@durov"]
  },
  "posts": [
    {
      "id": 123,
      "channel_id": 1001006503122,
      "channel_username": "@durov",
      "channel_title": "Pavel Durov",
      "text": "🆒 In case you missed it...",
      "date": "2025-06-07T17:00:00Z",
      "views": 1000,
      "forwards": 5,
      "replies": 2,
      "url": "https://t.me/durov/123",
      "media_type": "text"
    }
  ]
}
```

### 3.2 Планируемый формат (Stage 3)

#### POST /webhook/telegram-digest
**Extended Payload с топиками:**
```json
{
  "timestamp": "2025-06-07T18:20:00Z",
  "collection_stats": {
    "total_posts": 91,
    "successful_channels": 2,
    "failed_channels": 0,
    "channels_processed": ["@breakingmash", "@durov"]
  },
  "posts": [
    {
      "id": 123,
      "channel_id": 1001006503122,
      "channel_username": "@durov",
      "channel_title": "Pavel Durov",
      "text": "🆒 In case you missed it...",
      "date": "2025-06-07T17:00:00Z",
      "views": 1000,
      "forwards": 5,
      "replies": 2,
      "url": "https://t.me/durov/123",
      "media_type": "text",
      "categories": [
        {
          "id": 1,
          "name": "Технологии",
          "ai_prompt": "Фильтруй посты о технологиях..."
        }
      ]
    }
  ]
}
```

---

## 4. N8N Processing

### 4.1 Текущий workflow (Stage 2)

**Этапы обработки:**
1. **Receive Posts** - получение данных от userbot
2. **Process & Log** - логирование и валидация  
3. **Group by Channels** - группировка по каналам
4. **AI Processing (Mock)** - базовая фильтрация по длине текста
5. **Prepare Digest** - формирование финального дайджеста
6. **Save to Backend** - отправка результата (пока mock)

### 4.2 Планируемый workflow (Stage 3)

**Дополнительные этапы:**
- **Extract Categories** - извлечение топиков из постов
- **AI Category Filter** - фильтрация по топикам через LLM
- **Generate Summaries** - создание кратких описаний
- **Multilingual Processing** - обработка мультиязычности

---

## 5. N8N → Backend API

### 5.1 Текущий формат (Mock)

```json
{
  "success": true,
  "digest_id": "digest_1701970800000",
  "message": "Digest saved with 15 posts from 2 channels",
  "timestamp": "2025-06-07T18:30:00Z"
}
```

### 5.2 Планируемый формат (Stage 3)

#### POST /api/digests
**Request:**
```json
{
  "id": "digest_1701970800000",
  "created_at": "2025-06-07T18:20:00Z",
  "processed_at": "2025-06-07T18:30:00Z",
  "channels": [
    {
      "title": "Pavel Durov",
      "username": "@durov",
      "posts_count": 2,
      "posts": [
        {
          "title": "🆒 In case you missed it...",
          "url": "https://t.me/durov/123",
          "views": 1000,
          "date": "2025-06-07T17:00:00Z",
          "categories": ["Технологии"],
          "summary": "Pavel Durov announced new Telegram features..."
        }
      ]
    }
  ],
  "total_posts": 15,
  "summary": {
    "channels_processed": 2,
    "original_posts": 91,
    "filtered_posts": 15,
    "categories_found": ["Технологии", "Новости"]
  }
}
```

---

## 6. Конфигурация и настройки

### 6.1 Settings API

#### GET /api/settings?category=ai
**Response:**
```json
[
  {
    "key": "AI_MODEL",
    "value": "gpt-4",
    "value_type": "string",
    "category": "ai",
    "description": "Модель AI для обработки контента"
  },
  {
    "key": "MAX_SUMMARY_LENGTH",
    "value": "150",
    "value_type": "integer", 
    "category": "ai",
    "description": "Максимальная длина summary в символах"
  }
]
```

### 6.2 Переменные окружения

```env
# Backend API
BACKEND_API_URL=http://localhost:8000

# N8N Integration  
N8N_WEBHOOK_URL=http://localhost:5678/webhook/telegram-digest
TEST_MODE=false

# AI Configuration (Stage 3)
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4
MAX_SUMMARY_LENGTH=150
```

---

## 7. Error Handling

### 7.1 Стандартные ошибки

```json
{
  "error": "channel_not_found",
  "message": "Channel @example not found in Telegram",
  "timestamp": "2025-06-07T18:30:00Z",
  "context": {
    "channel": "@example",
    "component": "userbot"
  }
}
```

### 7.2 Fallback механизмы

- **Userbot**: fallback на каналы из .env при недоступности API
- **N8N**: возврат без обработки при ошибках AI
- **Backend**: сохранение сырых данных при ошибках обработки

---

## 8. Версионирование

**Текущая версия API**: `v1`  
**Планируемые изменения**: добавление топиков и AI обработки в Stage 3

**Обратная совместимость**: все изменения будут аддитивными, существующие поля не изменятся. 