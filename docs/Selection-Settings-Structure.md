# Selection Settings Structure - MorningStarBot3

## 📋 Обзор

Структура настроек выборки и критериев фильтрации контента для **Stage 2-3: N8N Integration & AI Processing**.

---

## 1. Settings API Structure

### 1.1 Общие настройки системы

#### GET /api/settings
**Response:**
```json
[
  {
    "id": 1,
    "key": "DIGEST_GENERATION_TIME",
    "value": "18:00",
    "value_type": "time",
    "category": "system",
    "description": "Время генерации дайджеста (UTC)",
    "is_editable": true
  },
  {
    "id": 2,
    "key": "MAX_POSTS_PER_DIGEST",
    "value": "20",
    "value_type": "integer",
    "category": "system", 
    "description": "Максимальное количество постов в дайджесте",
    "is_editable": true
  },
  {
    "id": 3,
    "key": "COLLECTION_LOOKBACK_HOURS",
    "value": "24",
    "value_type": "integer",
    "category": "collection",
    "description": "Глубина сбора постов в часах",
    "is_editable": true
  }
]
```

### 1.2 AI настройки (Stage 3)

```json
[
  {
    "key": "AI_PROVIDER",
    "value": "openai",
    "value_type": "select",
    "category": "ai",
    "options": ["openai", "anthropic", "local"],
    "description": "Провайдер AI для обработки контента"
  },
  {
    "key": "AI_MODEL",
    "value": "gpt-4",
    "value_type": "string",
    "category": "ai",
    "description": "Модель AI"
  },
  {
    "key": "MIN_POST_LENGTH",
    "value": "50",
    "value_type": "integer",
    "category": "filtering",
    "description": "Минимальная длина поста для обработки"
  },
  {
    "key": "SUMMARY_LENGTH",
    "value": "150",
    "value_type": "integer",
    "category": "ai",
    "description": "Максимальная длина summary в символах"
  }
]
```

---

## 2. Channel-Specific Settings

### 2.1 Настройки канала

#### Channel Model расширение:
```json
{
  "id": 1,
  "telegram_id": 1001006503122,
  "username": "durov",
  "title": "Pavel Durov",
  "is_active": true,
  "categories": [...],
  "settings": {
    "priority": "high",
    "min_views": 1000,
    "include_forwards": false,
    "language_filter": ["ru", "en"],
    "ai_processing": {
      "enabled": true,
      "summarize": true,
      "translate": false,
      "target_language": "ru"
    }
  }
}
```

### 2.2 Приоритеты каналов

```json
{
  "priority_levels": {
    "high": {
      "weight": 3,
      "min_posts_guaranteed": 3,
      "description": "Обязательно включать в дайджест"
    },
    "medium": {
      "weight": 2,
      "min_posts_guaranteed": 1,
      "description": "Включать если есть место"
    },
    "low": {
      "weight": 1,
      "min_posts_guaranteed": 0,
      "description": "Включать только лучшие посты"
    }
  }
}
```

---

## 3. Content Filtering Criteria

### 3.1 Базовые фильтры (Stage 2)

```json
{
  "basic_filters": {
    "min_text_length": 50,
    "max_text_length": 5000,
    "min_views": 100,
    "exclude_forwarded": false,
    "exclude_media_only": true,
    "time_window_hours": 24
  }
}
```

### 3.2 AI фильтры (Stage 3)

```json
{
  "ai_filters": {
    "content_quality": {
      "enabled": true,
      "threshold": 0.7,
      "criteria": ["informativeness", "relevance", "uniqueness"]
    },
    "category_matching": {
      "enabled": true,
      "strict_mode": false,
      "confidence_threshold": 0.6
    },
    "sentiment_filter": {
      "enabled": false,
      "exclude_negative": false,
      "min_neutrality": 0.3
    },
    "duplicate_detection": {
      "enabled": true,
      "similarity_threshold": 0.8,
      "method": "semantic"
    }
  }
}
```

---

## 4. Category-Based Processing

