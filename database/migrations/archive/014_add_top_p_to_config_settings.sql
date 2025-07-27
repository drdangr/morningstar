-- Migration 014: Добавление параметра top_p для суммаризации
-- Дата: 2025-01-04 (Task 4.2)
-- Описание: Добавляем глобальный параметр top_p для контроля разнообразия ответов в суммаризации

BEGIN;

-- Добавляем новый параметр ai_summarization_top_p
INSERT INTO config_settings (key, value, value_type, category, description, is_editable, created_at, updated_at) 
VALUES (
    'ai_summarization_top_p',
    '1.0',
    'float',
    'ai',
    'Top-p (nucleus sampling) для суммаризации (0.0-1.0). Контролирует разнообразие генерируемых ответов',
    true,
    NOW(),
    NOW()
) ON CONFLICT (key) DO NOTHING;

COMMIT;

-- Проверяем результат
SELECT key, value, value_type, category, description 
FROM config_settings 
WHERE key = 'ai_summarization_top_p'; 