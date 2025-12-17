-- Add user_id column to papers table
-- This is needed to associate papers with specific users

-- Add user_id column (nullable first to allow existing records)
ALTER TABLE papers ADD COLUMN IF NOT EXISTS user_id UUID;

-- Create index for faster user paper lookups
CREATE INDEX IF NOT EXISTS idx_papers_user_id ON papers(user_id);

-- Update existing papers to have a default user_id if needed (optional)
-- UPDATE papers SET user_id = '550e8400-e29b-41d4-a716-446655440000' WHERE user_id IS NULL;
