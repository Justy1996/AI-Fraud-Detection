-- ============================================================
-- GHANA'S AI POLICE: MySQL Database Setup Script
-- Run as: mysql -u root -p < setup_mysql.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS aifds_mm
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE aifds_mm;

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  VARCHAR(64)    NOT NULL,
    type            VARCHAR(20)    NOT NULL,
    amount          DECIMAL(18,2)  NOT NULL,
    orig_before     DECIMAL(18,2)  NOT NULL DEFAULT 0,
    orig_after      DECIMAL(18,2)  NOT NULL DEFAULT 0,
    dest_before     DECIMAL(18,2)  NOT NULL DEFAULT 0,
    dest_after      DECIMAL(18,2)  NOT NULL DEFAULT 0,
    is_fraud        TINYINT        NOT NULL DEFAULT 0,
    fraud_prob      FLOAT          NOT NULL DEFAULT 0,
    risk_level      VARCHAR(10)    NOT NULL DEFAULT 'LOW',
    top_features    TEXT,
    status          VARCHAR(20)    DEFAULT 'PROCESSED',
    created_at      TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fraud (is_fraud),
    INDEX idx_created (created_at),
    INDEX idx_txn_id (transaction_id)
) ENGINE=InnoDB;

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id  VARCHAR(64)  NOT NULL,
    alert_type      VARCHAR(50)  NOT NULL,
    message         TEXT,
    resolved        TINYINT      DEFAULT 0,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_txn (transaction_id),
    INDEX idx_resolved (resolved)
) ENGINE=InnoDB;

-- Model metrics table
CREATE TABLE IF NOT EXISTS model_metrics (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    version         VARCHAR(30)  NOT NULL,
    accuracy        FLOAT,
    precision_score FLOAT,
    recall_score    FLOAT,
    f1_score        FLOAT,
    trained_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(20)  DEFAULT 'analyst',
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Default admin user (password: justy1996.)
INSERT IGNORE INTO users (username, password, role)
VALUES (
    'Justina',
    SHA2('justy1996.', 256),
    'admin'
);

-- Fraud analyst user (password: analyst123)
INSERT IGNORE INTO users (username, password, role)
VALUES (
    'analyst',
    SHA2('analyst123', 256),
    'analyst'
);

SHOW TABLES;
SELECT 'GHANA''S AI POLICE MySQL setup complete!' AS status;
