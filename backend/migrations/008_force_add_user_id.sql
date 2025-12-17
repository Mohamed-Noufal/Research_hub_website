-- Force add user_id column to papers table
ALTER TABLE papers ADD COLUMN user_id UUID;
CREATE INDEX idx_papers_user_id ON papers(user_id);
