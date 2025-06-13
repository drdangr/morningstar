-- Migration 007: Enhance multitenancy support
-- Улучшение поддержки мультитенантности и оптимизация производительности

-- 1. Добавляем партиционирование для posts_cache
CREATE TABLE IF NOT EXISTS posts_cache_partitioned (
    id SERIAL,
    channel_telegram_id INTEGER NOT NULL,
    telegram_message_id INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    media_urls JSONB DEFAULT '[]'::jsonb,
    views INTEGER DEFAULT 0,
    post_date TIMESTAMP NOT NULL,
    collected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    userbot_metadata JSONB DEFAULT '{}'::jsonb,
    processing_status VARCHAR(50) DEFAULT 'pending',
    public_bot_id INTEGER REFERENCES public_bots(id),
    retention_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (id, post_date)
) PARTITION BY RANGE (post_date);

-- Создаем партиции по месяцам
CREATE TABLE posts_cache_y2025m06 PARTITION OF posts_cache_partitioned
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

CREATE TABLE posts_cache_y2025m07 PARTITION OF posts_cache_partitioned
    FOR VALUES FROM ('2025-07-01') TO ('2025-08-01');

-- 2. Добавляем индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_posts_cache_processing_status 
    ON posts_cache_partitioned(processing_status, post_date);

CREATE INDEX IF NOT EXISTS idx_posts_cache_public_bot 
    ON posts_cache_partitioned(public_bot_id, post_date);

CREATE INDEX IF NOT EXISTS idx_posts_cache_retention 
    ON posts_cache_partitioned(retention_until)
    WHERE retention_until IS NOT NULL;

-- 3. Добавляем связь между posts_cache и public_bots
ALTER TABLE posts_cache_partitioned
    ADD CONSTRAINT fk_posts_cache_public_bot
    FOREIGN KEY (public_bot_id)
    REFERENCES public_bots(id)
    ON DELETE SET NULL;

-- 4. Добавляем таблицу для отслеживания обработки постов
CREATE TABLE IF NOT EXISTS post_processing_queue (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_id, public_bot_id)
);

CREATE INDEX IF NOT EXISTS idx_processing_queue_status 
    ON post_processing_queue(status, priority, created_at);

-- 5. Добавляем таблицу для метрик обработки
CREATE TABLE IF NOT EXISTS processing_metrics (
    id SERIAL PRIMARY KEY,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id),
    metric_date DATE NOT NULL,
    total_posts INTEGER DEFAULT 0,
    processed_posts INTEGER DEFAULT 0,
    failed_posts INTEGER DEFAULT 0,
    avg_processing_time FLOAT,
    total_tokens_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(public_bot_id, metric_date)
);

-- 6. Миграция данных из старой таблицы в новую
INSERT INTO posts_cache_partitioned (
    channel_telegram_id,
    telegram_message_id,
    title,
    content,
    media_urls,
    views,
    post_date,
    collected_at,
    userbot_metadata,
    processing_status
)
SELECT 
    channel_telegram_id,
    telegram_message_id,
    title,
    content,
    media_urls,
    views,
    post_date,
    collected_at,
    userbot_metadata,
    processing_status
FROM posts_cache;

-- 7. Переименовываем таблицы
ALTER TABLE posts_cache RENAME TO posts_cache_old;
ALTER TABLE posts_cache_partitioned RENAME TO posts_cache;

-- 8. Создаем функцию для автоматического создания партиций
CREATE OR REPLACE FUNCTION create_posts_cache_partition()
RETURNS trigger AS $$
DECLARE
    partition_date TEXT;
    partition_name TEXT;
BEGIN
    partition_date := to_char(NEW.post_date, 'YYYY_MM');
    partition_name := 'posts_cache_y' || partition_date;
    
    IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF posts_cache
             FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            date_trunc('month', NEW.post_date),
            date_trunc('month', NEW.post_date + interval '1 month')
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 9. Создаем триггер для автоматического создания партиций
CREATE TRIGGER create_posts_cache_partition_trigger
    BEFORE INSERT ON posts_cache
    FOR EACH ROW
    EXECUTE FUNCTION create_posts_cache_partition(); 