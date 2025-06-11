-- Migration 004: Create processed_data table with hash partitioning by bot_id
-- AI-обработанные данные для каждого PublicBot индивидуально

-- Основная партиционированная таблица
CREATE TABLE IF NOT EXISTS processed_data (
    id BIGSERIAL,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    post_cache_id BIGINT NOT NULL, -- Ссылка на posts_cache без FK constraint
    channel_telegram_id BIGINT NOT NULL, -- Дублируем для удобства поиска
    telegram_message_id BIGINT NOT NULL, -- Дублируем для удобства поиска
    ai_summary TEXT,
    ai_category VARCHAR(100), -- AI-присвоенная категория (индивидуальная для поста)
    ai_importance FLOAT CHECK (ai_importance >= 0 AND ai_importance <= 10),
    ai_urgency FLOAT CHECK (ai_urgency >= 0 AND ai_urgency <= 10),  
    ai_significance FLOAT CHECK (ai_significance >= 0 AND ai_significance <= 10),
    ai_sentiment VARCHAR(20) CHECK (ai_sentiment IN ('positive', 'negative', 'neutral')),
    ai_language VARCHAR(10) DEFAULT 'ru',
    ai_processing_metadata JSONB DEFAULT '{}'::jsonb, -- Метаданные AI обработки
    processed_at TIMESTAMP DEFAULT NOW() NOT NULL,
    
    -- Составной PRIMARY KEY включает partition key
    PRIMARY KEY (id, public_bot_id),
    -- Уникальный constraint: один пост может быть обработан только один раз для каждого бота
    UNIQUE(public_bot_id, post_cache_id)
) PARTITION BY HASH (public_bot_id);

-- Создание hash партиций (4 партиции для начала, можно расширить)
CREATE TABLE IF NOT EXISTS processed_data_p0 PARTITION OF processed_data 
    FOR VALUES WITH (modulus 4, remainder 0);

CREATE TABLE IF NOT EXISTS processed_data_p1 PARTITION OF processed_data 
    FOR VALUES WITH (modulus 4, remainder 1);

CREATE TABLE IF NOT EXISTS processed_data_p2 PARTITION OF processed_data 
    FOR VALUES WITH (modulus 4, remainder 2);

CREATE TABLE IF NOT EXISTS processed_data_p3 PARTITION OF processed_data 
    FOR VALUES WITH (modulus 4, remainder 3);

-- Индексы на основной таблице
CREATE INDEX IF NOT EXISTS idx_processed_data_bot_id ON processed_data(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_processed_data_post_cache ON processed_data(post_cache_id);
CREATE INDEX IF NOT EXISTS idx_processed_data_processed_at ON processed_data(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_processed_data_category ON processed_data(public_bot_id, ai_category);
CREATE INDEX IF NOT EXISTS idx_processed_data_importance ON processed_data(public_bot_id, ai_importance DESC);

-- Композитный индекс для сортировки дайджестов
CREATE INDEX IF NOT EXISTS idx_processed_data_digest_sorting ON processed_data(
    public_bot_id, 
    ai_importance DESC, 
    ai_urgency DESC, 
    ai_significance DESC, 
    processed_at DESC
);

-- GIN индекс для AI метаданных
CREATE INDEX IF NOT EXISTS idx_processed_data_ai_metadata_gin ON processed_data USING GIN (ai_processing_metadata);

-- Полнотекстовый поиск по AI summary
CREATE INDEX IF NOT EXISTS idx_processed_data_summary_fts ON processed_data USING GIN (to_tsvector('russian', COALESCE(ai_summary, '')));

-- Функция для добавления новых hash партиций при масштабировании
CREATE OR REPLACE FUNCTION add_processed_data_partition(new_modulus INTEGER, new_remainder INTEGER)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
BEGIN
    partition_name := 'processed_data_p' || new_remainder::TEXT;
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF processed_data FOR VALUES WITH (modulus %L, remainder %L)',
                   partition_name, new_modulus, new_remainder);
    
    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- View для агрегированной статистики по ботам
CREATE OR REPLACE VIEW processed_data_stats AS
SELECT 
    pb.bot_name,
    pb.id as public_bot_id,
    COUNT(*) as total_processed_posts,
    AVG(pd.ai_importance) as avg_importance,
    AVG(pd.ai_urgency) as avg_urgency,
    AVG(pd.ai_significance) as avg_significance,
    COUNT(DISTINCT pd.ai_category) as unique_categories,
    MAX(pd.processed_at) as last_processed_at,
    COUNT(CASE WHEN pd.processed_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as posts_last_24h
FROM processed_data pd
JOIN public_bots pb ON pd.public_bot_id = pb.id
GROUP BY pb.id, pb.bot_name;

-- Функция для очистки старых обработанных данных (старше 3 месяцев)
CREATE OR REPLACE FUNCTION cleanup_old_processed_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM processed_data 
    WHERE processed_at < NOW() - INTERVAL '3 months';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Комментарии к таблице
COMMENT ON TABLE processed_data IS 'AI-обработанные данные постов для каждого PublicBot с hash partitioning';
COMMENT ON COLUMN processed_data.ai_category IS 'AI-присвоенная категория конкретно для этого поста (индивидуальная категоризация)';
COMMENT ON COLUMN processed_data.ai_importance IS 'AI-оценка важности поста (0-10)';
COMMENT ON COLUMN processed_data.ai_urgency IS 'AI-оценка срочности поста (0-10)';
COMMENT ON COLUMN processed_data.ai_significance IS 'AI-оценка значимости поста (0-10)';
COMMENT ON COLUMN processed_data.ai_processing_metadata IS 'Метаданные AI обработки (модель, токены, время обработки, etc.)'; 