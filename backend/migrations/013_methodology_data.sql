-- Migration: Methodology Explorer Backend Integration
-- Creates table for storing methodology data per paper

CREATE TABLE IF NOT EXISTS methodology_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    paper_id UUID NOT NULL,
    
    -- Core methodology fields (editable)
    methodology_description TEXT, -- "The Approach" column
    methodology_context TEXT,     -- "Previous Context" column
    approach_novelty TEXT,         -- "Why It's Different" column
    
    -- Additional custom fields
    custom_attributes JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_methodology_data_project ON methodology_data(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_methodology_data_paper ON methodology_data(paper_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_methodology_data_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER methodology_data_updated_at
    BEFORE UPDATE ON methodology_data
    FOR EACH ROW
    EXECUTE FUNCTION update_methodology_data_updated_at();
