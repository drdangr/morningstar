-- Docker-compatible PostgreSQL Migration Script
-- Выполняет все миграции для MorningStarBot3

BEGIN;

-- Создаем таблицу для отслеживания миграций
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_name VARCHAR(255) PRIMARY KEY,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
);

-- Функция для логирования миграций
CREATE OR REPLACE FUNCTION log_migration(p_migration_name VARCHAR(255))
RETURNS VOID AS $$
BEGIN
    INSERT INTO schema_migrations (migration_name, checksum)
    VALUES (p_migration_name, 'docker_migration')
    ON CONFLICT (migration_name) DO NOTHING;
    
    RAISE NOTICE 'Migration executed: %', p_migration_name;
END;
$$ LANGUAGE plpgsql;

-- Migration 001: Public Bots (инлайн)
\echo 'Executing Migration 001: Create public_bots table...'

CREATE TABLE IF NOT EXISTS public_bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    bot_token VARCHAR(100) NOT NULL UNIQUE,
    welcome_message TEXT DEFAULT 'Привет! Добро пожаловать в MorningStarBot3!',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration 002: Bot Relationships (инлайн)
\echo 'Executing Migration 002: Create bot relationships tables...'

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    channel_name VARCHAR(100) NOT NULL,
    telegram_id BIGINT UNIQUE,
    url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration 003: Posts Cache (упрощенная версия)
\echo 'Executing Migration 003: Create posts_cache table...'

CREATE TABLE IF NOT EXISTS posts_cache (
    id SERIAL PRIMARY KEY,
    channel_telegram_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_telegram_id, message_id)
);

-- Migration 004: Processed Data
\echo 'Executing Migration 004: Create processed_data table...'

CREATE TABLE IF NOT EXISTS processed_data (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES posts_cache(id),
    public_bot_id INTEGER REFERENCES public_bots(id),
    category_id INTEGER REFERENCES categories(id),
    summary TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_published BOOLEAN DEFAULT false
);

-- Migration 005: Users (упрощенная версия)
\echo 'Executing Migration 005: Create users table...'

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'ru',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migration 006: Config Settings
\echo 'Executing Migration 006: Create config_settings table...'

CREATE TABLE IF NOT EXISTS config_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем базовые настройки
INSERT INTO config_settings (key, value, description, category) VALUES
('ai_model', 'gpt-4o-mini', 'AI модель для обработки', 'ai'),
('max_tokens', '150', 'Максимальное количество токенов', 'ai'),
('temperature', '0.7', 'Температура для AI', 'ai'),
('system_prompt', 'Ты помощник для создания дайджестов новостей', 'Системный промпт', 'ai')
ON CONFLICT (key) DO NOTHING;

-- Добавляем базовые категории
INSERT INTO categories (name, description) VALUES
('Технологии', 'Новости о технологиях'),
('Политика', 'Политические новости'),
('Экономика', 'Экономические новости'),
('Общие', 'Общие новости')
ON CONFLICT (name) DO NOTHING;

-- Логируем выполнение миграций
SELECT log_migration('001_create_public_bots');
SELECT log_migration('002_create_bot_relationships');
SELECT log_migration('003_create_posts_cache');
SELECT log_migration('004_create_processed_data');
SELECT log_migration('005_create_users');
SELECT log_migration('006_create_config_settings');

COMMIT;

-- Успешное завершение
\echo 'All migrations completed successfully!' 