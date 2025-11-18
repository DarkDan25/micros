-- Создание пользователей и баз данных для всех сервисов
CREATE USER cinema_user WITH PASSWORD 'cinema_password';

-- Reviews Service Database
CREATE DATABASE reviews_db;
GRANT ALL PRIVILEGES ON DATABASE reviews_db TO cinema_user;

-- Users Service Database
CREATE DATABASE users_db;
GRANT ALL PRIVILEGES ON DATABASE users_db TO cinema_user;

-- Bonuses Service Database
CREATE DATABASE bonuses_db;
GRANT ALL PRIVILEGES ON DATABASE bonuses_db TO cinema_user;

-- Payments Service Database
CREATE DATABASE payments_db;
GRANT ALL PRIVILEGES ON DATABASE payments_db TO cinema_user;

-- Notifications Service Database
CREATE DATABASE notifications_db;
GRANT ALL PRIVILEGES ON DATABASE notifications_db TO cinema_user;

-- Movies Service Database
CREATE DATABASE movies_db;
GRANT ALL PRIVILEGES ON DATABASE movies_db TO cinema_user;