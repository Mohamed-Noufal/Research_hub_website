-- Literature Review Core Features - Migration 009
-- Extends existing UserLiteratureReview table and adds supporting tables

-- Extend existing UserLiteratureReview table with additional metadata
ALTER TABLE user_literature_reviews 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft',
ADD COLUMN IF NOT EXISTS review_metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS export_data JSONB DEFAULT '{}';

-- Create literature review annotations table
CREATE TABLE IF NOT EXISTS literature_review_annotations (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    methodology VARCHAR(100), -- 'experimental', 'survey', 'case-study', 'meta-analysis', 'review', 'other'
    sample_size VARCHAR(255),
    key_findings JSONB DEFAULT '[]', -- Array of findings
    limitations JSONB DEFAULT '[]', -- Array of limitations
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create research findings table
CREATE TABLE IF NOT EXISTS literature_review_findings (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    supporting_papers INTEGER[] DEFAULT '{}', -- Array of paper IDs
    finding_type VARCHAR(50), -- 'positive', 'negative', 'neutral'
    evidence_level VARCHAR(50), -- 'strong', 'moderate', 'weak'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_lit_review_annotations_review ON literature_review_annotations(review_id);
CREATE INDEX IF NOT EXISTS idx_lit_review_annotations_paper ON literature_review_annotations(paper_id);
CREATE INDEX IF NOT EXISTS idx_lit_review_findings_review ON literature_review_findings(review_id);

-- Add foreign key index for literature_review table
CREATE INDEX IF NOT EXISTS idx_user_literature_reviews_user ON user_literature_reviews(user_id);

-- Add updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
DROP TRIGGER IF EXISTS update_literature_review_annotations_updated_at ON literature_review_annotations;
CREATE TRIGGER update_literiterature_review_annotations_updated_at
    BEFORE UPDATE ON literature_review_annotations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_literature_review_findings_updated_at ON literature_review_findings;
CREATE TRIGGER update_literature_review_findings_updated_at
    BEFORE UPDATE ON literature_review_findings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_literature_reviews_updated_at ON user_literature_reviews;
CREATE TRIGGER update_user_literature_reviews_updated_at
    BEFORE UPDATE ON user_literature_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ROLLBACK SQL (for reference)
-- DROP TABLE IF EXISTS literature_review_annotations CASCADE;
-- DROP TABLE IF EXISTS literature_review_findings CASCADE;
-- ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS status;
-- ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS review_metadata;
-- ALTER TABLE user_literature_reviews DROP COLUMN IF EXISTS export_data;
