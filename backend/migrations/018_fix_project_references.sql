-- Migration: Fix Project References and Create Missing Tables (Corrected)
-- Description: Align all feature tables to use user_literature_reviews(id) [Integer]
-- and local_users(id) [UUID]. Drops and recreates incorrect/missing tables.
-- Corrects comparison_attributes schema.

-- 1. Table Configs (Summary Tab)
DROP TABLE IF EXISTS table_configs;
CREATE TABLE table_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    tab_name VARCHAR(50) NOT NULL CHECK (tab_name IN ('summary', 'methodology', 'findings', 'comparison', 'synthesis', 'analysis')),
    columns JSONB NOT NULL DEFAULT '[]',
    filters JSONB DEFAULT '[]',
    sort_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, tab_name)
);
CREATE INDEX idx_table_configs_project ON table_configs(project_id);

-- 2. Custom Field Values
DROP TABLE IF EXISTS custom_field_values;
CREATE TABLE custom_field_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    field_id VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id, field_id)
);
CREATE INDEX idx_custom_field_values_project ON custom_field_values(project_id);

-- 3. Project Papers
DROP TABLE IF EXISTS project_papers;
CREATE TABLE project_papers (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    added_by UUID REFERENCES local_users(id),
    UNIQUE(project_id, paper_id)
);
CREATE INDEX idx_project_papers_project ON project_papers(project_id);

-- 4. Methodology Data
DROP TABLE IF EXISTS methodology_data;
CREATE TABLE methodology_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    
    -- Methodology Fields
    methodology_description TEXT,
    methodology_context TEXT,
    approach_novelty TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id)
);
CREATE INDEX idx_methodology_data_project ON methodology_data(project_id);

-- 5. Findings & Gaps
DROP TABLE IF EXISTS research_gaps;
CREATE TABLE research_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    
    description TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'Medium', -- High, Medium, Low
    status VARCHAR(50) DEFAULT 'Open',     -- Open, In Progress, Addressed
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_research_gaps_project ON research_gaps(project_id);

DROP TABLE IF EXISTS gap_paper_associations;
CREATE TABLE gap_paper_associations (
    gap_id UUID NOT NULL REFERENCES research_gaps(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    contribution_type VARCHAR(50), -- addresses, highlights, confirms
    
    UNIQUE(gap_id, paper_id)
);

DROP TABLE IF EXISTS findings;
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    
    key_finding TEXT,
    limitations TEXT,
    custom_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id)
);
CREATE INDEX idx_findings_project ON findings(project_id);

-- 6. Comparison Configs
DROP TABLE IF EXISTS comparison_configs;
CREATE TABLE comparison_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    
    selected_paper_ids INTEGER[] DEFAULT '{}',
    insights_similarities TEXT,
    insights_differences TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

DROP TABLE IF EXISTS comparison_attributes;
CREATE TABLE comparison_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    
    attribute_name VARCHAR(100) NOT NULL,
    attribute_value TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id, attribute_name)
);

-- 7. Synthesis Configs
DROP TABLE IF EXISTS synthesis_configs;
CREATE TABLE synthesis_configs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    
    columns JSONB NOT NULL DEFAULT '[]',
    rows JSONB NOT NULL DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);

DROP TABLE IF EXISTS synthesis_cells;
CREATE TABLE synthesis_cells (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    
    row_id VARCHAR(100) NOT NULL,
    column_id VARCHAR(100) NOT NULL,
    value TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, row_id, column_id)
);

-- 8. Analysis Configs
DROP TABLE IF EXISTS analysis_configs;
CREATE TABLE analysis_configs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    
    chart_preferences JSONB DEFAULT '{}',
    custom_metrics JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id)
);
