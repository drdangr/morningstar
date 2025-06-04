-- MorningStar Bot Database Schema
-- Version: 1.0.0

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ru',
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    emoji VARCHAR(10),
    is_active BOOLEAN DEFAULT true,
    ai_prompt TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    title VARCHAR(255),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_parsed TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Channel categories mapping
CREATE TABLE IF NOT EXISTS channel_categories (
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (channel_id, category_id)
);

-- User subscriptions
CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    frequency VARCHAR(50) DEFAULT 'daily',
    delivery_time TIME DEFAULT '09:00',
    last_delivered TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, category_id)
);

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    telegram_message_id BIGINT,
    content TEXT,
    media_type VARCHAR(50),
    media_url TEXT,
    summary TEXT,
    category_id INTEGER REFERENCES categories(id),
    posted_at TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, telegram_message_id)
);

-- Digests table
CREATE TABLE IF NOT EXISTS digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id),
    content TEXT,
    posts_included INTEGER[],
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_posts_channel_posted ON posts(channel_id, posted_at DESC);
CREATE INDEX idx_posts_category_posted ON posts(category_id, posted_at DESC);
CREATE INDEX idx_digests_user_delivered ON digests(user_id, delivered_at DESC);
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_channels_telegram_id ON channels(telegram_id);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channels_updated_at BEFORE UPDATE ON channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default categories
INSERT INTO categories (name, description, emoji, ai_prompt) VALUES
    ('Технологии', 'Новости IT, программирование, AI', '💻', 'Создай краткое резюме технических новостей, выдели ключевые инновации и тренды'),
    ('Криптовалюта', 'Blockchain, DeFi, криптовалюты', '₿', 'Суммаризируй новости крипторынка, выдели важные движения цен и регуляторные изменения'),
    ('Наука', 'Научные открытия и исследования', '🔬', 'Опиши научные достижения простым языком, объясни их значимость'),
    ('Бизнес', 'Стартапы, инвестиции, экономика', '💼', 'Выдели ключевые бизнес-события, сделки и тренды рынка')
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO digest_bot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO digest_bot;