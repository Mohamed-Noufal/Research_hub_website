-- Enable vector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Paper chunks with embeddings for LlamaIndex
CREATE TABLE IF NOT EXISTS paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section_type VARCHAR(50),  -- 'abstract', 'methodology', 'results', etc.
    text TEXT NOT NULL,
    embedding vector(384),  -- BAAI/bge-small-en-v1.5 dimension
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',  -- LlamaIndex metadata
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(paper_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_paper_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_chunks_section ON paper_chunks(section_type);
CREATE INDEX IF NOT EXISTS idx_paper_chunks_embedding ON paper_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Agent conversations
CREATE TABLE IF NOT EXISTS agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES user_literature_reviews(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_conversations_user ON agent_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_conversations_project ON agent_conversations(project_id);

-- Agent messages
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_created ON agent_messages(created_at);

-- Tool execution logs
CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    result JSONB,
    error TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_conversation ON agent_tool_calls(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_tool ON agent_tool_calls(tool_name);

-- LLM usage tracking
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE SET NULL,
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_logs_user ON llm_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_logs_date ON llm_usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_logs_cost ON llm_usage_logs(cost_usd);

-- RAG usage tracking
CREATE TABLE IF NOT EXISTS rag_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES local_users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER,
    avg_similarity DECIMAL(5, 4),
    embed_duration_ms INTEGER,
    search_duration_ms INTEGER,
    total_duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_logs_user ON rag_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_rag_logs_date ON rag_usage_logs(created_at);
