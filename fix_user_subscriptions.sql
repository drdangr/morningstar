-- Исправление структуры таблицы user_subscriptions
-- Добавляет отсутствующие столбцы user_id и category_id

-- Проверяем текущую структуру таблицы
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'user_subscriptions' 
ORDER BY ordinal_position;

-- Если таблица существует, но структура неправильная - дропаем и пересоздаем
DROP TABLE IF EXISTS user_subscriptions CASCADE;

-- Создаем таблицу с правильной структурой
CREATE TABLE user_subscriptions (
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, category_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Проверяем финальную структуру
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'user_subscriptions' 
ORDER BY ordinal_position;

-- Проверяем ограничения
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'user_subscriptions'::regclass; 