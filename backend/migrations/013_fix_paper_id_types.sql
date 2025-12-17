-- Migration to fix paper_id type mismatches in literature review tables
-- Issue: findings.paper_id and methodology_data.paper_id are TEXT but papers.id is INTEGER
-- This causes "operator does not exist: integer = text" errors in JOIN queries

-- Migration: Fix Literature Review Type Mismatches
-- Created: 2025-12-07
-- Description: Convert paper_id columns from TEXT to INTEGER to match papers.id type

BEGIN;

-- Fix findings table
-- Convert paper_id from TEXT to INTEGER
ALTER TABLE findings 
ALTER COLUMN paper_id TYPE INTEGER USING paper_id::integer;

-- Fix methodology_data table
-- Convert paper_id from TEXT to INTEGER  
ALTER TABLE methodology_data 
ALTER COLUMN paper_id TYPE INTEGER USING paper_id::integer;

-- Verify the changes
DO $$
DECLARE
    findings_type TEXT;
    methodology_type TEXT;
BEGIN
    SELECT data_type INTO findings_type
    FROM information_schema.columns
    WHERE table_name = 'findings' AND column_name = 'paper_id';
    
    SELECT data_type INTO methodology_type
    FROM information_schema.columns
    WHERE table_name = 'methodology_data' AND column_name = 'paper_id';
    
    RAISE NOTICE 'findings.paper_id type: %', findings_type;
    RAISE NOTICE 'methodology_data.paper_id type: %', methodology_type;
    
    IF findings_type != 'integer' OR methodology_type != 'integer' THEN
        RAISE EXCEPTION 'Migration failed: Types not converted correctly';
    END IF;
    
    RAISE NOTICE 'Migration successful!';
END $$;

COMMIT;
