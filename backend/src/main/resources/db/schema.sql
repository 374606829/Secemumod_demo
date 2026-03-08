-- =====================================================
-- Encrypted Asset Demo - Minimal Schema
-- Database: secemumod_demo
-- =====================================================

CREATE DATABASE IF NOT EXISTS secemumod_demo
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE secemumod_demo;

-- 1. Users
CREATE TABLE IF NOT EXISTS sys_user (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(64)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL COMMENT 'BCrypt hash',
    role        VARCHAR(32)  NOT NULL DEFAULT 'USER',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Mod assets
CREATE TABLE IF NOT EXISTS mod_info (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    status      VARCHAR(32)  NOT NULL DEFAULT 'APPROVED',
    creator_id  BIGINT       NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Encryption keys (DEK encrypted by MasterKey via AES-GCM)
CREATE TABLE IF NOT EXISTS mod_encryption_key (
    id                   BIGINT AUTO_INCREMENT PRIMARY KEY,
    mod_id               BIGINT       NOT NULL,
    file_key_encrypted   TEXT         NOT NULL COMMENT 'Base64(iv + ciphertext + tag)',
    key_version          VARCHAR(16)  NOT NULL DEFAULT 'v1',
    encryption_algorithm VARCHAR(32)  NOT NULL DEFAULT 'AES-256',
    creator_id           BIGINT       NOT NULL,
    is_active            TINYINT(1)   NOT NULL DEFAULT 1,
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mod_id (mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Mod files
CREATE TABLE IF NOT EXISTS mod_file (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    mod_id            BIGINT       NOT NULL,
    file_name         VARCHAR(255) NOT NULL,
    file_path         VARCHAR(500) NOT NULL COMMENT 'Absolute path to .aimg1 file',
    file_size         BIGINT       NOT NULL DEFAULT 0,
    encryption_format VARCHAR(32)  NOT NULL DEFAULT 'AIMG1',
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mod_id (mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
