# Phase 1: Foundation & Database Setup

**Duration**: Week 1-2  
**Goal**: Set up core infrastructure, database schema, and dependencies

---

## 🔍 Current Situation Check

**Before starting this phase, verify**:

```bash
# 1. Check PostgreSQL with pgvector is running
docker ps | grep postgres
# Expected: Container running with pgvector

# 2. Check database connection
psql -U postgres -d your_database -c "SELECT version();"
# Expected: PostgreSQL version displayed

# 3. Check pgvector extension
psql -U postgres -d your_database -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Expected: pgvector extension listed (if not, we'll install it)

# 4. Check Python version
python --version
# Expected: Python 3.11+

# 5. Check current database tables
psql -U postgres -d your_database -c "\dt"
# Expected: See existing tables (papers, user_literature_reviews, etc.)
```

**✅ You should have**:
- PostgreSQL running in Docker Desktop
- pgvector extension available
- Python 3.11+
- Existing database with papers, projects tables

**❌ If missing, fix before proceeding**

---

## ✅ Checklist

### Database Setup
- [ ] Verify pgvector extension is enabled
- [ ] Create migration file `020_agent_system.sql`
- [ ] Run migration on development database
- [ ] Verify all tables created successfully
- [ ] Create database indexes for performance

### Dependencies Installation
- [ ] Update `requirements.txt` with LlamaIndex & new packages
- [ ] Install Python dependencies
- [ ] Verify Groq API access
- [ ] Test LlamaIndex setup
- [ ] Setup Redis for caching (optional)

### Project Structure
- [ ] Create `backend/app/agents/` directory
- [ ] Create `backend/app/tools/` directory
- [ ] Create `backend/app/core/llm_client.py`
- [ ] Create `backend/app/core/rag_engine.py` (LlamaIndex)
- [ ] Create `backend/app/core/memory.py`

---

## 📋 Step-by-Step Instructions

### 1. Verify pgvector Extension

```bash
# Connect to your PostgreSQL in Docker
docker exec -it <postgres_container_name> psql -U postgres -d your_database

# Check if pgvector is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

# If not installed, install it
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
\dx vector
```

### 2. Create Migration File

Create `backend/migrations/020_agent_system.sql`:

```sql
-- Enable vector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Paper chunks with embeddings for LlamaIndex
CREATE TABLE paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section_type VARCHAR(50),  -- 'abstract', 'methodology', 'results', etc.
    text TEXT NOT NULL,
    embedding vector(768),  -- nomic-embed-text-v1.5 dimension
    token_count INTEGER,
    metadata JSONB DEFAULT '{}',  -- LlamaIndex metadata
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(paper_id, chunk_index)
);

CREATE INDEX idx_paper_chunks_paper ON paper_chunks(paper_id);
CREATE INDEX idx_paper_chunks_section ON paper_chunks(section_type);
CREATE INDEX idx_paper_chunks_embedding ON paper_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Agent conversations
CREATE TABLE agent_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES local_users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES user_literature_reviews(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_conversations_user ON agent_conversations(user_id);
CREATE INDEX idx_agent_conversations_project ON agent_conversations(project_id);

-- Agent messages
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_agent_messages_conversation ON agent_messages(conversation_id);
CREATE INDEX idx_agent_messages_created ON agent_messages(created_at);

-- Tool execution logs
CREATE TABLE agent_tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    result JSONB,
    error TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_conversation ON agent_tool_calls(conversation_id);
CREATE INDEX idx_tool_calls_tool ON agent_tool_calls(tool_name);

-- LLM usage tracking
CREATE TABLE llm_usage_logs (
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

CREATE INDEX idx_llm_logs_user ON llm_usage_logs(user_id);
CREATE INDEX idx_llm_logs_date ON llm_usage_logs(created_at);
CREATE INDEX idx_llm_logs_cost ON llm_usage_logs(cost_usd);

-- RAG usage tracking
CREATE TABLE rag_usage_logs (
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

CREATE INDEX idx_rag_logs_user ON rag_usage_logs(user_id);
CREATE INDEX idx_rag_logs_date ON rag_usage_logs(created_at);
```

### 3. Run Migration

```bash
cd backend

# Create Python script to run migration
cat > run_migration.py << 'EOF'
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

with open('migrations/020_agent_system.sql', 'r') as f:
    cur.execute(f.read())

conn.commit()
print('✓ Migration completed successfully')
EOF

python run_migration.py
```

### 4. Update requirements.txt

Add these dependencies:

```txt
# LlamaIndex (RAG Framework)
llama-index==0.9.48
llama-index-vector-stores-postgres==0.1.8
llama-index-embeddings-huggingface==0.1.4
llama-index-llms-groq==0.1.3

# AI & LLM
groq==0.4.0
tiktoken==0.5.2

# Vector Database
pgvector==0.2.3
psycopg2-binary==2.9.9

# PDF Processing
pypdf2==3.0.1

# Utilities
redis==5.0.1
websockets==12.0
tenacity==8.2.3
pydantic==2.5.0
python-dotenv==1.0.0
```

### 5. Install Dependencies

```bash
cd backend
pip install -r requirements.txt

# Test LlamaIndex installation
python -c "
from llama_index.core import VectorStoreIndex
print('✓ LlamaIndex installed successfully')
"
```

### 6. Setup Environment Variables

Add to `backend/.env`:

```env
# Database (your existing Docker PostgreSQL)
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_database

# Groq API
GROQ_API_KEY=your_groq_api_key_here

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300

# LlamaIndex
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 7. Create Directory Structure

```bash
cd backend/app

# Create directories
mkdir -p agents tools core

# Create __init__.py files
touch agents/__init__.py
touch tools/__init__.py
touch core/__init__.py
```

---

## 🧪 Verification

Create `backend/test_phase1.py`:

```python
import asyncio
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

async def test_database():
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    with engine.connect() as conn:
        # Test pgvector
        result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        assert result.fetchone() is not None, "❌ pgvector not installed"
        print("✓ pgvector installed")
        
        # Test tables
        tables = [
            'paper_chunks',
            'agent_conversations',
            'agent_messages',
            'agent_tool_calls',
            'llm_usage_logs',
            'rag_usage_logs'
        ]
        
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            print(f"✓ Table {table} exists")
        
        # Test LlamaIndex
        try:
            from llama_index.core import Settings
            print("✓ LlamaIndex imported successfully")
        except ImportError as e:
            print(f"❌ LlamaIndex import failed: {e}")
    
    print("\n✅ Phase 1 verification complete!")

if __name__ == "__main__":
    asyncio.run(test_database())
```

Run verification:
```bash
python backend/test_phase1.py
```

---

## 📝 Deliverables

- ✅ pgvector extension enabled in Docker PostgreSQL
- ✅ 6 new database tables created
- ✅ LlamaIndex and all dependencies installed
- ✅ Directory structure created
- ✅ Environment variables configured
- ✅ Verification tests passing

---

## ⏭️ Next Phase

Once all checks pass, proceed to **Phase 2: Core Components with LlamaIndex** to build the RAG engine and agent framework.
