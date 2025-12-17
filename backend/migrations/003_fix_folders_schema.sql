-- Fix folders table schema to use UUID for user_id
-- Drop existing tables if they exist
DROP TABLE IF EXISTS folder_papers;
DROP TABLE IF EXISTS folders;

-- Create folders table with UUID user_id
CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL, -- Removed foreign key constraint for now to avoid issues if local_users doesn't exist or has different schema
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster user folder lookups
CREATE INDEX idx_folders_user_id ON folders(user_id);

-- Create folder_papers junction table (many-to-many relationship)
CREATE TABLE folder_papers (
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL, -- Removed foreign key to papers to avoid issues if papers table doesn't exist yet
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (folder_id, paper_id)
);

-- Create indexes for faster lookups
CREATE INDEX idx_folder_papers_folder ON folder_papers(folder_id);
CREATE INDEX idx_folder_papers_paper ON folder_papers(paper_id);

-- Ensure is_manual column exists in papers table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'papers' AND column_name = 'is_manual') THEN
        ALTER TABLE papers ADD COLUMN is_manual BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Add index for manual papers if not exists
CREATE INDEX IF NOT EXISTS idx_papers_is_manual ON papers(is_manual);
