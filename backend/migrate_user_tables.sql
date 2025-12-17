-- Migration script to add user data tables to ResearchHub
-- Run this after the existing papers table is set up

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create local users table (no authentication required)
CREATE TABLE IF NOT EXISTS local_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    device_info JSONB
);

-- Create user saved papers table
CREATE TABLE IF NOT EXISTS user_saved_papers (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',
    personal_notes TEXT,
    read_status VARCHAR(20) DEFAULT 'unread',
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    UNIQUE(user_id, paper_id)  -- Prevent duplicate saves
);

-- Create user notes table
CREATE TABLE IF NOT EXISTS user_notes (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    paper_id INTEGER REFERENCES papers(id) ON DELETE SET NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'markdown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user literature reviews table
CREATE TABLE IF NOT EXISTS user_literature_reviews (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    paper_ids INTEGER[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user uploads table
CREATE TABLE IF NOT EXISTS user_uploads (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create user search history table
CREATE TABLE IF NOT EXISTS user_search_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES local_users(id) ON DELETE CASCADE,
    query VARCHAR(500) NOT NULL,
    category VARCHAR(50),
    results_count INTEGER DEFAULT 0,
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_user_id ON user_saved_papers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_paper_id ON user_saved_papers(paper_id);
CREATE INDEX IF NOT EXISTS idx_user_notes_user_id ON user_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notes_paper_id ON user_notes(paper_id);
CREATE INDEX IF NOT EXISTS idx_user_literature_reviews_user_id ON user_literature_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_user_uploads_user_id ON user_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_user_search_history_user_id ON user_search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_search_history_searched_at ON user_search_history(searched_at);

-- Update trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for automatic updated_at
DROP TRIGGER IF EXISTS update_user_notes_updated_at ON user_notes;
CREATE TRIGGER update_user_notes_updated_at
    BEFORE UPDATE ON user_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_literature_reviews_updated_at ON user_literature_reviews;
CREATE TRIGGER update_user_literature_reviews_updated_at
    BEFORE UPDATE ON user_literature_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a test user for development
INSERT INTO local_users (id, device_info)
VALUES ('550e8400-e29b-41d4-a716-446655440000', '{"browser": "development", "platform": "test"}')
ON CONFLICT (id) DO NOTHING;

-- Verify tables were created
SELECT
    'local_users' as table_name,
    COUNT(*) as record_count
FROM local_users
UNION ALL
SELECT 'user_saved_papers', COUNT(*) FROM user_saved_papers
UNION ALL
SELECT 'user_notes', COUNT(*) FROM user_notes
UNION ALL
SELECT 'user_literature_reviews', COUNT(*) FROM user_literature_reviews
UNION ALL
SELECT 'user_uploads', COUNT(*) FROM user_uploads
UNION ALL
SELECT 'user_search_history', COUNT(*) FROM user_search_history;
