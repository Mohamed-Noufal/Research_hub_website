-- Migration: Comparison Tab Backend Integration
-- Creates tables for comparison configurations and custom attributes

-- Comparison Configurations Table
CREATE TABLE IF NOT EXISTS comparison_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    
    selected_paper_ids TEXT[] NOT NULL DEFAULT '{}', -- Array of paper IDs
    insights_similarities TEXT, -- Editable similarities text
    insights_differences TEXT, -- Editable differences text
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

-- Comparison Attributes Table (for custom comparison rows)
CREATE TABLE IF NOT EXISTS comparison_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    paper_id TEXT NOT NULL,
    
    attribute_name VARCHAR(100) NOT NULL,
    attribute_value TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id, attribute_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_comparison_configs_project ON comparison_configs(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_comparison_attributes_project ON comparison_attributes(project_id, user_id);

-- Triggers
CREATE OR REPLACE FUNCTION update_comparison_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER comparison_configs_updated_at
    BEFORE UPDATE ON comparison_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_comparison_configs_updated_at();

CREATE OR REPLACE FUNCTION update_comparison_attributes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER comparison_attributes_updated_at
    BEFORE UPDATE ON comparison_attributes
    FOR EACH ROW
    EXECUTE FUNCTION update_comparison_attributes_updated_at();
