# Data Structure Documentation

## Общая Архитектура

MorningStarBot3 использует мультитенантную архитектуру с центральной БД PostgreSQL. Ключевые компоненты:
- **posts_cache**: Централизованное хранение сырых постов из всех каналов
- **processed_data**: Мультитенантные AI результаты (привязаны к bot_id)
- **public_bots**: Конфигурация ботов
- **channels** и **categories**: Общие ресурсы, привязываемые к ботам через связи
- **config_settings**: Глобальные и AI настройки
- **llm_providers** и **llm_settings**: Настройки LLM провайдеров (пока не реализовано)

Данные обрабатываются через Backend API (FastAPI), фронтенд (React) взаимодействует с эндпоинтами.

## Таблицы БД

### public_bots
- id: Integer (PK)
- name: String (NOT NULL)
- description: Text
- status: String (default 'setup') - статусы: setup, active, paused
- bot_token: String
- welcome_message: Text
- default_language: String (default 'ru')
- max_posts_per_digest: Integer (default 10) - используется в публичном боте для ограничения постов
- max_summary_length: Integer (default 150)
- categorization_prompt: Text
- summarization_prompt: Text
- delivery_schedule: JSONB (сложное расписание доставки)
- timezone: String (default 'Europe/Moscow')
- digest_generation_time: String (default '09:00') - legacy поле, используется в публичном боте
- digest_schedule: String (default 'daily') - legacy поле, используется в публичном боте
- users_count: Integer (default 0)
- channels_count: Integer (default 0)
- topics_count: Integer (default 0)
- created_at: DateTime
- updated_at: DateTime

Связи: bot_channels, bot_categories, posts, processing_queue, metrics, ai_settings

### channels
- id: Integer (PK)
- channel_name: String (NOT NULL)
- username: String
- telegram_id: BigInteger (NOT NULL, index) - ВАЖНО: BigInteger для поддержки ID > 2,147,483,647
- title: String (NOT NULL) - отображаемое название канала
- description: Text
- is_active: Boolean (default True)
- last_parsed: DateTime - время последнего парсинга постов
- error_count: Integer (default 0) - счетчик ошибок при парсинге
- created_at: DateTime
- updated_at: DateTime

### categories
- id: Integer (PK)
- name: String (NOT NULL) - ВАЖНО: в БД поле называется "name", не "category_name"!
- description: Text
- emoji: String (default '📝') - эмодзи для отображения в UI
- is_active: Boolean (default True)
- ai_prompt: Text - дополнительные инструкции для AI
- sort_order: Integer (default 0) - порядок сортировки категорий
- created_at: DateTime
- updated_at: DateTime

### bot_channels
- id: Integer (PK)
- public_bot_id: Integer (FK public_bots)
- channel_id: Integer (FK channels)
- weight: Float (default 1.0)
- is_active: Boolean (default True)
- created_at: DateTime

### bot_categories
- id: Integer (PK)
- public_bot_id: Integer (FK public_bots)
- category_id: Integer (FK categories)
- custom_ai_instructions: Text
- weight: Float (default 1.0)
- is_active: Boolean (default True)
- created_at: DateTime

### posts_cache
- id: Integer (PK) в SQLite, BigInteger в PostgreSQL
- channel_telegram_id: BigInteger (NOT NULL, index) - ВАЖНО: BigInteger для поддержки ID > 2,147,483,647
- telegram_message_id: BigInteger (NOT NULL)
- title: Text
- content: Text
- media_urls: JSONB (PostgreSQL) / Text (SQLite)
- views: Integer (default 0)
- post_date: DateTime (NOT NULL)
- collected_at: DateTime (NOT NULL)
- userbot_metadata: JSONB (PostgreSQL) / Text (SQLite)
- retention_until: DateTime
- created_at: DateTime
- updated_at: DateTime

