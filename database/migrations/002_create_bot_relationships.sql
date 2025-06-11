-- Migration 002: Create bot_channels and bot_categories tables
-- Many-to-Many связи между ботами, каналами и категориями

-- Таблица каналов (встроенная в multi-tenant схему)
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    channel_name VARCHAR(255) NOT NULL,
    channel_username VARCHAR(100),
    telegram_id BIGINT UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица категорий (встроенная в multi-tenant схему)
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Таблица связей бот-канал
CREATE TABLE IF NOT EXISTS bot_channels (
    id SERIAL PRIMARY KEY,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    weight FLOAT DEFAULT 1.0, -- Приоритет канала для данного бота (0.1-2.0)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(public_bot_id, channel_id)
);

-- Таблица связей бот-категория
CREATE TABLE IF NOT EXISTS bot_categories (
    id SERIAL PRIMARY KEY,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    custom_ai_instructions TEXT, -- Специфические AI инструкции для категории в этом боте
    weight FLOAT DEFAULT 1.0, -- Приоритет категории для данного бота
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(public_bot_id, category_id)
);

-- Индексы для channels
CREATE INDEX IF NOT EXISTS idx_channels_telegram_id ON channels(telegram_id);
CREATE INDEX IF NOT EXISTS idx_channels_username ON channels(channel_username);
CREATE INDEX IF NOT EXISTS idx_channels_active ON channels(is_active);

-- Индексы для categories  
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(category_name);
CREATE INDEX IF NOT EXISTS idx_categories_active ON categories(is_active);

-- Индексы для bot_channels
CREATE INDEX IF NOT EXISTS idx_bot_channels_bot_id ON bot_channels(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_channels_channel_id ON bot_channels(channel_id);
CREATE INDEX IF NOT EXISTS idx_bot_channels_active ON bot_channels(public_bot_id, is_active);
CREATE INDEX IF NOT EXISTS idx_bot_channels_weight ON bot_channels(public_bot_id, weight DESC);

-- Индексы для bot_categories
CREATE INDEX IF NOT EXISTS idx_bot_categories_bot_id ON bot_categories(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_categories_category_id ON bot_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_bot_categories_active ON bot_categories(public_bot_id, is_active);
CREATE INDEX IF NOT EXISTS idx_bot_categories_weight ON bot_categories(public_bot_id, weight DESC);

-- Комментарии к таблицам
COMMENT ON TABLE bot_channels IS 'Many-to-Many связи между публичными ботами и каналами';
COMMENT ON TABLE bot_categories IS 'Many-to-Many связи между публичными ботами и категориями';

COMMENT ON COLUMN bot_channels.weight IS 'Приоритет канала для бота: 0.1=низкий, 1.0=нормальный, 2.0=высокий';
COMMENT ON COLUMN bot_categories.weight IS 'Приоритет категории для бота: 0.1=низкий, 1.0=нормальный, 2.0=высокий';
COMMENT ON COLUMN bot_categories.custom_ai_instructions IS 'Кастомные AI инструкции для данной категории в контексте конкретного бота'; 