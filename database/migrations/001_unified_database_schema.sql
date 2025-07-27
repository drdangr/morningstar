-- =====================================================
-- UNIFIED DATABASE SCHEMA для MorningStarBot3
-- =====================================================
-- Объединяет все миграции 001-015 в единую чистую схему
-- Создано: 27 июля 2025
-- Источник: анализ всех миграций и schemas.py

-- Включаем расширения
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

BEGIN;

-- =====================================================
-- 1. СИСТЕМА ОТСЛЕЖИВАНИЯ МИГРАЦИЙ
-- =====================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_name VARCHAR(255) PRIMARY KEY,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    description TEXT
);

-- Функция для логирования миграций
CREATE OR REPLACE FUNCTION log_migration(p_migration_name VARCHAR(255), p_description TEXT DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO schema_migrations (migration_name, checksum, description)
    VALUES (p_migration_name, 'unified_schema_v1', p_description)
    ON CONFLICT (migration_name) DO NOTHING;
    
    RAISE NOTICE 'Migration executed: % - %', p_migration_name, COALESCE(p_description, 'Unified schema');
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. ОСНОВНЫЕ СПРАВОЧНИКИ
-- =====================================================

-- Категории контента
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    emoji VARCHAR(10) DEFAULT '📝',
    is_active BOOLEAN DEFAULT true,
    ai_prompt TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_categories_sort_order ON categories(sort_order);

-- Telegram каналы
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    channel_name VARCHAR(100) NOT NULL,
    username VARCHAR(100),  -- без @
    telegram_id BIGINT UNIQUE,  -- BIGINT для больших ID
    title VARCHAR(255),  -- может быть NULL для существующих каналов
    url VARCHAR(255),
    description TEXT,
    last_parsed TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_channels_telegram_id ON channels(telegram_id) WHERE telegram_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_channels_active ON channels(is_active);
CREATE INDEX IF NOT EXISTS idx_channels_username ON channels(username);
CREATE INDEX IF NOT EXISTS idx_channels_last_parsed ON channels(last_parsed);
CREATE INDEX IF NOT EXISTS idx_channels_error_count ON channels(error_count);

-- Связи каналов и категорий (многие ко многим)
CREATE TABLE IF NOT EXISTS channel_categories (
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id, category_id)
);

-- =====================================================
-- 3. ПУБЛИЧНЫЕ БОТЫ И КОНФИГУРАЦИЯ
-- =====================================================

-- Публичные боты (мультитенантность)
CREATE TABLE IF NOT EXISTS public_bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    bot_token VARCHAR(100) NOT NULL UNIQUE,
    bot_username VARCHAR(100),  -- автоматически из Telegram API
    welcome_message TEXT DEFAULT 'Привет! Добро пожаловать в MorningStarBot3!',
    status VARCHAR(20) DEFAULT 'active',  -- enum: active, inactive, maintenance
    
    -- Legacy compatibility fields (до STAGE 4)
    default_language VARCHAR(10) DEFAULT 'ru',
    max_posts_per_digest INTEGER DEFAULT 50,
    max_summary_length INTEGER DEFAULT 500,
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    digest_generation_time VARCHAR(5) DEFAULT '09:00',
    digest_schedule JSONB DEFAULT '{"enabled": false}'::jsonb,
    users_count INTEGER DEFAULT 0,
    digests_count INTEGER DEFAULT 0,
    channels_count INTEGER DEFAULT 0,
    topics_count INTEGER DEFAULT 0,
    
    -- New unified fields
    delivery_schedule JSONB DEFAULT '{"enabled": false}'::jsonb,
    categorization_prompt TEXT,
    summarization_prompt TEXT,
    ai_settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_bot_status CHECK (status IN ('setup', 'active', 'paused', 'development'))
);

CREATE INDEX IF NOT EXISTS idx_public_bots_status ON public_bots(status);
CREATE INDEX IF NOT EXISTS idx_public_bots_username ON public_bots(bot_username);

