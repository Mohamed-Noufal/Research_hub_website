-- Migration: 023_file_tracking_and_processing.sql
-- Adds file tracking and processing status columns to papers table
-- This supports:
--   1. Background processing (Celery)
--   2. Duplicate PDF detection
--   3. File location tracking

-- File tracking columns
ALTER TABLE papers ADD COLUMN IF NOT EXISTS local_file_path TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Processing status columns (for background jobs)
ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE papers ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_papers_processing_status ON papers(processing_status);
CREATE INDEX IF NOT EXISTS idx_papers_file_hash ON papers(file_hash);
CREATE INDEX IF NOT EXISTS idx_papers_user_id ON papers(user_id);

-- Update existing papers to 'completed' if they have embeddings
UPDATE papers 
SET processing_status = 'completed' 
WHERE embedding IS NOT NULL AND processing_status = 'pending';
