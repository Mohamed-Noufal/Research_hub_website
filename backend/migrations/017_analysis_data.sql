-- Migration: Analysis & Visuals Tab Backend Integration
-- Creates table for analysis chart preferences

-- Analysis Configurations Table (stores chart preferences)
CREATE TABLE IF NOT EXISTS analysis_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    
    chart_preferences JSONB DEFAULT '{}', -- Chart customization
    custom_metrics JSONB DEFAULT '[]',   -- Custom quality metrics
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_analysis_configs_project ON analysis_configs(project_id, user_id);

-- Triggers
CREATE OR REPLACE FUNCTION update_analysis_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER analysis_configs_updated_at
    BEFORE UPDATE ON analysis_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_analysis_configs_updated_at();
