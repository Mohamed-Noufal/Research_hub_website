-- Migration: Add missing columns to user_literature_reviews table
-- Date: 2025-12-04
-- Description: Adds columns that exist in SQLAlchemy model but not in database

-- Add missing columns to user_literature_reviews table
ALTER TABLE user_literature_reviews 
  ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft',
  ADD COLUMN IF NOT EXISTS review_metadata JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS export_data JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS ai_features_enabled BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS advanced_analytics JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS custom_views JSONB DEFAULT '{}';

-- Verify the columns were added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_literature_reviews'
ORDER BY ordinal_position;
