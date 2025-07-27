-- Migration 008: AI Settings Table
-- Создание таблицы для хранения AI-настроек ботов

-- 1. Создание таблицы ai_settings
CREATE TABLE IF NOT EXISTS ai_settings (
    id SERIAL PRIMARY KEY,
    
    -- Привязка к боту (может быть NULL для глобальных настроек)
    public_bot_id INTEGER REFERENCES public_bots(id) ON DELETE CASCADE,
    
    -- Основные параметры
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    
    -- Категоризация настройки
    category VARCHAR(50) NOT NULL, -- 'summarization', 'categorization', 'general', 'prompts'
    description TEXT,
    
    -- Метаданные
    is_active BOOLEAN DEFAULT true,
    is_editable BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Создание индексов для быстрого поиска
CREATE INDEX idx_ai_settings_bot_key ON ai_settings(public_bot_id, setting_key);
CREATE INDEX idx_ai_settings_category ON ai_settings(category);
CREATE INDEX idx_ai_settings_active ON ai_settings(is_active) WHERE is_active = true;

-- 3. Создание уникального ключа для предотвращения дублирования
CREATE UNIQUE INDEX idx_ai_settings_unique ON ai_settings(
    COALESCE(public_bot_id, 0), setting_key
);

-- 4. Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_ai_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER ai_settings_update_timestamp
    BEFORE UPDATE ON ai_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_settings_timestamp();

-- 5. Вставка базовых настроек для AI сервисов
INSERT INTO ai_settings (public_bot_id, setting_key, setting_value, setting_type, category, description) VALUES

-- Глобальные настройки для суммаризации (public_bot_id = NULL означает глобальные настройки)
(NULL, 'max_summary_length', '150', 'integer', 'summarization', 'Максимальная длина резюме в символах'),
(NULL, 'min_summary_length', '50', 'integer', 'summarization', 'Минимальная длина резюме в символах'),
(NULL, 'default_language', 'ru', 'string', 'summarization', 'Язык по умолчанию для суммаризации'),
(NULL, 'default_tone', 'neutral', 'string', 'summarization', 'Тон по умолчанию (neutral, formal, casual)'),

-- Глобальные настройки для категоризации
(NULL, 'min_confidence', '0.7', 'float', 'categorization', 'Минимальный уровень уверенности для категоризации'),
(NULL, 'max_categories', '3', 'integer', 'categorization', 'Максимальное количество категорий на пост'),
(NULL, 'use_binary_relevance', 'true', 'boolean', 'categorization', 'Использовать бинарную релевантность'),
(NULL, 'quality_threshold', '0.6', 'float', 'categorization', 'Порог качества для принятия поста'),

-- Общие AI настройки
(NULL, 'ai_model', 'gpt-4', 'string', 'general', 'Модель AI по умолчанию'),
(NULL, 'max_tokens', '4000', 'integer', 'general', 'Максимальное количество токенов'),
(NULL, 'temperature', '0.7', 'float', 'general', 'Температура для генерации'),
(NULL, 'timeout', '30', 'integer', 'general', 'Таймаут запроса в секундах'),
(NULL, 'retry_attempts', '3', 'integer', 'general', 'Количество попыток повтора'),
(NULL, 'retry_delay', '5', 'integer', 'general', 'Задержка между попытками в секундах'),

-- Промпты по умолчанию
(NULL, 'default_summarization_prompt', 'Создай краткое резюме следующего текста на русском языке:', 'string', 'prompts', 'Промпт по умолчанию для суммаризации'),
(NULL, 'default_categorization_prompt', 'Определи категории для следующего поста и оцени его релевантность:', 'string', 'prompts', 'Промпт по умолчанию для категоризации'),

-- Настройки мониторинга
(NULL, 'enable_metrics', 'true', 'boolean', 'general', 'Включить сбор метрик'),
(NULL, 'metrics_retention_days', '30', 'integer', 'general', 'Количество дней хранения метрик'),
(NULL, 'batch_size', '10', 'integer', 'general', 'Размер батча для обработки');

-- 6. Добавление комментариев к таблице
COMMENT ON TABLE ai_settings IS 'Таблица для хранения AI-настроек ботов и глобальных настроек';
COMMENT ON COLUMN ai_settings.public_bot_id IS 'ID бота (NULL для глобальных настроек)';
COMMENT ON COLUMN ai_settings.setting_key IS 'Ключ настройки';
COMMENT ON COLUMN ai_settings.setting_value IS 'Значение настройки в текстовом формате';
COMMENT ON COLUMN ai_settings.setting_type IS 'Тип данных настройки';
COMMENT ON COLUMN ai_settings.category IS 'Категория настройки для группировки в UI'; 