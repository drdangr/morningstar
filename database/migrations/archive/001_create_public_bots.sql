-- Migration 001: Create public_bots table
-- Основная таблица для конфигурации тематических ботов в мультитенантной архитектуре

CREATE TABLE IF NOT EXISTS public_bots (
    id SERIAL PRIMARY KEY,
    bot_name VARCHAR(100) NOT NULL UNIQUE,
    bot_token VARCHAR(255) NOT NULL UNIQUE, -- Telegram bot token
    description TEXT,
    ai_prompt_template TEXT NOT NULL, -- Персональный AI промпт для тона голоса
    categorization_prompt TEXT, -- Специальный промпт для CategorizationService
    summarization_prompt TEXT, -- Специальный промпт для SummarizationService
    default_language VARCHAR(10) DEFAULT 'ru',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    welcome_message TEXT, -- Персональное приветствие для каждого бота
    digest_schedule VARCHAR(50) DEFAULT 'daily', -- daily, twice_daily, hourly, manual
    max_posts_per_digest INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_public_bots_status ON public_bots(status);
CREATE INDEX IF NOT EXISTS idx_public_bots_bot_name ON public_bots(bot_name);
CREATE INDEX IF NOT EXISTS idx_public_bots_language ON public_bots(default_language);

-- Функция автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_public_bots_updated_at ON public_bots;
CREATE TRIGGER update_public_bots_updated_at 
    BEFORE UPDATE ON public_bots 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Комментарии к таблице и полям
COMMENT ON TABLE public_bots IS 'Конфигурация тематических ботов в мультитенантной платформе';
COMMENT ON COLUMN public_bots.bot_name IS 'Уникальное имя бота (например: usa_digest, military_reports)';
COMMENT ON COLUMN public_bots.bot_token IS 'Telegram Bot API token';
COMMENT ON COLUMN public_bots.ai_prompt_template IS 'Базовый AI промпт, определяющий тон голоса и стиль бота';
COMMENT ON COLUMN public_bots.categorization_prompt IS 'Специализированный промпт для AI категоризации постов';
COMMENT ON COLUMN public_bots.summarization_prompt IS 'Специализированный промпт для AI саммаризации постов';
COMMENT ON COLUMN public_bots.digest_schedule IS 'Расписание отправки дайджестов';
COMMENT ON COLUMN public_bots.max_posts_per_digest IS 'Максимальное количество постов в одном дайджесте'; 