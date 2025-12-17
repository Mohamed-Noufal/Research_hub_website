-- Migration: Add Summary Table Configuration and Custom Fields
-- Description: Tables for storing user-specific table configurations and custom field values

-- Table for storing table column configurations per user/project
CREATE TABLE IF NOT EXISTS table_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    tab_name VARCHAR(50) NOT NULL CHECK (tab_name IN ('summary', 'methodology', 'findings', 'comparison', 'synthesis', 'analysis')),
    columns JSONB NOT NULL DEFAULT '[]',
    filters JSONB DEFAULT '[]',
    sort_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, tab_name)
);

-- Table for storing custom field values
CREATE TABLE IF NOT EXISTS custom_field_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    field_id VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id, field_id)
);

-- Table for project-paper associations (if not exists)
CREATE TABLE IF NOT EXISTS project_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    added_by UUID REFERENCES users(id),
    UNIQUE(project_id, paper_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_table_configs_user_project ON table_configs(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_values_user_project ON custom_field_values(user_id, project_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_values_paper ON custom_field_values(paper_id);
CREATE INDEX IF NOT EXISTS idx_project_papers_project ON project_papers(project_id);
CREATE INDEX IF NOT EXISTS idx_project_papers_paper ON project_papers(paper_id);

-- Add updated_at trigger for table_configs
CREATE OR REPLACE FUNCTION update_table_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER table_configs_updated_at
    BEFORE UPDATE ON table_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_table_configs_updated_at();

-- Add updated_at trigger for custom_field_values
CREATE OR REPLACE FUNCTION update_custom_field_values_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER custom_field_values_updated_at
    BEFORE UPDATE ON custom_field_values
    FOR EACH ROW
    EXECUTE FUNCTION update_custom_field_values_updated_at();
