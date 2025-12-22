# Phase 5: Testing & Quality Assurance

**Duration**: Week 7  
**Goal**: Comprehensive testing of all components, integration tests, and quality assurance

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 4 is complete**:

```bash
# 1. Verify API endpoints exist
.venv\Scripts\python.exe -c "from app.api.v1.agent import router; print(f'✓ API has {len(router.routes)} routes')"
# Expected: "✓ API has X routes"

# 2. Verify agent service exists
.venv\Scripts\python.exe -c "from app.services.agent_service import AgentService; print('✓ Agent service ready')"
# Expected: "✓ Agent service ready"

# 3. Test API server
# Start server: uvicorn app.main:app --reload
# Then: curl http://localhost:8000/api/v1/agent/conversations
# Expected: JSON response

# 4. Verify frontend components exist
# Check: frontend/src/components/ai/ChatPanel.tsx
# Check: frontend/src/hooks/useAgent.ts
```

**✅ You should have**:
- All API endpoints working
- Agent service implemented
- Frontend chat UI built
- WebSocket support added

**❌ If missing, complete Phase 4 first**

---

## ✅ Checklist

### Unit Tests
- [ ] Test RAG Engine (`test_rag_engine.py`)
- [ ] Test LLM Client (`test_llm_client.py`)
- [ ] Test Flexible Agent (`test_agent.py`)
- [ ] Test Database Tools (`test_database_tools.py`)
- [ ] Test RAG Tools (`test_rag_tools.py`)
- [ ] Test PDF Tools (`test_pdf_tools.py`)
- [ ] Test Orchestrator (`test_orchestrator.py`)
- [ ] Achieve 80%+ coverage

### Integration Tests
- [ ] Test full upload workflow
- [ ] Test query workflow
- [ ] Test section generation workflow
- [ ] Test comparison generation
- [ ] Test concurrent operations
- [ ] Test error scenarios
- [ ] Test WebSocket events

### Performance Tests
- [ ] Load test chat endpoint
- [ ] Test RAG query performance
- [ ] Test concurrent users
- [ ] Optimize slow queries
- [ ] Add caching where needed

### Manual Testing
- [ ] Upload PDF via chat
- [ ] Ask questions about papers
- [ ] Generate methodology section
- [ ] Compare papers
- [ ] Verify UI updates correctly
- [ ] Test on different browsers

---

## 📋 Step-by-Step Implementation

### 1. Unit Tests

Create `backend/tests/test_rag_engine.py`:

```python
"""
Unit tests for RAG Engine
Tests LlamaIndex integration, Nomic embeddings, and Docling parsing
"""
import pytest
import asyncio
from app.core.rag_engine import RAGEngine
import os

@pytest.fixture
def rag_engine():
    """Create RAG engine instance"""
    return RAGEngine()

@pytest.mark.asyncio
async def test_rag_initialization(rag_engine):
    """Test RAG engine initializes correctly"""
    assert rag_engine is not None
    assert rag_engine.embed_model is not None
    assert rag_engine.llm is not None
    assert rag_engine.index is not None
    print("✅ RAG engine initialized")

@pytest.mark.asyncio
async def test_docling_ingestion(rag_engine, tmp_path):
    """Test PDF ingestion with Docling"""
    # Create a test PDF (or use existing sample)
    pdf_path = "tests/fixtures/sample_paper.pdf"
    
    if os.path.exists(pdf_path):
        stats = await rag_engine.ingest_paper_with_docling(
            paper_id=999,
            pdf_path=pdf_path,
            metadata={"project_id": 1}
        )
        
        assert stats['total_elements'] > 0
        assert stats['text_chunks'] > 0
        print(f"✅ Ingested {stats['text_chunks']} chunks")
    else:
        pytest.skip("Sample PDF not found")

@pytest.mark.asyncio
async def test_semantic_query(rag_engine):
    """Test semantic search with Nomic embeddings"""
    result = await rag_engine.query(
        query_text="machine learning methodology",
        top_k=5,
        return_sources=True
    )
    
    assert 'answer' in result
    assert 'source_nodes' in result
    assert isinstance(result['source_nodes'], list)
    print(f"✅ Query returned {len(result['source_nodes'])} sources")

@pytest.mark.asyncio
async def test_retrieval_only(rag_engine):
    """Test retrieval without LLM generation"""
    chunks = await rag_engine.retrieve_only(
        query_text="deep learning",
        top_k=3
    )
    
    assert isinstance(chunks, list)
    if chunks:
        assert 'text' in chunks[0]
        assert 'score' in chunks[0]
        assert 'metadata' in chunks[0]
    print(f"✅ Retrieved {len(chunks)} chunks")

@pytest.mark.asyncio
async def test_project_filtering(rag_engine):
    """Test filtering by project_id"""
    result = await rag_engine.query(
        query_text="test query",
        project_id=1,
        top_k=5
    )
    
    # Verify all results are from project 1
    for node in result['source_nodes']:
        assert node['metadata'].get('project_id') == 1
    print("✅ Project filtering works")
```

