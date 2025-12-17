-- Literature Review Research Analysis Features - Migration 010
-- Adds citation management, paper comparisons, and advanced analysis

-- Enhance research findings with relationships
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS citation_count INTEGER DEFAULT 0;
ALTER TABLE research_findings ADD COLUMN IF NOT EXISTS methodology_match JSONB;

-- Create paper comparison data
CREATE TABLE IF NOT EXISTS paper_comparisons (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_ids INTEGER[] NOT NULL, -- Papers being compared
    comparison_data JSONB, -- Methodology, sample, results comparison
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create citation templates and formatting
CREATE TABLE IF NOT EXISTS citation_formats (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    format_type VARCHAR(50), -- 'APA', 'MLA', 'Chicago', 'Harvard'
    custom_template TEXT, -- Optional custom format
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create research themes for analysis
CREATE TABLE IF NOT EXISTS research_themes (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    theme_name VARCHAR(255) NOT NULL,
    theme_description TEXT,
    supporting_findings INTEGER[] DEFAULT '{}', -- Array of finding IDs
    paper_count INTEGER DEFAULT 0,
    theme_strength VARCHAR(50), -- strong, moderate, weak
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_paper_comparisons_project ON paper_comparisons(project_id);
CREATE INDEX IF NOT EXISTS idx_citation_formats_project ON citation_formats(project_id);
CREATE INDEX IF NOT EXISTS idx_research_themes_project ON research_themes(project_id);
CREATE INDEX IF NOT EXISTS idx_research_themes_name ON research_themes(theme_name);

-- Add triggers for updated_at columns
DROP TRIGGER IF EXISTS update_paper_comparisons_updated_at ON paper_comparisons;
CREATE TRIGGER update_paper_comparisons_updated_at
    BEFORE UPDATE ON paper_comparisons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_citation_formats_updated_at ON citation_formats;
CREATE TRIGGER update_citation_formats_updated_at
    BEFORE UPDATE ON citation_formats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_research_themes_updated_at ON research_themes;
CREATE TRIGGER update_research_themes_updated_at
    BEFORE UPDATE ON research_themes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ROLLBACK SQL (for reference)
-- DROP TABLE IF EXISTS paper_comparisons CASCADE;
-- DROP TABLE IF EXISTS citation_formats CASCADE;
-- DROP TABLE IF EXISTS research_themes CASCADE;
-- ALTER TABLE research_findings DROP COLUMN IF EXISTS citation_count;
-- ALTER TABLE research_findings DROP COLUMN IF EXISTS methodology_match;
