-- Migration 013: Add boolean flags to processed_data for service-independent tracking
-- Date: 2025-06-28
-- Purpose: Replace status-based tracking with boolean flags for each service
--          This allows services to work independently without blocking each other

-- Drop the old CHECK constraint that doesn't include 'processing' status
ALTER TABLE processed_data
DROP CONSTRAINT IF EXISTS chk_processing_status;

-- Add new CHECK constraint with updated status values
ALTER TABLE processed_data
ADD CONSTRAINT chk_processing_status_v2
CHECK (processing_status IN ('not_found', 'pending', 'processing', 'completed', 'failed'));

-- Add boolean flags for tracking what services have been completed
ALTER TABLE processed_data 
ADD COLUMN IF NOT EXISTS is_categorized BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_summarized BOOLEAN DEFAULT FALSE;

-- Add indexes for efficient filtering by flags
CREATE INDEX IF NOT EXISTS idx_processed_data_is_categorized ON processed_data (is_categorized);
CREATE INDEX IF NOT EXISTS idx_processed_data_is_summarized ON processed_data (is_summarized);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_processed_data_bot_flags ON processed_data (public_bot_id, is_categorized, is_summarized);

-- Backfill existing data based on content
UPDATE processed_data 
SET 
    is_categorized = CASE 
        WHEN categories IS NOT NULL AND categories != '{}'::jsonb THEN TRUE 
        ELSE FALSE 
    END,
    is_summarized = CASE 
        WHEN summaries IS NOT NULL AND summaries != '{}'::jsonb THEN TRUE 
        ELSE FALSE 
    END;

-- Update processing_status based on flags
UPDATE processed_data
SET processing_status = CASE
    WHEN is_categorized = TRUE AND is_summarized = TRUE THEN 'completed'
    WHEN is_categorized = TRUE OR is_summarized = TRUE THEN 'processing'
    WHEN processing_status = 'categorized' OR processing_status = 'summarized' THEN 'processing'
    ELSE processing_status
END;

-- Add comments explaining the new architecture
COMMENT ON COLUMN processed_data.is_categorized IS 
'Flag indicating if categorization service has processed this post';

COMMENT ON COLUMN processed_data.is_summarized IS 
'Flag indicating if summarization service has processed this post';

-- Update the processing_status comment
COMMENT ON COLUMN processed_data.processing_status IS 
'Overall processing status: not_found → pending → processing → completed. Use flags for service-specific status'; 