Примечание: поле processing_status было удалено в пользу мультитенантных статусов в processed_data
Таблица партиционирована по collected_at в PostgreSQL

### processed_data
- id: Integer (PK)
- post_id: BigInteger (NOT NULL) - ссылается на posts_cache.id
- public_bot_id: Integer (NOT NULL)
- summaries: JSONB (NOT NULL, default '{}') - формат: {"ru": "текст саммари", "en": "summary text"}
- categories: JSONB (NOT NULL, default '[]') - формат: [{"category_name": "Политика", "relevance": 0.95}]
- metrics: JSONB (NOT NULL, default '{}') - формат: {"importance": 0.8, "urgency": 0.7, "significance": 0.9}
- processed_at: DateTime
- processing_version: String (default 'v3.1')
- processing_status: String (default 'pending') - статусы: pending, processing, completed, failed
- is_categorized: Boolean (default False) - флаг завершения категоризации
- is_summarized: Boolean (default False) - флаг завершения саммаризации

Примечания:
- Уникальный индекс: (post_id, public_bot_id)
- Таблица партиционирована по public_bot_id в PostgreSQL
- НЕ содержит channel_telegram_id и telegram_message_id (используется JOIN с posts_cache)
- НЕ содержит отдельных полей для метрик (всё в JSONB)
- Foreign Keys отсутствуют из-за партиционирования

### config_settings
- id: Integer (PK)
- key: String (unique)
- value: Text
- value_type: String (default 'string')
- category: String
- description: Text
- is_editable: Boolean (default True)
- created_at: DateTime
- updated_at: DateTime

Ключевые настройки:
- ai_categorization_model: модель для категоризации (default 'gpt-4o-mini')
- ai_summarization_model: модель для суммаризации (default 'gpt-4o')
- ai_analysis_model: модель для анализа (default 'gpt-4o-mini')
- ai_categorization_max_tokens: лимит токенов (default '1000')
- ai_summarization_max_tokens: лимит токенов (default '2000')
- ai_analysis_max_tokens: лимит токенов (default '1500')
- ai_categorization_temperature: температура (default '0.3')
- ai_summarization_temperature: температура (default '0.7')
- ai_analysis_temperature: температура (default '0.5')
- ai_summarization_top_p: параметр top_p для суммаризации (default '1.0')

### llm_providers (пока не используется)
- id: Integer (PK)
- provider_name: String (unique)
- base_url: String
- api_key_env_var: String
- default_model: String
- supported_models: JSONB
- pricing_per_1k_tokens: JSONB
- is_active: Boolean (default True)
- created_at: DateTime
- updated_at: DateTime

### llm_settings (пока не используется)
- id: Integer (PK)
- public_bot_id: Integer (FK public_bots)
- llm_provider_id: Integer (FK llm_providers)
- model_name: String
- max_tokens: Integer (default 4000)
- temperature: Float (default 0.7)
- system_prompt: Text
- backup_provider_id: Integer
- is_active: Boolean (default True)
- created_at: DateTime
- updated_at: DateTime

### users (мультитенантные пользователи)
- id: Integer (PK)
- telegram_id: BigInteger (NOT NULL) - ВАЖНО: BigInteger для поддержки ID > 2,147,483,647
- first_name: String
- last_name: String
- username: String
- is_bot: Boolean (default False)
- language_code: String
- created_at: DateTime
- updated_at: DateTime

## Эндпоинты API

### Posts Cache
- GET /api/posts/cache - Получить сырые посты с пагинацией и фильтрами
- GET /api/posts/cache/count - Количество постов
- GET /api/posts/cache/size - Размер данных в МБ
- GET /api/posts/cache-with-ai - Посты с AI данными (JOIN с processed_data), фильтр по bot_id
- GET /api/posts/stats - Общая статистика постов
- GET /api/ai/multitenant-status - Статистика обработки по ботам
- POST /api/posts/cache - Создать новый пост (используется userbot)
- DELETE /api/posts/cache/{id} - Удалить пост

