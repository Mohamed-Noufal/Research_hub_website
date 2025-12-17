-- Migration: Synthesis Tab Backend Integration
-- Creates tables for synthesis table structure and cell values

-- Synthesis Configurations Table (stores table structure)
CREATE TABLE IF NOT EXISTS synthesis_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    
    columns JSONB NOT NULL DEFAULT '[]', -- Column definitions
    rows JSONB NOT NULL DEFAULT '[]',    -- Row definitions
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

-- Synthesis Cells Table (stores cell values)
CREATE TABLE IF NOT EXISTS synthesis_cells (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    
    row_id VARCHAR(100) NOT NULL,
    column_id VARCHAR(100) NOT NULL,
    value TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, row_id, column_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_synthesis_configs_project ON synthesis_configs(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_synthesis_cells_project ON synthesis_cells(project_id, user_id);

-- Triggers
CREATE OR REPLACE FUNCTION update_synthesis_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER synthesis_configs_updated_at
    BEFORE UPDATE ON synthesis_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_synthesis_configs_updated_at();

CREATE OR REPLACE FUNCTION update_synthesis_cells_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER synthesis_cells_updated_at
    BEFORE UPDATE ON synthesis_cells
    FOR EACH ROW
    EXECUTE FUNCTION update_synthesis_cells_updated_at();
