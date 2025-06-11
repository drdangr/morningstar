-- Migration 005: Create multitenant users and subscriptions tables
-- Пользователи изолированы по ботам + гибкие подписки

-- Мультитенантные пользователи
CREATE TABLE IF NOT EXISTS bot_users (
    id BIGSERIAL PRIMARY KEY,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    telegram_user_id BIGINT NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'ru',
    preferred_digest_time TIME DEFAULT '09:00:00', -- Время получения дайджестов
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP DEFAULT NOW(),
    subscription_status VARCHAR(20) DEFAULT 'free' CHECK (subscription_status IN ('free', 'premium', 'enterprise')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Уникальный constraint: один Telegram пользователь может быть только в одном боте
    UNIQUE(public_bot_id, telegram_user_id)
);

-- Гибкие подписки пользователей
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    bot_user_id BIGINT NOT NULL REFERENCES bot_users(id) ON DELETE CASCADE,
    subscription_type VARCHAR(20) NOT NULL CHECK (subscription_type IN ('channel', 'category')),
    channel_id INTEGER REFERENCES channels(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 5), -- 1=низкий, 5=высокий
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Проверка: должен быть указан либо channel_id, либо category_id
    CHECK (
        (subscription_type = 'channel' AND channel_id IS NOT NULL AND category_id IS NULL) OR
        (subscription_type = 'category' AND category_id IS NOT NULL AND channel_id IS NULL)
    ),
    
    -- Уникальный constraint: пользователь не может дважды подписаться на одно и то же
    UNIQUE(bot_user_id, subscription_type, channel_id, category_id)
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_bot_users_bot_id ON bot_users(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_users_telegram_id ON bot_users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_bot_users_active ON bot_users(public_bot_id, is_active);
CREATE INDEX IF NOT EXISTS idx_bot_users_subscription_status ON bot_users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_bot_users_last_activity ON bot_users(last_activity DESC);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(bot_user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_channel ON user_subscriptions(channel_id) WHERE subscription_type = 'channel';
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_category ON user_subscriptions(category_id) WHERE subscription_type = 'category';
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON user_subscriptions(bot_user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_priority ON user_subscriptions(bot_user_id, priority DESC);

-- Функция для обновления last_activity
CREATE OR REPLACE FUNCTION update_user_last_activity(p_public_bot_id INTEGER, p_telegram_user_id BIGINT)
RETURNS VOID AS $$
BEGIN
    UPDATE bot_users 
    SET last_activity = NOW()
    WHERE public_bot_id = p_public_bot_id 
    AND telegram_user_id = p_telegram_user_id;
END;
$$ LANGUAGE plpgsql;

-- View для статистики пользователей по ботам
CREATE OR REPLACE VIEW bot_users_stats AS
SELECT 
    pb.bot_name,
    pb.id as public_bot_id,
    COUNT(*) as total_users,
    COUNT(CASE WHEN bu.is_active THEN 1 END) as active_users,
    COUNT(CASE WHEN bu.subscription_status = 'premium' THEN 1 END) as premium_users,
    COUNT(CASE WHEN bu.last_activity >= NOW() - INTERVAL '7 days' THEN 1 END) as users_last_week,
    AVG(EXTRACT(EPOCH FROM (NOW() - bu.created_at))/86400) as avg_user_age_days
FROM bot_users bu
JOIN public_bots pb ON bu.public_bot_id = pb.id
GROUP BY pb.id, pb.bot_name;

-- View для аналитики подписок
CREATE OR REPLACE VIEW subscription_analytics AS
SELECT 
    pb.bot_name,
    us.subscription_type,
    CASE 
        WHEN us.subscription_type = 'channel' THEN ch.channel_name
        WHEN us.subscription_type = 'category' THEN cat.category_name
    END as subscription_target,
    COUNT(*) as subscriber_count,
    AVG(us.priority) as avg_priority,
    COUNT(CASE WHEN us.is_active THEN 1 END) as active_subscriptions
FROM user_subscriptions us
JOIN bot_users bu ON us.bot_user_id = bu.id
JOIN public_bots pb ON bu.public_bot_id = pb.id
LEFT JOIN channels ch ON us.channel_id = ch.id
LEFT JOIN categories cat ON us.category_id = cat.id
GROUP BY pb.bot_name, us.subscription_type, subscription_target;

-- Комментарии к таблицам
COMMENT ON TABLE bot_users IS 'Мультитенантные пользователи - изолированы по ботам';
COMMENT ON TABLE user_subscriptions IS 'Гибкие подписки пользователей на каналы или категории';

COMMENT ON COLUMN bot_users.preferred_digest_time IS 'Предпочитаемое время получения дайджестов';
COMMENT ON COLUMN bot_users.timezone IS 'Временная зона пользователя для правильной доставки';
COMMENT ON COLUMN user_subscriptions.subscription_type IS 'Тип подписки: channel (на конкретный канал) или category (на категорию)';
COMMENT ON COLUMN user_subscriptions.priority IS 'Приоритет подписки: 1=низкий, 5=высокий (влияет на порядок в дайджесте)'; 