### Categories
- GET /api/categories - Список всех категорий
- POST /api/categories - Создать категорию
- PUT /api/categories/{id} - Обновить категорию
- DELETE /api/categories/{id} - Удалить категорию

### Public Bots
- GET /api/public-bots - Список всех ботов
- POST /api/public-bots - Создать бота
- PUT /api/public-bots/{id} - Обновить бота
- DELETE /api/public-bots/{id} - Удалить бота
- GET /api/public-bots/{id}/channels - Каналы бота
- GET /api/public-bots/{id}/categories - Категории бота
- POST /api/public-bots/{id}/channels - Добавить каналы к боту
- POST /api/public-bots/{id}/categories - Добавить категории к боту
- DELETE /api/public-bots/{id}/channels/{channel_id} - Удалить канал из бота
- DELETE /api/public-bots/{id}/categories/{category_id} - Удалить категорию из бота

### AI/LLM Settings
- GET /api/settings - Все настройки
- PUT /api/settings/{id} - Обновить настройку
- GET /api/bot-templates - Шаблоны ботов (пока не реализовано)

### AI Processing
- POST /api/ai/results/batch - Сохранить батч AI результатов
- PUT /api/ai/results/batch-status - Обновить статусы батча
- PUT /api/ai/results/sync-status - Синхронизировать статусы сервисов
- POST /api/ai/clear-results - Очистить AI результаты
- POST /api/ai/reprocess-all - Перезапустить обработку

## Фронтенд Использование

### Posts Cache Monitor
- **RAW POSTS таб**: 
  - Отображает данные из posts_cache
  - Поля: id, channel_telegram_id, content, media_urls, views, post_date
  - Фильтры: по каналу, дате, тексту
  - Сортировка: по дате, просмотрам
  
- **AI RESULTS таб**: 
  - Отображает данные из posts_cache + processed_data (LEFT JOIN)
  - Дополнительные поля: summaries, categories, metrics, processing_status
  - Фильтр по bot_id для мультитенантности
  - Статистика по ботам из /api/ai/multitenant-status

### Categories
- Список: отображает id, name, description, is_active
- Редактирование: 
  - Фронтенд использует поле "name", но отправляет как "category_name" в API
  - Backend трансформирует обратно в "name" для БД
  - Поля emoji и sort_order только во фронтенде

### Public Bots
- Список: id, name, status, channels_count, categories_count
- Редактирование через табы:
  - General: основные настройки (name, token, welcome_message)
  - Channels: управление связанными каналами
  - Categories: управление связанными категориями  
  - AI Settings: промпты для категоризации и суммаризации
  - Delivery: расписание доставки (JSONB структура)

### AI и LLM Настройки
- Загружает настройки из config_settings через /api/settings
- Группирует по сервисам: categorization, summarization, analysis
- Пока использует mock данные для стоимости и сравнения моделей
- В будущем будет использовать llm_providers и llm_settings

## Важные особенности

1. **Мультитенантность**: Один пост может быть обработан разными ботами с разными результатами
2. **Партиционирование**: posts_cache по collected_at, processed_data по public_bot_id
3. **JSONB поля**: В PostgreSQL используется JSONB, в SQLite - Text с JSON строками
4. **BigInteger**: Telegram ID всегда BigInteger из-за больших значений (может быть > 2,147,483,647)
5. **Трансформация полей**: Фронтенд и бэкенд могут использовать разные имена (name vs category_name)
6. **Legacy поля**: Некоторые поля сохранены для обратной совместимости
7. **Нормализация**: Данные о каналах и сообщениях НЕ дублируются в processed_data, используется JOIN
8. **Boolean флаги**: is_categorized и is_summarized для отслеживания прогресса обработки
9. **Foreign Keys**: Отсутствуют в партиционированных таблицах из-за ограничений PostgreSQL 