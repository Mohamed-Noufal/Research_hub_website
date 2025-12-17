-- Initialize database with vector extensions
-- This file runs automatically when the PostgreSQL container starts

-- Connect to the research_db database
\c research_db;

-- Create pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extensions are loaded
\dx vector;

-- Optional: Create placeholder tables for testing (will be created by app)
-- The app will create the 'papers' table with vector column

SELECT '✅ PostgreSQL with pgvector initialized successfully' AS status;
