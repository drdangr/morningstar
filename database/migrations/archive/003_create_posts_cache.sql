-- Migration 003: Create posts_cache table with time-based partitioning
-- Централизованное RAW хранение всех собранных постов от userbot

-- Основная партиционированная таблица
CREATE TABLE IF NOT EXISTS posts_cache (
    id BIGSERIAL,
    channel_telegram_id BIGINT NOT NULL, -- Telegram ID канала (без внешнего ключа)
    telegram_message_id BIGINT NOT NULL,
    title TEXT,
    content TEXT,
    media_urls JSONB DEFAULT '[]'::jsonb,
    views INTEGER DEFAULT 0,
    post_date TIMESTAMP NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW() NOT NULL,
    userbot_metadata JSONB DEFAULT '{}'::jsonb, -- Дополнительные данные от userbot
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Составной PRIMARY KEY включает partition key
    PRIMARY KEY (id, collected_at),
    -- Уникальный constraint по каналу и Telegram ID
    UNIQUE(channel_telegram_id, telegram_message_id, collected_at)
) PARTITION BY RANGE (collected_at);

-- Создание партиций по месяцам (начиная с июня 2025)
CREATE TABLE IF NOT EXISTS posts_cache_2025_06 PARTITION OF posts_cache 
    FOR VALUES FROM ('2025-06-01 00:00:00') TO ('2025-07-01 00:00:00');

CREATE TABLE IF NOT EXISTS posts_cache_2025_07 PARTITION OF posts_cache 
    FOR VALUES FROM ('2025-07-01 00:00:00') TO ('2025-08-01 00:00:00');

CREATE TABLE IF NOT EXISTS posts_cache_2025_08 PARTITION OF posts_cache 
    FOR VALUES FROM ('2025-08-01 00:00:00') TO ('2025-09-01 00:00:00');

-- Индексы на основной таблице (автоматически создаются на всех партициях)
CREATE INDEX IF NOT EXISTS idx_posts_cache_channel_date ON posts_cache(channel_telegram_id, post_date DESC);
CREATE INDEX IF NOT EXISTS idx_posts_cache_collected ON posts_cache(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_cache_telegram_id ON posts_cache(channel_telegram_id, telegram_message_id);
CREATE INDEX IF NOT EXISTS idx_posts_cache_processing_status ON posts_cache(processing_status, collected_at);

-- GIN индекс для JSONB полей
CREATE INDEX IF NOT EXISTS idx_posts_cache_metadata_gin ON posts_cache USING GIN (userbot_metadata);
CREATE INDEX IF NOT EXISTS idx_posts_cache_media_gin ON posts_cache USING GIN (media_urls);

-- Полнотекстовый поиск по контенту
CREATE INDEX IF NOT EXISTS idx_posts_cache_content_fts ON posts_cache USING GIN (to_tsvector('russian', COALESCE(title, '') || ' ' || COALESCE(content, '')));

-- Функция для автоматического создания партиций
CREATE OR REPLACE FUNCTION create_posts_cache_partition(partition_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    partition_name := 'posts_cache_' || to_char(partition_date, 'YYYY_MM');
    start_date := to_char(date_trunc('month', partition_date), 'YYYY-MM-DD HH24:MI:SS');
    end_date := to_char(date_trunc('month', partition_date) + interval '1 month', 'YYYY-MM-DD HH24:MI:SS');
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF posts_cache FOR VALUES FROM (%L) TO (%L)',
                   partition_name, start_date, end_date);
    
    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых партиций (старше 6 месяцев)
CREATE OR REPLACE FUNCTION cleanup_old_posts_cache_partitions()
RETURNS INTEGER AS $$
DECLARE
    partition_record RECORD;
    dropped_count INTEGER := 0;
    cutoff_date DATE := CURRENT_DATE - INTERVAL '6 months';
BEGIN
    FOR partition_record IN
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'posts_cache_____%%'
        AND tablename < 'posts_cache_' || to_char(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I.%I CASCADE', 
                      partition_record.schemaname, 
                      partition_record.tablename);
        dropped_count := dropped_count + 1;
    END LOOP;
    
    RETURN dropped_count;
END;
$$ LANGUAGE plpgsql;

-- Комментарии к таблице
COMMENT ON TABLE posts_cache IS 'Централизованное хранилище RAW постов от userbot с monthly partitioning';
COMMENT ON COLUMN posts_cache.telegram_message_id IS 'ID сообщения в Telegram';
COMMENT ON COLUMN posts_cache.userbot_metadata IS 'Дополнительные метаданные от userbot (автор, реакции, etc.)';
COMMENT ON COLUMN posts_cache.processing_status IS 'Статус обработки поста AI сервисами';
COMMENT ON COLUMN posts_cache.collected_at IS 'Время сбора поста userbot (используется для партиционирования)'; 