Create `backend/tests/test_database_tools.py`:

```python
"""
Unit tests for Database Tools
Tests integration with YOUR existing tables
"""
import pytest
from app.tools import database_tools
from app.core.database import get_db
from sqlalchemy import text

@pytest.fixture
async def db():
    """Get database session"""
    db_gen = get_db()
    db = next(db_gen)
    yield db
    db.close()

@pytest.mark.asyncio
async def test_get_project_by_name(db):
    """Test fuzzy project name matching"""
    # Create test project
    await db.execute(
        text("""
            INSERT INTO projects (id, user_id, name, description)
            VALUES (9999, 'test_user', 'Test Research Project', 'Test description')
            ON CONFLICT (id) DO NOTHING
        """)
    )
    await db.commit()
    
    # Test exact match
    project = await database_tools.get_project_by_name(
        project_name="Test Research Project",
        user_id="test_user",
        db=db
    )
    assert project is not None
    assert project['name'] == "Test Research Project"
    
    # Test fuzzy match
    project = await database_tools.get_project_by_name(
        project_name="test research",
        user_id="test_user",
        db=db,
        fuzzy=True
    )
    assert project is not None
    print("✅ Fuzzy matching works")

@pytest.mark.asyncio
async def test_update_comparison(db):
    """Test updating YOUR comparison_configs table"""
    result = await database_tools.update_comparison(
        user_id="test_user",
        project_id=9999,
        similarities="Both use machine learning",
        differences="Different datasets",
        db=db
    )
    
    assert result is not None
    assert result['insights_similarities'] == "Both use machine learning"
    assert result['insights_differences'] == "Different datasets"
    print("✅ Comparison update works")

@pytest.mark.asyncio
async def test_update_findings(db):
    """Test updating YOUR findings table"""
    result = await database_tools.update_findings(
        user_id="test_user",
        project_id=9999,
        paper_id=1,
        key_finding="Significant improvement in accuracy",
        limitations="Small sample size",
        db=db
    )
    
    assert result is not None
    assert result['key_finding'] == "Significant improvement in accuracy"
    print("✅ Findings update works")

@pytest.mark.asyncio
async def test_update_methodology(db):
    """Test updating YOUR methodology_data table"""
    result = await database_tools.update_methodology(
        user_id="test_user",
        project_id=9999,
        paper_id=1,
        methodology_summary="Experimental study with control group",
        data_collection="Surveys and interviews",
        analysis_methods="Statistical analysis",
        sample_size="N=100",
        db=db
    )
    
    assert result is not None
    assert result['methodology_summary'] == "Experimental study with control group"
    print("✅ Methodology update works")
```

Create `backend/tests/test_orchestrator.py`:

```python
"""
Unit tests for Orchestrator Agent
Tests intent classification and tool delegation
"""
import pytest
from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.core.database import get_db

@pytest.fixture
async def orchestrator():
    """Create orchestrator instance"""
    db = next(get_db())
    llm = LLMClient(db)
    rag = RAGEngine()
    return OrchestratorAgent(llm, db, rag)

@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes with tools"""
    assert orchestrator is not None
    assert len(orchestrator.tools) > 0
    print(f"✅ Orchestrator has {len(orchestrator.tools)} tools")

@pytest.mark.asyncio
async def test_simple_query(orchestrator):
    """Test simple user query"""
    result = await orchestrator.process_user_message(
        user_id="test_user",
        message="Hello, what can you help me with?",
        project_id=1
    )
    
    assert result is not None
    assert 'status' in result or 'result' in result
    print("✅ Simple query works")

@pytest.mark.asyncio
async def test_tool_execution(orchestrator):
    """Test tool execution through orchestrator"""
    result = await orchestrator.process_user_message(
        user_id="test_user",
        message="Get papers in project 1",
        project_id=1
    )
    
    # Should use get_project_papers tool
    assert result is not None
    print("✅ Tool execution works")
```

