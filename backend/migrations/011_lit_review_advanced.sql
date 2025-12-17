-- Literature Review Advanced Features - Migration 011
-- Adds Excel-like editor, AI synthesis, and export functionality

-- Create Excel-like spreadsheet editor table
CREATE TABLE IF NOT EXISTS spreadsheet_templates (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    template_name VARCHAR(255) NOT NULL,
    template_config JSONB, -- Column definitions, cell types, validation rules
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spreadsheet data storage
CREATE TABLE IF NOT EXISTS spreadsheet_data (
    id SERIAL PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES spreadsheet_templates(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    row_data JSONB NOT NULL, -- Individual row data
    cell_data JSONB, -- Individual cell configurations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create AI synthesis and reporting
CREATE TABLE IF NOT EXISTS ai_synthesis (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    synthesis_type VARCHAR(50), -- 'summary', 'comparison', 'theme_analysis', 'methodology', 'gap_analysis'
    input_data JSONB, -- Data used for synthesis
    ai_prompt TEXT NOT NULL,
    ai_response TEXT,
    confidence_score FLOAT,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create export configurations
CREATE TABLE IF NOT EXISTS export_configurations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    export_type VARCHAR(50), -- 'word', 'excel', 'pdf', 'csv'
    template_name VARCHAR(255),
    configuration JSONB, -- Format-specific configuration
    output_path VARCHAR(500), -- Generated file path
    status VARCHAR(50) DEFAULT 'draft', -- draft, generating, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create custom analysis templates
CREATE TABLE IF NOT EXISTS analysis_templates (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    template_type VARCHAR(50), -- 'comparison_matrix', 'evidence_table', 'methodology_table'
    template_config JSONB NOT NULL,
    custom_fields JSONB, -- Additional fields beyond standard
    is_public BOOLEAN DEFAULT FALSE, -- Shareable templates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhance existing UserLiteratureReview with Phase 3 capabilities
ALTER TABLE user_literature_reviews 
ADD COLUMN IF NOT EXISTS ai_features_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS advanced_analytics JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS custom_views JSONB DEFAULT '{}';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_spreadsheet_templates_project ON spreadsheet_templates(project_id);
CREATE INDEX IF NOT EXISTS idx_spreadsheet_data_template ON spreadsheet_data(template_id);
CREATE INDEX IF NOT EXISTS idx_ai_synthesis_project ON ai_synthesis(project_id);
CREATE INDEX IF NOT EXISTS idx_ai_synthesis_status ON ai_synthesis(status);
CREATE INDEX IF NOT EXISTS idx_export_configurations_project ON export_configurations(project_id);
CREATE INDEX IF NOT EXISTS idx_analysis_templates_project ON analysis_templates(project_id);

-- Add triggers for updated_at columns
DROP TRIGGER IF EXISTS update_spreadsheet_templates_updated_at ON spreadsheet_templates;
CREATE TRIGGER update_spreadsheet_templates_updated_at
    BEFORE UPDATE ON spreadsheet_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_spreadsheet_data_updated_at ON spreadsheet_data;
CREATE TRIGGER update_spreadsheet_data_updated_at
    BEFORE UPDATE ON spreadsheet_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_synthesis_updated_at ON ai_synthesis;
CREATE TRIGGER update_ai_synthesis_updated_at
    BEFORE UPDATE ON ai_synthesis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_export_configurations_updated_at ON export_configurations;
CREATE TRIGGER update_export_configurations_updated_at
    BEFORE UPDATE ON export_configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_analysis_templates_updated_at ON analysis_templates;
CREATE TRIGGER update_analysis_templates_updated_at
    BEFORE UPDATE ON analysis_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ROLLBACK SQL (for reference)
-- DROP TABLE IF EXISTS spreadsheet_templates CASCADE;
-- DROP TABLE IF EXISTS spreadsheet_data CASCADE;
-- DROP TABLE IF EXISTS ai_synthesis CASCADE;
-- DROP TABLE IF EXISTS export_configurations CASCADE;
-- DROP TABLE IF EXISTS analysis_templates CASCADE;
-- ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS ai_features_enabled;
-- ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS advanced_analytics;
-- ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS custom_views;
