-- Create folders table
CREATE TABLE IF NOT EXISTS folders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster user folder lookups
CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders(user_id);

-- Create folder_papers junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS folder_papers (
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (folder_id, paper_id)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_folder_papers_folder ON folder_papers(folder_id);
CREATE INDEX IF NOT EXISTS idx_folder_papers_paper ON folder_papers(paper_id);

-- Add is_manual column to papers table to track manually created papers
ALTER TABLE papers ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE;

-- Add index for manual papers
CREATE INDEX IF NOT EXISTS idx_papers_is_manual ON papers(is_manual);