-- Связи ботов и каналов (многие ко многим)
CREATE TABLE IF NOT EXISTS bot_channels (
    id SERIAL PRIMARY KEY,
    public_bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    weight FLOAT DEFAULT 1.0,  -- Приоритет канала для данного бота (0.1-2.0)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_bot_channel UNIQUE (public_bot_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_bot_channels_bot_id ON bot_channels(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_channels_channel_id ON bot_channels(channel_id);
CREATE INDEX IF NOT EXISTS idx_bot_channels_is_active ON bot_channels(is_active);

-- Связи ботов и категорий (многие ко многим)
CREATE TABLE IF NOT EXISTS bot_categories (
    id SERIAL PRIMARY KEY,
    public_bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    custom_ai_instructions TEXT,  -- Специфические AI инструкции для категории в этом боте
    weight FLOAT DEFAULT 1.0,  -- Приоритет категории для данного бота
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_bot_category UNIQUE (public_bot_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_bot_categories_bot_id ON bot_categories(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_categories_category_id ON bot_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_bot_categories_is_active ON bot_categories(is_active);

-- =====================================================
-- 4. ПОЛЬЗОВАТЕЛИ И ПОДПИСКИ
-- =====================================================

-- Пользователи системы
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,  -- BIGINT для больших ID
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'ru',
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Подписки пользователей на категории (мультитенантные)
CREATE TABLE IF NOT EXISTS user_category_subscriptions (
    user_telegram_id BIGINT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    public_bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_telegram_id, category_id, public_bot_id)
);

CREATE INDEX IF NOT EXISTS idx_user_cat_subs_user ON user_category_subscriptions(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_user_cat_subs_bot ON user_category_subscriptions(public_bot_id);

-- Подписки пользователей на каналы (мультитенантные)
CREATE TABLE IF NOT EXISTS user_channel_subscriptions (
    user_telegram_id BIGINT NOT NULL,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    public_bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_telegram_id, channel_id, public_bot_id)
);

CREATE INDEX IF NOT EXISTS idx_user_ch_subs_user ON user_channel_subscriptions(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_user_ch_subs_bot ON user_channel_subscriptions(public_bot_id);

-- Legacy подписки пользователей (простая связь - для Backend совместимости)
CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, category_id)
);

-- =====================================================
-- 5. КЭШИРОВАНИЕ ПОСТОВ (основное хранилище)
-- =====================================================

-- Кэш постов от userbot (единый пул всех постов)
CREATE TABLE IF NOT EXISTS posts_cache (
    id SERIAL PRIMARY KEY,
    channel_telegram_id BIGINT NOT NULL,  -- BIGINT для больших ID
    telegram_message_id BIGINT NOT NULL,  -- BIGINT для больших ID
    title TEXT,
    content TEXT,
    media_urls JSONB DEFAULT '[]'::jsonb,  -- List[str] в JSONB
    views INTEGER DEFAULT 0,
    post_date TIMESTAMP NOT NULL,  -- используем post_date, НЕ published_at
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    userbot_metadata JSONB DEFAULT '{}'::jsonb,
    retention_until TIMESTAMP,  -- Время до которого хранить пост
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT uq_posts_cache_channel_message UNIQUE (channel_telegram_id, telegram_message_id)
);

-- Критически важные индексы для производительности
CREATE INDEX IF NOT EXISTS idx_posts_cache_channel_date ON posts_cache(channel_telegram_id, post_date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_cache_date ON posts_cache(post_date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_cache_collected ON posts_cache(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_cache_content_search ON posts_cache USING gin(to_tsvector('russian', COALESCE(title, '') || ' ' || COALESCE(content, '')));
CREATE INDEX IF NOT EXISTS idx_posts_cache_retention ON posts_cache(retention_until) WHERE retention_until IS NOT NULL;

-- Недостающие индексы из документации:
CREATE INDEX IF NOT EXISTS idx_posts_cache_telegram_id ON posts_cache(channel_telegram_id, telegram_message_id);
CREATE INDEX IF NOT EXISTS idx_posts_cache_metadata_gin ON posts_cache USING gin(userbot_metadata);
CREATE INDEX IF NOT EXISTS idx_posts_cache_media_gin ON posts_cache USING gin(media_urls);

-- =====================================================
-- 6. AI ОБРАБОТКА ПОСТОВ (мультитенантная)
-- =====================================================

-- Основные результаты AI обработки (по ботам)
CREATE TABLE IF NOT EXISTS processed_data (
    id SERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts_cache(id) ON DELETE CASCADE,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    
    -- AI результаты в JSONB
    summaries JSONB DEFAULT '{}'::jsonb,
    categories JSONB DEFAULT '{}'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb,
    
    -- Статусы обработки
    processing_status VARCHAR(32) DEFAULT 'pending',
    is_categorized BOOLEAN DEFAULT FALSE,
    is_summarized BOOLEAN DEFAULT FALSE,
    
    -- Метаинформация
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_version VARCHAR(50) DEFAULT 'v2.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Уникальность: один пост - один бот - одна запись
    CONSTRAINT uq_processed_post_bot UNIQUE (post_id, public_bot_id),
    CONSTRAINT chk_processing_status CHECK (processing_status IN ('not_found', 'pending', 'processing', 'completed', 'failed'))
);

-- Индексы для AI обработки
CREATE INDEX IF NOT EXISTS idx_processed_data_post_id ON processed_data(post_id);
CREATE INDEX IF NOT EXISTS idx_processed_data_bot_id ON processed_data(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_processed_data_status ON processed_data(processing_status);
CREATE INDEX IF NOT EXISTS idx_processed_data_flags ON processed_data(public_bot_id, is_categorized, is_summarized);
CREATE INDEX IF NOT EXISTS idx_processed_data_processed_at ON processed_data(processed_at DESC);

-- КРИТИЧЕСКИЕ недостающие индексы из документации:
CREATE INDEX IF NOT EXISTS idx_processed_data_post_bot ON processed_data(post_id, public_bot_id);
CREATE INDEX IF NOT EXISTS idx_processed_data_bot_status ON processed_data(public_bot_id, processing_status);
CREATE INDEX IF NOT EXISTS idx_processed_data_is_categorized ON processed_data(is_categorized);
CREATE INDEX IF NOT EXISTS idx_processed_data_is_summarized ON processed_data(is_summarized);
CREATE INDEX IF NOT EXISTS idx_processed_data_version ON processed_data(processing_version);

-- Детальные результаты AI сервисов (новая архитектура)
CREATE TABLE IF NOT EXISTS processed_service_results (
    id SERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL,
    public_bot_id INTEGER NOT NULL,
    service_name VARCHAR(64) NOT NULL,  -- 'categorization', 'summarization', 'analysis'
    status VARCHAR(32) DEFAULT 'success',  -- 'success', 'failed', 'partial'
    payload JSONB NOT NULL DEFAULT '{}',   -- результат сервиса
    metrics JSONB NOT NULL DEFAULT '{}',   -- метрики производительности
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT uq_service_result UNIQUE (post_id, public_bot_id, service_name)
);

CREATE INDEX IF NOT EXISTS idx_psr_post_bot_service ON processed_service_results (post_id, public_bot_id, service_name);
CREATE INDEX IF NOT EXISTS idx_psr_service_status ON processed_service_results (service_name, status);
CREATE INDEX IF NOT EXISTS idx_psr_processed_at ON processed_service_results (processed_at DESC);

-- =====================================================
-- 7. СИСТЕМНЫЕ НАСТРОЙКИ
-- =====================================================

-- Глобальные настройки системы
CREATE TABLE IF NOT EXISTS config_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    value_type VARCHAR(20) DEFAULT 'string',  -- string, integer, float, boolean, json
    is_editable BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_config_settings_category ON config_settings(category);
CREATE INDEX IF NOT EXISTS idx_config_settings_active ON config_settings(is_active);
CREATE INDEX IF NOT EXISTS idx_config_settings_editable ON config_settings(is_editable);

-- LLM провайдеры
CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    api_base_url VARCHAR(255),
    provider_type VARCHAR(50) NOT NULL,  -- 'openai', 'anthropic', 'local'
    is_active BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM настройки
CREATE TABLE IF NOT EXISTS llm_settings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    llm_provider_id INTEGER REFERENCES llm_providers(id),
    model_name VARCHAR(100) NOT NULL,
    max_tokens INTEGER DEFAULT 1000,
    temperature DECIMAL(3,2) DEFAULT 0.70,
    top_p DECIMAL(3,2) DEFAULT 1.00,
    system_prompt TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI настройки (шаблоны)
CREATE TABLE IF NOT EXISTS ai_settings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    service_type VARCHAR(50) NOT NULL,  -- 'categorization', 'summarization', 'analysis'
    llm_setting_id INTEGER REFERENCES llm_settings(id),
    prompt_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 8. ДАЙДЖЕСТЫ (N8N ИНТЕГРАЦИЯ)
-- =====================================================

-- Таблица дайджестов от N8N workflow
CREATE TABLE IF NOT EXISTS digests (
    id SERIAL PRIMARY KEY,
    digest_id VARCHAR(255) UNIQUE NOT NULL,  -- timestamp от N8N
    total_posts INTEGER DEFAULT 0,
    channels_processed INTEGER DEFAULT 0,
    original_posts INTEGER DEFAULT 0,
    relevant_posts INTEGER DEFAULT 0,
    avg_importance FLOAT DEFAULT 0.0,
    avg_urgency FLOAT DEFAULT 0.0,
    avg_significance FLOAT DEFAULT 0.0,
    binary_relevance_applied BOOLEAN DEFAULT FALSE,
    with_metrics BOOLEAN DEFAULT FALSE,
    digest_data TEXT,  -- JSON данные полного дайджеста
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_digests_digest_id ON digests(digest_id);
CREATE INDEX IF NOT EXISTS idx_digests_processed_at ON digests(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_digests_created_at ON digests(created_at DESC);

-- =====================================================
-- 9. ЗАПОЛНЕНИЕ БАЗОВЫХ ДАННЫХ
-- =====================================================

-- Базовые категории
INSERT INTO categories (name, description) VALUES
('Технологии', 'Новости о технологиях и IT'),
('Политика', 'Политические новости и события'),
('Экономика', 'Экономические новости и аналитика'),
('Общие', 'Общие новости и события'),
('Война', 'Военные действия и конфликты'),
('Украина', 'Новости о Украине'),
('США', 'Новости из США'),
('Культура', 'Культурные события и новости'),
('Спорт', 'Спортивные новости')
ON CONFLICT (name) DO NOTHING;

-- Базовые системные настройки
INSERT INTO config_settings (key, value, description, category, value_type) VALUES
-- AI Models
('ai_categorization_model', 'gpt-4o-mini', 'AI модель для категоризации', 'ai', 'string'),
('ai_summarization_model', 'gpt-4o', 'AI модель для саммаризации', 'ai', 'string'),
('ai_analysis_model', 'gpt-4o-mini', 'AI модель для анализа', 'ai', 'string'),

-- Max Tokens
('ai_categorization_max_tokens', '1000', 'Максимальные токены для категоризации', 'ai', 'integer'),
('ai_summarization_max_tokens', '2000', 'Максимальные токены для саммаризации', 'ai', 'integer'),
('ai_analysis_max_tokens', '1500', 'Максимальные токены для анализа', 'ai', 'integer'),

-- Temperature
('ai_categorization_temperature', '0.3', 'Температура для категоризации', 'ai', 'float'),
('ai_summarization_temperature', '0.7', 'Температура для саммаризации', 'ai', 'float'),
('ai_analysis_temperature', '0.5', 'Температура для анализа', 'ai', 'float'),

-- System
('collection_depth_days', '3', 'Глубина сбора постов в днях', 'system', 'integer'),
('max_posts_per_digest', '50', 'Максимум постов в дайджесте', 'system', 'integer'),
('digest_delivery_time', '09:00', 'Время доставки дайджестов', 'system', 'string'),

-- DEFAULT_ настройки для шаблонов ботов (КРИТИЧЕСКИ ВАЖНО для создания ботов!)
('DEFAULT_AI_MODEL', 'gpt-4o-mini', 'AI модель по умолчанию для новых ботов', 'template', 'string'),
('DEFAULT_MAX_TOKENS', '4000', 'Максимум токенов по умолчанию', 'template', 'integer'),
('DEFAULT_TEMPERATURE', '0.7', 'Температура по умолчанию', 'template', 'float'),
('DEFAULT_CATEGORIZATION_PROMPT', 'Анализируй посты по следующим категориям:\n1. НОВОСТИ - политические события, экономика, общественные новости\n2. ТЕХНОЛОГИИ - IT, гаджеты, научные открытия\n3. КУЛЬТУРА - искусство, развлечения, спорт\n4. ВОЙНА - военные действия, конфликты, оборона\n\nОпредели наиболее подходящую категорию для каждого поста.', 'Промпт категоризации по умолчанию', 'template', 'string'),
('DEFAULT_SUMMARIZATION_PROMPT', 'Создавай краткие резюме постов:\n- Максимум 2-3 предложения\n- Фокус на ключевых фактах\n- Нейтральный тон без эмоций\n- Указывай источник если важно', 'Промпт саммаризации по умолчанию', 'template', 'string'),
('DEFAULT_MAX_POSTS_PER_DIGEST', '10', 'Максимум постов в дайджесте по умолчанию', 'template', 'integer'),
('DEFAULT_MAX_SUMMARY_LENGTH', '150', 'Максимальная длина резюме по умолчанию', 'template', 'integer'),
('DEFAULT_DIGEST_LANGUAGE', 'ru', 'Язык дайджестов по умолчанию', 'template', 'string'),
('DEFAULT_WELCOME_MESSAGE', '🤖 Добро пожаловать! Этот бот будет присылать вам персонализированные дайджесты новостей.', 'Приветственное сообщение по умолчанию', 'template', 'string'),
('DEFAULT_DELIVERY_SCHEDULE', '{"monday": ["08:00", "19:00"], "tuesday": ["08:00", "19:00"], "wednesday": ["08:00", "19:00"], "thursday": ["08:00", "19:00"], "friday": ["08:00", "19:00"], "saturday": ["10:00"], "sunday": ["10:00"]}', 'Расписание доставки по умолчанию', 'template', 'json'),
('DEFAULT_TIMEZONE', 'Europe/Moscow', 'Часовой пояс по умолчанию', 'template', 'string')
ON CONFLICT (key) DO NOTHING;

-- =====================================================
-- 10. ЛОГИРОВАНИЕ И ЗАВЕРШЕНИЕ
-- =====================================================

-- Логируем создание unified схемы
SELECT log_migration('001_unified_database_schema', 'Complete unified database schema with Backend compatibility - все миграции объединены + legacy поля для совместимости с Backend');

COMMIT;

-- Успешное завершение
\echo '🎉 UNIFIED DATABASE SCHEMA CREATED SUCCESSFULLY!'
\echo '✅ Все таблицы созданы'
\echo '✅ Индексы настроены' 
\echo '✅ Базовые данные заполнены'
\echo '✅ Система готова к работе' 