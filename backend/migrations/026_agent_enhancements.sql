-- Migration 026: Agent Enhancement Tables
-- Adds tables for task checkpointing and Mem0-style memory

-- ============================================
-- Table 1: agent_task_states (Task Checkpointing)
-- ============================================
-- Purpose: Store state of long-running tasks so they can resume after failure

CREATE TABLE IF NOT EXISTS agent_task_states (
    id SERIAL PRIMARY KEY,
    task_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES user_literature_reviews(id) ON DELETE SET NULL,
    
    -- Task info
    task_type VARCHAR(50) NOT NULL,  -- 'fill_all_tabs', 'batch_methodology', etc.
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'paused')),
    current_phase VARCHAR(50),  -- 'methodology', 'findings', 'comparison', etc.
    
    -- Progress tracking
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    completed_item_ids INTEGER[] DEFAULT '{}',
    failed_item_ids INTEGER[] DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_agent_task_states_user ON agent_task_states(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_task_states_project ON agent_task_states(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_task_states_status ON agent_task_states(status);
CREATE INDEX IF NOT EXISTS idx_agent_task_states_task_id ON agent_task_states(task_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_agent_task_states_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER agent_task_states_updated_at
    BEFORE UPDATE ON agent_task_states
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_task_states_updated_at();

-- ============================================
-- Table 2: user_memories (Mem0-Style Long-Term Memory)
-- ============================================
-- Purpose: Store semantic memories extracted from conversations

CREATE TABLE IF NOT EXISTS user_memories (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    
    -- Memory content
    memory_text TEXT NOT NULL,  -- "User prefers ML papers from 2020+"
    embedding vector(768),  -- Nomic embedding for similarity search
    
    -- Classification
    memory_type VARCHAR(50) DEFAULT 'semantic' CHECK (memory_type IN ('semantic', 'episodic', 'preference', 'project')),
    category VARCHAR(100),  -- 'research_focus', 'paper_preference', etc.
    
    -- Importance & decay
    importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    
    -- Source tracking
    source_conversation_id UUID REFERENCES agent_conversations(id) ON DELETE SET NULL,
    source_message TEXT,  -- Original message that generated this memory
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_memories_user ON user_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memories_type ON user_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_user_memories_importance ON user_memories(importance_score DESC);

-- Vector index for similarity search (using IVFFlat for performance)
CREATE INDEX IF NOT EXISTS idx_user_memories_embedding ON user_memories 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_user_memories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_memories_updated_at
    BEFORE UPDATE ON user_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_user_memories_updated_at();

-- ============================================
-- Table 3: methodology_data_history (Rollback Support)
-- ============================================
-- Purpose: Track changes for undo/rollback functionality

CREATE TABLE IF NOT EXISTS data_change_history (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    
    -- What changed
    table_name VARCHAR(100) NOT NULL,  -- 'methodology_data', 'findings', etc.
    record_id UUID NOT NULL,  -- ID of the changed record
    
    -- Change details
    operation VARCHAR(20) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,  -- Previous values (NULL for INSERT)
    new_data JSONB,  -- New values (NULL for DELETE)
    
    -- Source
    changed_by VARCHAR(50) DEFAULT 'agent',  -- 'agent', 'user', 'system'
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE SET NULL,
    
    -- Timestamp
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_data_change_history_user ON data_change_history(user_id);
CREATE INDEX IF NOT EXISTS idx_data_change_history_table ON data_change_history(table_name);
CREATE INDEX IF NOT EXISTS idx_data_change_history_record ON data_change_history(record_id);
CREATE INDEX IF NOT EXISTS idx_data_change_history_date ON data_change_history(changed_at DESC);

-- ============================================
-- Add missing indexes to paper_sections for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_paper_sections_user_paper ON paper_sections(user_id, paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_sections_embedding ON paper_sections 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
