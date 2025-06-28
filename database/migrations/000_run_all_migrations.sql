-- Master Migration Script: Multi-tenant Database Schema
-- Запускает все миграции в правильном порядке для мультитенантной архитектуры

-- Начало транзакции для atomic migration
BEGIN;

-- Создание таблицы для трекинга миграций
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64)
);

-- Функция для логирования миграций
CREATE OR REPLACE FUNCTION log_migration(migration_name TEXT, checksum TEXT DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO schema_migrations (migration_name, checksum)
    VALUES (migration_name, checksum)
    ON CONFLICT (migration_name) DO NOTHING;
    
    RAISE NOTICE 'Migration executed: %', migration_name;
END;
$$ LANGUAGE plpgsql;

-- Migration 001: Public Bots
\echo 'Executing Migration 001: Create public_bots table...'
\i 001_create_public_bots.sql
SELECT log_migration('001_create_public_bots');

-- Migration 002: Bot Relationships  
\echo 'Executing Migration 002: Create bot relationships tables...'
\i 002_create_bot_relationships.sql
SELECT log_migration('002_create_bot_relationships');

-- Migration 003: Posts Cache
\echo 'Executing Migration 003: Create posts_cache with partitioning...'
\i 003_create_posts_cache.sql
SELECT log_migration('003_create_posts_cache');

-- Migration 004: Processed Data
\echo 'Executing Migration 004: Create processed_data with partitioning...'
\i 004_create_processed_data.sql
SELECT log_migration('004_create_processed_data');

-- Migration 005: Multitenant Users
\echo 'Executing Migration 005: Create multitenant users and subscriptions...'
\i 005_create_multitenant_users.sql
SELECT log_migration('005_create_multitenant_users');

-- Migration 006: LLM Management
\echo 'Executing Migration 006: Create LLM management and billing...'
\i 006_create_llm_management.sql
SELECT log_migration('006_create_llm_management');

-- Run migration 012: Add processing_status to processed_data
\i 012_add_processing_status_to_processed_data.sql

-- Run migration 013: Add boolean flags to processed_data
\i 013_add_boolean_flags_to_processed_data.sql

-- Создание первого default PublicBot
INSERT INTO public_bots (
    bot_name, 
    bot_token, 
    description, 
    ai_prompt_template,
    categorization_prompt,
    summarization_prompt,
    welcome_message
) VALUES (
    'default_digest_bot',
    'TEMP_TOKEN_TO_BE_REPLACED', -- Будет заменен реальным токеном
    'Главный дайджест-бот (миграция из монолитной системы)',
    'Ты - профессиональный редактор новостных дайджестов. Анализируй посты внимательно и предоставляй краткие, информативные резюме на русском языке.',
    'Проанализируй этот пост и определи наиболее подходящую категорию. Учитывай контекст и семантику, а не только ключевые слова.',
    'Создай краткое резюме этого поста на русском языке. Сохрани ключевую информацию и сделай текст понятным для читателя.',
    'Добро пожаловать в Дайджест-бот! 📰\n\nВыберите интересующие вас категории для получения персонализированных новостных дайджестов.\n\nИспользуйте /categories для просмотра доступных категорий.'
) ON CONFLICT (bot_name) DO NOTHING;

-- Получение ID default бота для дальнейших операций
DO $$
DECLARE
    default_bot_id INTEGER;
BEGIN
    -- Получаем ID default бота
    SELECT id INTO default_bot_id FROM public_bots WHERE bot_name = 'default_digest_bot';
    
    -- Default bot создан, каналы и категории будут добавлены через админ-панель
    RAISE NOTICE 'Default bot created with ID: %', default_bot_id;
END $$;

-- Настройка LLM для default бота
DO $$
DECLARE
    default_bot_id INTEGER;
    openai_provider_id INTEGER;
BEGIN
    SELECT id INTO default_bot_id FROM public_bots WHERE bot_name = 'default_digest_bot';
    SELECT id INTO openai_provider_id FROM llm_providers WHERE provider_name = 'openai';
    
    INSERT INTO llm_settings (
        public_bot_id,
        llm_provider_id,
        model_name,
        max_tokens,
        temperature,
        system_prompt,
        is_active
    ) VALUES (
        default_bot_id,
        openai_provider_id,
        'gpt-4o-mini',
        4000,
        0.7,
        'Ты - профессиональный AI-редактор новостных дайджестов. Твоя задача - анализировать посты из Telegram каналов и создавать краткие, информативные резюме на русском языке.',
        TRUE
    ) ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'LLM settings configured for default bot';
END $$;

-- Создание функций для удобного управления multi-tenant схемой
CREATE OR REPLACE FUNCTION create_new_public_bot(
    p_bot_name VARCHAR,
    p_bot_token VARCHAR,
    p_description TEXT DEFAULT NULL,
    p_ai_prompt_template TEXT DEFAULT 'Стандартный AI промпт для анализа новостей.',
    p_language VARCHAR DEFAULT 'ru'
)
RETURNS INTEGER AS $$
DECLARE
    new_bot_id INTEGER;
BEGIN
    INSERT INTO public_bots (
        bot_name, bot_token, description, ai_prompt_template, default_language
    ) VALUES (
        p_bot_name, p_bot_token, p_description, p_ai_prompt_template, p_language
    ) RETURNING id INTO new_bot_id;
    
    -- Автоматическая настройка LLM (OpenAI по умолчанию)
    INSERT INTO llm_settings (
        public_bot_id, llm_provider_id, model_name, is_active
    ) SELECT 
        new_bot_id, id, 'gpt-4o-mini', TRUE
    FROM llm_providers 
    WHERE provider_name = 'openai' 
    LIMIT 1;
    
    RETURN new_bot_id;
END;
$$ LANGUAGE plpgsql;

-- Функция для клонирования настроек между ботами
CREATE OR REPLACE FUNCTION clone_bot_settings(source_bot_id INTEGER, target_bot_id INTEGER)
RETURNS VOID AS $$
BEGIN
    -- Клонирование привязок каналов
    INSERT INTO bot_channels (public_bot_id, channel_id, weight, is_active)
    SELECT target_bot_id, channel_id, weight, is_active
    FROM bot_channels
    WHERE public_bot_id = source_bot_id
    ON CONFLICT DO NOTHING;
    
    -- Клонирование привязок категорий
    INSERT INTO bot_categories (public_bot_id, category_id, custom_ai_instructions, weight, is_active)
    SELECT target_bot_id, category_id, custom_ai_instructions, weight, is_active
    FROM bot_categories
    WHERE public_bot_id = source_bot_id
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Settings cloned from bot % to bot %', source_bot_id, target_bot_id;
END;
$$ LANGUAGE plpgsql;

-- Финальная статистика после миграции
DO $$
DECLARE
    bots_count INTEGER;
    llm_providers_count INTEGER;
    partitions_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO bots_count FROM public_bots;
    SELECT COUNT(*) INTO llm_providers_count FROM llm_providers;
    SELECT COUNT(*) INTO partitions_count FROM pg_tables WHERE tablename LIKE '%partition%';
    
    RAISE NOTICE '=== MIGRATION COMPLETED SUCCESSFULLY ===';
    RAISE NOTICE 'Public Bots created: %', bots_count;
    RAISE NOTICE 'LLM Providers configured: %', llm_providers_count;
    RAISE NOTICE 'Database partitions created: %', partitions_count;
    RAISE NOTICE 'Multi-tenant schema ready for production!';
    RAISE NOTICE 'Next: Add channels and categories through Admin Panel';
END $$;

-- Коммит транзакции
COMMIT;

\echo 'Multi-tenant database migration completed successfully!'
\echo 'Next steps:'
\echo '1. Update Backend API models to support multi-tenant schema'
\echo '2. Create Python AI Services (SummarizationService + CategorizationService)'
\echo '3. Archive and remove N8N workflows'
\echo '4. Test the new architecture with real data'

-- All migrations completed 