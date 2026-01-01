-- Migration for Advanced RAG System

-- 1. Enable vector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Update paper_chunks table for Hybrid Search & Hierarchical Chunking
-- Note: We drop and recreate because embedding dimension is changing (384 -> 768)
DROP TABLE IF EXISTS paper_chunks CASCADE;

CREATE TABLE paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    
    -- Semantic Hierarchy
    parent_id UUID REFERENCES paper_chunks(id), -- For Parent/Child retrieval
    level INTEGER DEFAULT 0,                    -- 0=Child, 1=Parent
    
    -- Content
    section_type VARCHAR(50),  -- 'abstract', 'methodology', 'results', etc.
    text TEXT NOT NULL,
    
    -- Embeddings (Updated to 768 for Nomic)
    embedding vector(768),
    
    -- Metadata for Hybrid Search
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',  -- Must contain 'keywords' for BM25
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(paper_id, chunk_index, level) -- Allow same index at different levels
);

-- Indices for fast search
CREATE INDEX idx_paper_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX idx_paper_chunks_parent ON paper_chunks(parent_id);

-- IVFFlat index for vector search (Cosine Similarity)
-- Lists = 100 is good for < 1M vectors
CREATE INDEX idx_paper_chunks_embedding 
ON paper_chunks USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- GIN index for metadata filtering (Hybrid Search)
CREATE INDEX idx_paper_chunks_metadata ON paper_chunks USING gin (metadata);

-- 3. Knowledge Base Tracking Table
-- Tracks which papers are indexed in the KB for each project
CREATE TABLE IF NOT EXISTS knowledge_base_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    
    -- Status Tracking
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'indexed', 'failed')),
    error_message TEXT,
    
    -- Stats
    chunks_count INTEGER DEFAULT 0,
    last_indexed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Enforce limits per project/user
    UNIQUE(user_id, project_id, paper_id)
);

CREATE INDEX idx_kb_papers_project ON knowledge_base_papers(project_id);
CREATE INDEX idx_kb_papers_user_project ON knowledge_base_papers(user_id, project_id);
