-- Настройка PostgreSQL для MorningStarBot3
-- Параметры из .env файла

-- Создание пользователя digest_bot
CREATE USER digest_bot WITH PASSWORD 'SecurePassword123!';

-- Создание базы данных digest_bot
CREATE DATABASE digest_bot OWNER digest_bot;

-- Предоставление всех привилегий пользователю
GRANT ALL PRIVILEGES ON DATABASE digest_bot TO digest_bot;

-- Подключение к созданной БД и настройка схемы
\c digest_bot;

-- Предоставление привилегий на схему public
GRANT ALL ON SCHEMA public TO digest_bot;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO digest_bot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO digest_bot;

-- Установка search_path для пользователя
ALTER USER digest_bot SET search_path TO public;

-- Проверка создания
SELECT 'База данных digest_bot успешно создана!' as status;
SELECT current_database(), current_user; 