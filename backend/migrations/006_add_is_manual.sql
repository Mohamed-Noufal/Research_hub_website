-- Add is_manual column to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE;

-- Create index for manual papers
CREATE INDEX IF NOT EXISTS idx_papers_is_manual ON papers(is_manual);
