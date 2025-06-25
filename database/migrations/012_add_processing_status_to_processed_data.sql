-- Migration 012: Add processing_status to processed_data for multitenant status tracking
-- Date: 2025-06-24
-- Purpose: Fix architectural issue with global processing_status in posts_cache
--          Move to per-bot processing status in processed_data table

-- Add processing_status column to processed_data table
ALTER TABLE processed_data 
ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending' NOT NULL;

-- Add index for efficient status queries
CREATE INDEX idx_processed_data_status ON processed_data (processing_status);

-- Add composite index for bot_id + status queries
CREATE INDEX idx_processed_data_bot_status ON processed_data (public_bot_id, processing_status);

-- Add check constraint for valid status values
ALTER TABLE processed_data
ADD CONSTRAINT chk_processing_status 
CHECK (processing_status IN ('pending', 'categorized', 'summarized', 'completed', 'failed'));

-- Update existing records to have proper status based on data presence
UPDATE processed_data 
SET processing_status = CASE 
    WHEN summary IS NOT NULL AND category IS NOT NULL THEN 'completed'
    WHEN summary IS NOT NULL AND category IS NULL THEN 'summarized'
    WHEN summary IS NULL AND category IS NOT NULL THEN 'categorized'
    ELSE 'pending'
END;

-- Add comment explaining the status flow
COMMENT ON COLUMN processed_data.processing_status IS 
'Per-bot processing status: pending → categorized/summarized → completed'; 