-- Migration 011: Create processed_data table for AI Services
-- STAGE 2: Python AI Services - Database Schema
-- Date: 2025-06-14

-- Drop table if exists (for clean recreation)
DROP TABLE IF EXISTS processed_data;

-- Create processed_data table
CREATE TABLE processed_data (
    id SERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES posts_cache(id) ON DELETE CASCADE,
    public_bot_id INTEGER NOT NULL REFERENCES public_bots(id) ON DELETE CASCADE,
    summaries JSONB NOT NULL,
    categories JSONB NOT NULL,
    metrics JSONB NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_version VARCHAR(50) DEFAULT 'v1.0',
    
    -- Unique constraint to prevent duplicate processing
    CONSTRAINT uq_processed_post_bot UNIQUE (post_id, public_bot_id)
);

-- Create indexes for performance
CREATE INDEX idx_processed_data_post_id ON processed_data(post_id);
CREATE INDEX idx_processed_data_bot_id ON processed_data(public_bot_id);
CREATE INDEX idx_processed_data_processed_at ON processed_data(processed_at);
CREATE INDEX idx_processed_data_version ON processed_data(processing_version);

-- Add comments
COMMENT ON TABLE processed_data IS 'AI processing results for posts by public bots';
COMMENT ON COLUMN processed_data.summaries IS 'AI-generated summaries in JSONB format';
COMMENT ON COLUMN processed_data.categories IS 'AI-generated categories and relevance scores in JSONB format';
COMMENT ON COLUMN processed_data.metrics IS 'AI-generated metrics (importance, urgency, significance) in JSONB format';
COMMENT ON COLUMN processed_data.processing_version IS 'Version of AI processing pipeline used';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON processed_data TO digest_bot;
GRANT USAGE, SELECT ON SEQUENCE processed_data_id_seq TO digest_bot; 