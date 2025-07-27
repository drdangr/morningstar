-- =====================================================
-- Migration 009: AI Settings Templates System
-- =====================================================
-- Система 3-уровневых AI настроек:
-- 1. Глобальные настройки (config_settings)
-- 2. Шаблон Public Bot (bot_templates)  
-- 3. Индивидуальные настройки бота (public_bots)

-- Таблица шаблонов ботов (значения по умолчанию)
CREATE TABLE bot_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT 'default',
    description TEXT,
    
    -- AI Settings Template
    default_ai_model VARCHAR(100) DEFAULT 'gpt-4o-mini',
    default_max_tokens INTEGER DEFAULT 4000,
    default_temperature DECIMAL(3,2) DEFAULT 0.3,
    
    -- Prompts Template
    default_categorization_prompt TEXT DEFAULT 'Проанализируй пост и определи наиболее подходящую категорию из предложенного списка. Учитывай контекст и семантическое значение.',
    default_summarization_prompt TEXT DEFAULT 'Создай краткое и информативное резюме поста на русском языке. Сохрани ключевые факты и важные детали.',
    
    -- Digest Settings Template
    default_max_posts_per_digest INTEGER DEFAULT 10,
    default_max_summary_length INTEGER DEFAULT 150,
    default_digest_language VARCHAR(10) DEFAULT 'ru',
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Создаем стандартный шаблон
INSERT INTO bot_templates (name, description) VALUES 
('default', 'Стандартный шаблон для новых публичных ботов');

-- Расширяем таблицу public_bots полями для override настроек
ALTER TABLE public_bots ADD COLUMN template_id INTEGER REFERENCES bot_templates(id) DEFAULT 1;

-- AI Settings Override (NULL = наследуется из шаблона)
ALTER TABLE public_bots ADD COLUMN override_ai_model VARCHAR(100);
ALTER TABLE public_bots ADD COLUMN override_max_tokens INTEGER;
ALTER TABLE public_bots ADD COLUMN override_temperature DECIMAL(3,2);

-- Override flags (определяют какие настройки переопределены)
ALTER TABLE public_bots ADD COLUMN ai_settings_override JSONB DEFAULT '{
    "ai_model": false,
    "max_tokens": false,
    "temperature": false,
    "categorization_prompt": false,
    "summarization_prompt": false,
    "max_posts_per_digest": false,
    "max_summary_length": false,
    "digest_language": false
}';

-- Упрощаем delivery_schedule - просто массивы времен по дням
-- Убираем сложные параметры для каждого времени
UPDATE public_bots SET delivery_schedule = '{
    "monday": ["08:00", "19:00"],
    "tuesday": ["08:00", "19:00"], 
    "wednesday": ["08:00", "19:00"],
    "thursday": ["08:00", "19:00"],
    "friday": ["08:00", "19:00"],
    "saturday": [],
    "sunday": []
}' WHERE delivery_schedule IS NULL;

-- Индексы для производительности
CREATE INDEX idx_bot_templates_active ON bot_templates(is_active);
CREATE INDEX idx_public_bots_template ON public_bots(template_id);
CREATE INDEX idx_public_bots_ai_override ON public_bots USING GIN (ai_settings_override);

-- Представление для получения эффективных настроек бота (с наследованием)
CREATE OR REPLACE VIEW bot_effective_settings AS
SELECT 
    pb.id as bot_id,
    pb.name as bot_name,
    
    -- Эффективные AI настройки (с fallback на шаблон)
    COALESCE(pb.override_ai_model, bt.default_ai_model) as effective_ai_model,
    COALESCE(pb.override_max_tokens, bt.default_max_tokens) as effective_max_tokens,
    COALESCE(pb.override_temperature, bt.default_temperature) as effective_temperature,
    
    -- Промпты (всегда из бота, fallback на шаблон)
    COALESCE(pb.categorization_prompt, bt.default_categorization_prompt) as effective_categorization_prompt,
    COALESCE(pb.summarization_prompt, bt.default_summarization_prompt) as effective_summarization_prompt,
    
    -- Digest настройки  
    COALESCE(pb.max_posts_per_digest, bt.default_max_posts_per_digest) as effective_max_posts,
    COALESCE(pb.max_summary_length, bt.default_max_summary_length) as effective_max_summary_length,
    COALESCE(pb.default_language, bt.default_digest_language) as effective_language,
    
    -- Мета информация
    pb.ai_settings_override,
    bt.name as template_name
FROM public_bots pb
LEFT JOIN bot_templates bt ON pb.template_id = bt.id;

-- Функция для создания бота из шаблона
CREATE OR REPLACE FUNCTION create_bot_from_template(
    bot_name VARCHAR(255),
    template_name VARCHAR(255) DEFAULT 'default'
) RETURNS INTEGER AS $$
DECLARE
    template_id INTEGER;
    new_bot_id INTEGER;
BEGIN
    -- Получаем ID шаблона
    SELECT id INTO template_id FROM bot_templates WHERE name = template_name AND is_active = true;
    
    IF template_id IS NULL THEN
        RAISE EXCEPTION 'Шаблон % не найден', template_name;
    END IF;
    
    -- Создаем бота с привязкой к шаблону
    INSERT INTO public_bots (name, template_id, status)
    VALUES (bot_name, template_id, 'setup')
    RETURNING id INTO new_bot_id;
    
    RETURN new_bot_id;
END;
$$ LANGUAGE plpgsql; 