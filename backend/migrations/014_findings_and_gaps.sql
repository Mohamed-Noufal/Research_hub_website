-- Migration: Findings & Gaps Backend Integration
-- Creates tables for research gaps and findings

-- Research Gaps Table
CREATE TABLE IF NOT EXISTS research_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('High', 'Medium', 'Low')),
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Gap-Paper Associations (many-to-many)
CREATE TABLE IF NOT EXISTS gap_paper_associations (
    gap_id UUID REFERENCES research_gaps(id) ON DELETE CASCADE,
    paper_id UUID,
    PRIMARY KEY (gap_id, paper_id)
);

-- Findings Table (per paper)
CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL,
    paper_id UUID NOT NULL,
    
    key_finding TEXT,
    limitations TEXT,
    custom_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, project_id, paper_id)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_research_gaps_project ON research_gaps(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_findings_project ON findings(project_id, user_id);
CREATE INDEX IF NOT EXISTS idx_findings_paper ON findings(paper_id);

-- Triggers to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_research_gaps_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER research_gaps_updated_at
    BEFORE UPDATE ON research_gaps
    FOR EACH ROW
    EXECUTE FUNCTION update_research_gaps_updated_at();

CREATE OR REPLACE FUNCTION update_findings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER findings_updated_at
    BEFORE UPDATE ON findings
    FOR EACH ROW
    EXECUTE FUNCTION update_findings_updated_at();