### 4.1 Категории с AI промптами

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Технологии",
      "emoji": "💻",
      "ai_prompt": "Фильтруй посты о новых технологиях, стартапах, IT-новостях, программировании. Исключи рекламные посты и мемы.",
      "settings": {
        "priority": "high",
        "min_posts": 2,
        "max_posts": 5,
        "require_summary": true
      }
    },
    {
      "id": 2,
      "name": "Новости",
      "emoji": "📰",
      "ai_prompt": "Важные новости дня: политика, экономика, социальные события. Фокус на фактах, исключи слухи и спекуляции.",
      "settings": {
        "priority": "medium",
        "min_posts": 1,
        "max_posts": 3,
        "require_summary": true
      }
    }
  ]
}
```

### 4.2 Обработка по категориям в N8N

```javascript
// Псевдокод N8N ноды "Category Processing"
const processCategories = (posts) => {
  const categorized = {};
  
  for (const post of posts) {
    for (const category of post.categories) {
      if (!categorized[category.id]) {
        categorized[category.id] = {
          category: category,
          posts: [],
          settings: category.settings
        };
      }
      
      // AI фильтрация по промпту категории
      if (shouldIncludePost(post, category.ai_prompt)) {
        categorized[category.id].posts.push(post);
      }
    }
  }
  
  return categorized;
};
```

---

## 5. User Preferences (Будущее)

### 5.1 Персональные настройки

```json
{
  "user_preferences": {
    "user_id": 123,
    "language": "ru",
    "timezone": "Europe/Moscow",
    "digest_format": "html",
    "categories": {
      "enabled": [1, 2, 3],
      "priorities": {
        "1": "high",
        "2": "medium", 
        "3": "low"
      }
    },
    "content_settings": {
      "max_posts": 15,
      "include_summaries": true,
      "include_translations": false,
      "exclude_duplicates": true
    }
  }
}
```

---

## 6. N8N Configuration Variables

### 6.1 Environment Variables для N8N

```env
# Processing Settings
MAX_POSTS_PER_DIGEST=20
MIN_POST_LENGTH=50
COLLECTION_HOURS=24

# AI Settings (Stage 3)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
AI_MODEL=gpt-4
SUMMARY_MAX_LENGTH=150

# Quality Thresholds
MIN_VIEWS_THRESHOLD=100
QUALITY_THRESHOLD=0.7
SIMILARITY_THRESHOLD=0.8
```

### 6.2 N8N Workflow Variables

```json
{
  "workflow_settings": {
    "processing": {
      "batch_size": 50,
      "timeout_seconds": 300,
      "retry_attempts": 3
    },
    "ai": {
      "parallel_requests": 5,
      "cache_results": true,
      "fallback_enabled": true
    },
    "output": {
      "format": "structured",
      "include_metadata": true,
      "compress_large_payloads": true
    }
  }
}
```

---

## 7. Processing Flow Configuration

### 7.1 Stage 2 Flow (Текущий)

```yaml
processing_stages:
  1_receive:
    description: "Получение данных от userbot"
    timeout: 30s
    
  2_validate:
    description: "Валидация и логирование"
    required_fields: ["posts", "timestamp"]
    
  3_basic_filter:
    description: "Базовая фильтрация"
    filters: ["length", "views", "time"]
    
  4_group:
    description: "Группировка по каналам"
    sort_by: "views"
    
  5_mock_ai:
    description: "Mock AI обработка"
    enabled: true
    
  6_prepare:
    description: "Подготовка финального дайджеста"
    max_posts: 20
    
  7_save:
    description: "Сохранение (mock)"
    endpoint: "http://localhost:8000/api/digests"
```

### 7.2 Stage 3 Flow (Планируемый)

```yaml
processing_stages:
  1_receive: {...}
  2_validate: {...}
  
  3_category_extract:
    description: "Извлечение категорий из постов"
    ai_enabled: true
    
  4_ai_filter:
    description: "AI фильтрация по категориям"
    model: "gpt-4"
    parallel: true
    
  5_quality_score:
    description: "Оценка качества контента"
    criteria: ["info", "relevance", "uniqueness"]
    
  6_summarize:
    description: "Генерация summary"
    max_length: 150
    
  7_deduplicate:
    description: "Удаление дубликатов"
    method: "semantic"
    
  8_prioritize:
    description: "Приоритизация по настройкам"
    max_posts: 20
    
  9_save:
    description: "Сохранение в Backend"
    format: "structured"
```

---

## 8. Error Handling & Fallbacks

### 8.1 Fallback стратегии

```json
{
  "fallback_strategies": {
    "ai_processing_failure": {
      "action": "use_basic_filters",
      "filters": ["length", "views", "recency"]
    },
    "category_assignment_failure": {
      "action": "assign_default",
      "default_category": "Разное"
    },
    "api_unavailable": {
      "action": "save_raw_data",
      "retry_later": true
    }
  }
}
```

---

## 9. Performance & Scaling

### 9.1 Оптимизация

```json
{
  "performance": {
    "caching": {
      "ai_results": "1h",
      "channel_settings": "30m", 
      "categories": "1h"
    },
    "batching": {
      "ai_requests": 10,
      "database_writes": 50
    },
    "timeouts": {
      "ai_processing": "60s",
      "total_workflow": "300s"
    }
  }
}
```

---

## 10. Implementation Plan

### 10.1 Stage 2 (Текущий этап)
- [x] Базовые настройки в environment variables
- [ ] Settings API endpoint в Backend  
- [ ] Чтение настроек в N8N workflow
- [ ] Конфигурируемые базовые фильтры

### 10.2 Stage 3 (AI Processing)
- [ ] AI provider интеграция
- [ ] Category-based AI фильтрация
- [ ] Качественная оценка контента
- [ ] Персональные предпочтения пользователей 