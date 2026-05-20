-- Run once in DataGrip while connected as MySQL root (Homebrew, no Docker)
-- Creates database + app user matching DriveClear_Backend/.env

CREATE DATABASE IF NOT EXISTS driveclear
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'driveclear'@'localhost' IDENTIFIED BY 'driveclear';
CREATE USER IF NOT EXISTS 'driveclear'@'127.0.0.1' IDENTIFIED BY 'driveclear';

GRANT ALL PRIVILEGES ON driveclear.* TO 'driveclear'@'localhost';
GRANT ALL PRIVILEGES ON driveclear.* TO 'driveclear'@'127.0.0.1';

FLUSH PRIVILEGES;

-- Verify
SELECT user, host FROM mysql.user WHERE user = 'driveclear';
SHOW DATABASES LIKE 'driveclear';