---

### 2. Integration Tests

Create `backend/tests/test_integration.py`:

```python
"""
Integration tests for full workflows
Tests end-to-end functionality
"""
import pytest
import asyncio
from app.agents.orchestrator import OrchestratorAgent
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.core.database import get_db

@pytest.mark.asyncio
async def test_full_upload_workflow():
    """Test: Upload PDF → Parse → Ingest → Query"""
    db = next(get_db())
    llm = LLMClient(db)
    rag = RAGEngine()
    orchestrator = OrchestratorAgent(llm, db, rag)
    
    # Step 1: Upload PDF (simulated)
    pdf_path = "tests/fixtures/sample_paper.pdf"
    
    if not os.path.exists(pdf_path):
        pytest.skip("Sample PDF not found")
    
    # Step 2: Parse and ingest
    stats = await rag.ingest_paper_with_docling(
        paper_id=9999,
        pdf_path=pdf_path,
        metadata={"project_id": 1}
    )
    
    assert stats['text_chunks'] > 0
    
    # Step 3: Query the paper
    result = await rag.query(
        query_text="What is the main contribution?",
        project_id=1,
        top_k=5
    )
    
    assert result['answer']
    assert len(result['source_nodes']) > 0
    print("✅ Full upload workflow works")

@pytest.mark.asyncio
async def test_comparison_generation_workflow():
    """Test: Get papers → Compare → Update comparison_configs"""
    db = next(get_db())
    llm = LLMClient(db)
    rag = RAGEngine()
    orchestrator = OrchestratorAgent(llm, db, rag)
    
    # Step 1: Request comparison
    result = await orchestrator.process_user_message(
        user_id="test_user",
        message="Compare papers 1 and 2 on methodology",
        project_id=1
    )
    
    # Step 2: Verify comparison was generated and saved
    # (Check comparison_configs table)
    from sqlalchemy import text
    check = await db.execute(
        text("""
            SELECT * FROM comparison_configs
            WHERE user_id = 'test_user' AND project_id = 1
        """)
    )
    
    row = check.fetchone()
    assert row is not None
    print("✅ Comparison generation workflow works")

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test multiple users chatting simultaneously"""
    db = next(get_db())
    llm = LLMClient(db)
    rag = RAGEngine()
    
    # Create multiple orchestrators (simulating different users)
    orchestrators = [
        OrchestratorAgent(llm, db, rag)
        for _ in range(3)
    ]
    
    # Send messages concurrently
    tasks = [
        orch.process_user_message(
            user_id=f"user_{i}",
            message="Hello",
            project_id=1
        )
        for i, orch in enumerate(orchestrators)
    ]
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(r is not None for r in results)
    print("✅ Concurrent operations work")
```

---

### 3. Performance Tests

Create `backend/tests/test_performance.py`:

```python
"""
Performance tests
Tests response times and load handling
"""
import pytest
import asyncio
import time
from app.core.rag_engine import RAGEngine
from app.core.llm_client import LLMClient

@pytest.mark.asyncio
async def test_rag_query_performance():
    """Test RAG query completes within 2 seconds"""
    rag = RAGEngine()
    
    start = time.time()
    result = await rag.query(
        query_text="machine learning",
        top_k=10
    )
    duration = time.time() - start
    
    assert duration < 2.0, f"Query took {duration:.2f}s (should be < 2s)"
    print(f"✅ RAG query: {duration:.2f}s")

@pytest.mark.asyncio
async def test_llm_response_time():
    """Test LLM response completes within 5 seconds"""
    llm = LLMClient()
    
    start = time.time()
    response = await llm.complete(
        prompt="Say hello",
        model="llama-3.1-8b-instant"
    )
    duration = time.time() - start
    
    assert duration < 5.0, f"LLM took {duration:.2f}s (should be < 5s)"
    print(f"✅ LLM response: {duration:.2f}s")

@pytest.mark.asyncio
async def test_concurrent_users_load():
    """Test system handles 10 concurrent users"""
    rag = RAGEngine()
    
    async def simulate_user():
        result = await rag.query(
            query_text="test query",
            top_k=5
        )
        return result
    
    start = time.time()
    tasks = [simulate_user() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    assert len(results) == 10
    assert duration < 10.0, f"10 users took {duration:.2f}s (should be < 10s)"
    print(f"✅ 10 concurrent users: {duration:.2f}s")
```

