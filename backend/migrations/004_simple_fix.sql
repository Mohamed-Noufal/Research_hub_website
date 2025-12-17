-- Fix folders table schema to use UUID for user_id
-- Drop existing tables if they exist
DROP TABLE IF EXISTS folder_papers;
DROP TABLE IF EXISTS folders;

-- Create folders table with UUID user_id
CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
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
    paper_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (folder_id, paper_id)
);

-- Create indexes for faster lookups
CREATE INDEX idx_folder_papers_folder ON folder_papers(folder_id);
CREATE INDEX idx_folder_papers_paper ON folder_papers(paper_id);

-- Add is_manual column to papers table if it doesn't exist
ALTER TABLE papers ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE;

-- Add index for manual papers if not exists
CREATE INDEX IF NOT EXISTS idx_papers_is_manual ON papers(is_manual);
