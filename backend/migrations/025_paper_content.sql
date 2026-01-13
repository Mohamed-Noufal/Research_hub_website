-- Migration 025: Paper Content Tables for RAG System
-- Stores parsed PDF content: sections, figures, tables, equations

-- Enable vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Table 1: paper_sections (Text Sections)
-- ============================================
CREATE TABLE IF NOT EXISTS paper_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
    
    -- Section info
    section_type VARCHAR(50) NOT NULL,  -- 'abstract', 'introduction', 'methodology', 'results', 'discussion', 'conclusion', 'references'
    section_title VARCHAR(500),
    content TEXT NOT NULL,
    word_count INTEGER,
    order_index INTEGER DEFAULT 0,
    page_start INTEGER,
    page_end INTEGER,
    
    -- Embedding for semantic search
    embedding vector(768),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_paper_sections_paper ON paper_sections(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_sections_user ON paper_sections(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_sections_type ON paper_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_paper_sections_paper_type ON paper_sections(paper_id, section_type);

-- ============================================
-- Table 2: paper_figures (Images)
-- ============================================
CREATE TABLE IF NOT EXISTS paper_figures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
    
    -- Figure info
    figure_number VARCHAR(50),     -- "Figure 1", "Fig. 2a"
    caption TEXT,
    image_path VARCHAR(1000),       -- Local storage path
    image_url VARCHAR(1000),        -- URL if stored remotely
    page_number INTEGER,
    order_index INTEGER DEFAULT 0,
    
    -- Metadata
    width INTEGER,
    height INTEGER,
    format VARCHAR(20),             -- 'png', 'jpg', 'svg'
    
    -- Embedding of caption for semantic search
    embedding vector(768),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_figures_paper ON paper_figures(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_figures_user ON paper_figures(user_id);

-- ============================================
-- Table 3: paper_tables (Data Tables)
-- ============================================
CREATE TABLE IF NOT EXISTS paper_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
    
    -- Table info
    table_number VARCHAR(50),       -- "Table 1", "Table 2"
    caption TEXT,
    content_markdown TEXT,          -- Table rendered as markdown
    content_json JSONB,             -- Structured table data {headers: [], rows: [[]]}
    page_number INTEGER,
    order_index INTEGER DEFAULT 0,
    
    -- Dimensions
    row_count INTEGER,
    column_count INTEGER,
    
    -- Embedding for semantic search
    embedding vector(768),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_tables_paper ON paper_tables(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_tables_user ON paper_tables(user_id);

-- ============================================
-- Table 4: paper_equations (Math)
-- ============================================
CREATE TABLE IF NOT EXISTS paper_equations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
    
    -- Equation info
    equation_number VARCHAR(50),    -- "Eq. 1", "(1)", "Equation 3.1"
    latex TEXT NOT NULL,            -- LaTeX source
    mathml TEXT,                    -- MathML representation
    context TEXT,                   -- Surrounding text for context
    page_number INTEGER,
    order_index INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_paper_equations_paper ON paper_equations(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_equations_user ON paper_equations(user_id);

-- ============================================
-- Table 5: project_summaries (Literature Review Summaries)
-- ============================================
CREATE TABLE IF NOT EXISTS project_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INTEGER NOT NULL REFERENCES user_literature_reviews(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    
    summary_text TEXT,
    key_insights TEXT[],
    methodology_overview TEXT,
    main_findings TEXT,
    research_gaps TEXT[],
    future_directions TEXT,
    
    -- Word counts for tracking
    word_count INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_project_summaries_project ON project_summaries(project_id);
CREATE INDEX IF NOT EXISTS idx_project_summaries_user ON project_summaries(user_id);

-- ============================================
-- Update papers table with processing columns
-- ============================================
ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_error TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS section_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS figure_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS table_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS equation_count INTEGER DEFAULT 0;