---

### 4. Test Configuration

Create `backend/pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests (skip by default)

# Coverage settings
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

Create `backend/tests/conftest.py`:

```python
"""
Pytest configuration and fixtures
"""
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Create test database connection"""
    db_url = os.getenv('TEST_DATABASE_URL') or os.getenv('DATABASE_URL')
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    
    # Create test tables if needed
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    yield SessionLocal()
    
    # Cleanup
    engine.dispose()

@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF for testing"""
    return "tests/fixtures/sample_paper.pdf"
```

---

### 5. Running Tests

Create `backend/run_tests.sh` (or `.bat` for Windows):

```bash
#!/bin/bash

echo "🧪 Running AI Assistant Tests"
echo "=============================="

# Unit tests
echo -e "\n1️⃣ Running unit tests..."
pytest tests/test_rag_engine.py tests/test_database_tools.py tests/test_orchestrator.py -v

# Integration tests
echo -e "\n2️⃣ Running integration tests..."
pytest tests/test_integration.py -v

# Performance tests
echo -e "\n3️⃣ Running performance tests..."
pytest tests/test_performance.py -v

# Coverage report
echo -e "\n4️⃣ Generating coverage report..."
pytest --cov=app --cov-report=html --cov-report=term-missing

echo -e "\n✅ All tests complete!"
echo "📊 Coverage report: htmlcov/index.html"
```

For Windows (`run_tests.bat`):

```batch
@echo off
echo Running AI Assistant Tests
echo ==========================

echo.
echo 1. Running unit tests...
.venv\Scripts\python.exe -m pytest tests\test_rag_engine.py tests\test_database_tools.py tests\test_orchestrator.py -v

echo.
echo 2. Running integration tests...
.venv\Scripts\python.exe -m pytest tests\test_integration.py -v

echo.
echo 3. Running performance tests...
.venv\Scripts\python.exe -m pytest tests\test_performance.py -v

echo.
echo 4. Generating coverage report...
.venv\Scripts\python.exe -m pytest --cov=app --cov-report=html --cov-report=term-missing

echo.
echo All tests complete!
echo Coverage report: htmlcov\index.html
```

---

## 🧪 Manual Testing Checklist

### Chat Interface Testing

1. **Upload PDF**:
   - [ ] Upload via chat: "Upload this PDF: [path]"
   - [ ] Verify parsing with Docling
   - [ ] Check equations/tables extracted
   - [ ] Verify chunks stored in database

2. **Query Papers**:
   - [ ] Ask: "What methodology did they use?"
   - [ ] Ask: "What are the main findings?"
   - [ ] Ask: "What are the limitations?"
   - [ ] Verify relevant chunks retrieved

3. **Generate Sections**:
   - [ ] Request: "Generate methodology section"
   - [ ] Verify content quality
   - [ ] Check methodology_data table updated
   - [ ] Verify UI auto-refreshes

4. **Compare Papers**:
   - [ ] Request: "Compare papers 1 and 2"
   - [ ] Verify similarities identified
   - [ ] Verify differences identified
   - [ ] Check comparison_configs table updated

5. **UI/UX**:
   - [ ] Chat panel opens/closes smoothly
   - [ ] Messages display correctly
   - [ ] Markdown rendering works
   - [ ] Code syntax highlighting works
   - [ ] Auto-scroll to bottom works
   - [ ] Loading indicators show
   - [ ] Error messages display

### Browser Testing

- [ ] Chrome
- [ ] Firefox
- [ ] Edge
- [ ] Safari (if available)

---

## 📝 Deliverables

- ✅ 80%+ test coverage
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Performance benchmarks met
- ✅ Manual testing complete
- ✅ Bug fixes implemented

---

## ⏭️ Next Phase

Proceed to **Phase 6: Deployment** to prepare for production.
