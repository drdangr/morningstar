-- Migration 015: Create processed_service_results table for per-service AI results
-- Run this after 014_add_top_p_to_config_settings.sql

-- ----------------------------
-- 1. Create table
-- ----------------------------
CREATE TABLE IF NOT EXISTS processed_service_results (
    id              SERIAL PRIMARY KEY,
    post_id         BIGINT      NOT NULL,
    public_bot_id   INTEGER     NOT NULL,
    service_name    VARCHAR(64) NOT NULL,
    status          VARCHAR(32) DEFAULT 'success',
    payload         JSONB       NOT NULL DEFAULT '{}',
    metrics         JSONB       NOT NULL DEFAULT '{}',
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (post_id, public_bot_id, service_name)
);

-- ----------------------------
-- 2. Recommended index for fast look-ups
-- ----------------------------
CREATE INDEX IF NOT EXISTS idx_psr_post_bot_service ON processed_service_results (post_id, public_bot_id, service_name);

-- ----------------------------
-- 3. No FK constraints because of partitioning / performance considerations
-- ----------------------------
-- (We rely on application-level consistency) 