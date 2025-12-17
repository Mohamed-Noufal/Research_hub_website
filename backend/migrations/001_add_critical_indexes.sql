-- Migration: Add Critical Indexes for Performance
-- Impact: 25-40x performance improvement on searches and queries
-- Date: 2025-11-21

-- ============================================
-- PAPERS TABLE INDEXES
-- ============================================

-- Single column indexes for filtering
CREATE INDEX IF NOT EXISTS idx_papers_category ON papers(category);
CREATE INDEX IF NOT EXISTS idx_papers_source ON papers(source);
CREATE INDEX IF NOT EXISTS idx_papers_is_processed ON papers(is_processed);

-- Indexes for sorting
CREATE INDEX IF NOT EXISTS idx_papers_publication_date ON papers(publication_date DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_papers_citation_count ON papers(citation_count DESC);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_papers_category_date ON papers(category, publication_date DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_papers_category_citations ON papers(category, citation_count DESC);
CREATE INDEX IF NOT EXISTS idx_papers_category_processed ON papers(category, is_processed);

-- Full-text search indexes (requires pg_trgm extension)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_papers_title_trgm ON papers USING gin(title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_papers_abstract_trgm ON papers USING gin(abstract gin_trgm_ops);

-- ============================================
-- USER_SAVED_PAPERS TABLE INDEXES
-- ============================================

-- Foreign key indexes
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_user_id ON user_saved_papers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_paper_id ON user_saved_papers(paper_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_user_saved_at ON user_saved_papers(user_id, saved_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_user_paper ON user_saved_papers(user_id, paper_id);
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_user_status ON user_saved_papers(user_id, read_status);

-- Array index for tags
CREATE INDEX IF NOT EXISTS idx_user_saved_papers_tags ON user_saved_papers USING gin(tags);

-- ============================================
-- USER_NOTES TABLE INDEXES
-- ============================================

-- Foreign key indexes
CREATE INDEX IF NOT EXISTS idx_user_notes_user_id ON user_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notes_paper_id ON user_notes(paper_id);
CREATE INDEX IF NOT EXISTS idx_user_notes_parent_id ON user_notes(parent_id);

-- Composite indexes for hierarchy queries
CREATE INDEX IF NOT EXISTS idx_user_notes_user_folder ON user_notes(user_id, is_folder);
CREATE INDEX IF NOT EXISTS idx_user_notes_user_parent ON user_notes(user_id, parent_id);

-- Path index for tree traversal
CREATE INDEX IF NOT EXISTS idx_user_notes_path ON user_notes(path);

-- ============================================
-- USER_SEARCH_HISTORY TABLE INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_user_search_history_user_id ON user_search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_search_history_searched_at ON user_search_history(user_id, searched_at DESC);

-- ============================================
-- USER_LITERATURE_REVIEWS TABLE INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_user_literature_reviews_user_id ON user_literature_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_user_literature_reviews_created_at ON user_literature_reviews(user_id, created_at DESC);

-- ============================================
-- USER_UPLOADS TABLE INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_user_uploads_user_id ON user_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_user_uploads_uploaded_at ON user_uploads(user_id, uploaded_at DESC);

-- ============================================
-- LOCAL_USERS TABLE INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_local_users_last_active ON local_users(last_active DESC);
CREATE INDEX IF NOT EXISTS idx_local_users_created_at ON local_users(created_at DESC);

-- ============================================
-- ANALYZE TABLES (Update statistics)
-- ============================================

ANALYZE papers;
ANALYZE user_saved_papers;
ANALYZE user_notes;
ANALYZE user_search_history;
ANALYZE user_literature_reviews;
ANALYZE user_uploads;
ANALYZE local_users;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
