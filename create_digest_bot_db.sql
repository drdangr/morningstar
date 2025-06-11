-- Создание пользователя и базы данных digest_bot
-- Выполнить от имени суперпользователя postgres

-- Создаем пользователя digest_bot
CREATE USER digest_bot WITH PASSWORD 'Demiurg12@';

-- Создаем базу данных digest_bot с владельцем digest_bot
CREATE DATABASE digest_bot OWNER digest_bot;

-- Даем пользователю права на создание баз данных (для тестов)
ALTER USER digest_bot CREATEDB;

-- Подключаемся к базе digest_bot и даем полные права
\c digest_bot

-- Даем пользователю все права на схему public
GRANT ALL PRIVILEGES ON SCHEMA public TO digest_bot;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO digest_bot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO digest_bot;

-- Устанавливаем права по умолчанию для новых объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO digest_bot;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO digest_bot;

\echo 'Пользователь digest_bot и база данных digest_bot созданы успешно!' 