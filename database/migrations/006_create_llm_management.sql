-- Migration 006: Create LLM management and billing tables
-- Управление AI провайдерами и монетизация

-- LLM провайдеры (OpenAI, Anthropic, Local, etc.)
CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL UNIQUE, -- openai, anthropic, local, ollama
    base_url VARCHAR(255),
    api_key_env_var VARCHAR(100), -- Имя переменной окружения с API ключом
    default_model VARCHAR(100),
    supported_models JSONB DEFAULT '[]'::jsonb,
    pricing_per_1k_tokens JSONB DEFAULT '{}'::jsonb, -- Цены за 1k токенов по моделям
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Настройки LLM для каждого PublicBot
CREATE TABLE IF NOT EXISTS llm_settings (
    id SERIAL PRIMARY KEY,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    llm_provider_id INTEGER NOT NULL REFERENCES llm_providers(id) ON DELETE RESTRICT,
    model_name VARCHAR(100) NOT NULL,
    max_tokens INTEGER DEFAULT 4000,
    temperature FLOAT DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),
    system_prompt TEXT,
    backup_provider_id INTEGER REFERENCES llm_providers(id), -- Fallback провайдер
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Один активный LLM setting на бота
    UNIQUE(public_bot_id, is_active) DEFERRABLE INITIALLY DEFERRED
);

-- Транзакции для биллинга
CREATE TABLE IF NOT EXISTS billing_transactions (
    id BIGSERIAL PRIMARY KEY,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    bot_user_id BIGINT REFERENCES bot_users(id) ON DELETE SET NULL,
    transaction_type VARCHAR(30) NOT NULL CHECK (transaction_type IN ('subscription', 'api_usage', 'premium_feature', 'refund')),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    provider VARCHAR(20) CHECK (provider IN ('stripe', 'paypal', 'crypto', 'internal')),
    provider_transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    metadata JSONB DEFAULT '{}'::jsonb, -- Дополнительная информация о транзакции
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_llm_providers_active ON llm_providers(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_providers_name ON llm_providers(provider_name);

CREATE INDEX IF NOT EXISTS idx_llm_settings_bot_id ON llm_settings(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_llm_settings_provider ON llm_settings(llm_provider_id);
CREATE INDEX IF NOT EXISTS idx_llm_settings_active ON llm_settings(public_bot_id, is_active);

CREATE INDEX IF NOT EXISTS idx_billing_transactions_bot_id ON billing_transactions(public_bot_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_user_id ON billing_transactions(bot_user_id);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_type ON billing_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_status ON billing_transactions(status);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_created ON billing_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_billing_transactions_provider_id ON billing_transactions(provider_transaction_id);

-- GIN индекс для metadata поиска
CREATE INDEX IF NOT EXISTS idx_billing_transactions_metadata_gin ON billing_transactions USING GIN (metadata);

-- Функция для получения активного LLM для бота
CREATE OR REPLACE FUNCTION get_active_llm_for_bot(p_public_bot_id INTEGER)
RETURNS TABLE(
    provider_name VARCHAR,
    model_name VARCHAR,
    max_tokens INTEGER,
    temperature FLOAT,
    system_prompt TEXT,
    api_key_env_var VARCHAR,
    base_url VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lp.provider_name,
        ls.model_name,
        ls.max_tokens,
        ls.temperature,
        ls.system_prompt,
        lp.api_key_env_var,
        lp.base_url
    FROM llm_settings ls
    JOIN llm_providers lp ON ls.llm_provider_id = lp.id
    WHERE ls.public_bot_id = p_public_bot_id 
    AND ls.is_active = TRUE 
    AND lp.is_active = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- View для статистики использования LLM
CREATE OR REPLACE VIEW llm_usage_stats AS
SELECT 
    pb.bot_name,
    lp.provider_name,
    ls.model_name,
    COUNT(pd.id) as processed_posts_count,
    AVG(CASE WHEN pd.ai_processing_metadata->>'tokens_used' IS NOT NULL 
             THEN (pd.ai_processing_metadata->>'tokens_used')::INTEGER 
             ELSE NULL END) as avg_tokens_per_post,
    SUM(CASE WHEN pd.ai_processing_metadata->>'tokens_used' IS NOT NULL 
             THEN (pd.ai_processing_metadata->>'tokens_used')::INTEGER 
             ELSE 0 END) as total_tokens_used
FROM llm_settings ls
JOIN public_bots pb ON ls.public_bot_id = pb.id
JOIN llm_providers lp ON ls.llm_provider_id = lp.id
LEFT JOIN processed_data pd ON pd.public_bot_id = pb.id 
    AND pd.processed_at >= NOW() - INTERVAL '30 days'
WHERE ls.is_active = TRUE
GROUP BY pb.bot_name, lp.provider_name, ls.model_name;

-- View для биллинг аналитики
CREATE OR REPLACE VIEW billing_analytics AS
SELECT 
    pb.bot_name,
    bt.transaction_type,
    bt.currency,
    COUNT(*) as transaction_count,
    SUM(bt.amount) as total_amount,
    AVG(bt.amount) as avg_amount,
    COUNT(CASE WHEN bt.status = 'completed' THEN 1 END) as completed_transactions,
    SUM(CASE WHEN bt.status = 'completed' THEN bt.amount ELSE 0 END) as total_revenue
FROM billing_transactions bt
JOIN public_bots pb ON bt.public_bot_id = pb.id
WHERE bt.created_at >= NOW() - INTERVAL '30 days'
GROUP BY pb.bot_name, bt.transaction_type, bt.currency;

-- Начальные данные: основные LLM провайдеры
INSERT INTO llm_providers (provider_name, base_url, api_key_env_var, default_model, supported_models, pricing_per_1k_tokens) VALUES
('openai', 'https://api.openai.com/v1', 'OPENAI_API_KEY', 'gpt-4o-mini', 
 '["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]'::jsonb,
 '{"gpt-4o-mini": 0.0001, "gpt-4o": 0.003, "gpt-3.5-turbo": 0.0005}'::jsonb),
('anthropic', 'https://api.anthropic.com', 'ANTHROPIC_API_KEY', 'claude-3-haiku-20240307',
 '["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"]'::jsonb,
 '{"claude-3-haiku-20240307": 0.0001, "claude-3-sonnet-20240229": 0.003, "claude-3-opus-20240229": 0.015}'::jsonb),
('local', 'http://localhost:11434', NULL, 'llama3.1:8b',
 '["llama3.1:8b", "llama3.1:70b", "mistral:7b"]'::jsonb,
 '{}'::jsonb);

-- Комментарии к таблицам
COMMENT ON TABLE llm_providers IS 'Конфигурация AI провайдеров (OpenAI, Anthropic, Local)';
COMMENT ON TABLE llm_settings IS 'Настройки LLM для каждого PublicBot';
COMMENT ON TABLE billing_transactions IS 'Транзакции биллинга и монетизации';

COMMENT ON COLUMN llm_providers.api_key_env_var IS 'Имя переменной окружения с API ключом (безопасность)';
COMMENT ON COLUMN llm_providers.pricing_per_1k_tokens IS 'Цены за 1000 токенов по моделям в JSON формате';
COMMENT ON COLUMN llm_settings.backup_provider_id IS 'Резервный провайдер при недоступности основного';
COMMENT ON COLUMN billing_transactions.metadata IS 'Дополнительная информация: usage stats, features used, etc.'; 