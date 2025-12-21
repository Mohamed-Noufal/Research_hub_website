# Phase 5: Testing & Quality Assurance

**Duration**: Week 7  
**Goal**: Comprehensive testing, quality metrics, and production readiness

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 4 is complete**:

```bash
# 1. Verify API endpoint exists
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
# Expected: Response from agent

# 2. Verify WebSocket endpoint
# (Use wscat or browser console)
# Expected: WebSocket connection successful

# 3. Verify frontend component exists
ls frontend/src/components/ai/ChatPanel.tsx
# Expected: File exists

# 4. Test full integration
# Open frontend, test chat with AI
# Expected: Chat works end-to-end
```

**✅ You should have**:
- API endpoints working
- WebSocket real-time updates
- Frontend chat component
- Full integration tested

**❌ If missing, complete Phase 4 first**

---

## ✅ Checklist

### Unit Tests
- [ ] Test LLM client
- [ ] Test vector store
- [ ] Test flexible agent
- [ ] Test all tools
- [ ] Achieve 80%+ coverage

### Integration Tests
- [ ] Test full chat workflow
- [ ] Test section generation
- [ ] Test database updates
- [ ] Test WebSocket events

### Quality Metrics
- [ ] RAG precision > 0.7
- [ ] Response time < 3s
- [ ] Zero critical bugs

---

## 📋 Testing Implementation

### 1. Unit Tests

Create `backend/tests/test_llm_client.py`:

```python
import pytest
from app.core.llm_client import LLMClient

@pytest.mark.asyncio
async def test_llm_complete():
    llm = LLMClient()
    response = await llm.complete("Say hello")
    assert len(response) > 0

@pytest.mark.asyncio
async def test_token_counting():
    llm = LLMClient()
    tokens = llm.count_tokens("Hello world")
    assert tokens > 0
```

Create `backend/tests/test_vector_store.py`:

```python
import pytest
from app.core.vector_store import VectorStore

@pytest.mark.asyncio
async def test_embedding_generation(db):
    vs = VectorStore(db)
    embedding = await vs.embed_text("test")
    assert len(embedding) == 768

@pytest.mark.asyncio
async def test_similarity_search(db):
    vs = VectorStore(db)
    results = await vs.similarity_search(
        query="methodology",
        user_id="test_user",
        filters={'section_types': ['methodology']}
    )
    assert isinstance(results, list)
```

### 2. Integration Tests

Create `backend/tests/integration/test_full_workflow.py`:

```python
import pytest
from app.agents.orchestrator import OrchestratorAgent

@pytest.mark.asyncio
async def test_generate_section_workflow(db, llm, vector_store):
    orchestrator = OrchestratorAgent(llm, db, vector_store)
    
    result = await orchestrator.process_user_message(
        user_id="test_user",
        message="Generate methodology for test project",
        project_id=1
    )
    
    assert result['status'] == 'success'
```

### 3. Run Tests

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html
```

---

## 📊 Quality Metrics

### RAG Quality

```python
# backend/tests/quality/test_rag_quality.py

def test_rag_precision():
    """Test if RAG returns relevant results"""
    results = await vector_store.similarity_search(
        query="methodology approach",
        section_filter=['methodology']
    )
    
    # All results should be from methodology section
    precision = sum(1 for r in results if r['section_type'] == 'methodology') / len(results)
    assert precision > 0.7
```

### Performance

```python
import time

def test_response_time():
    start = time.time()
    result = await orchestrator.process_user_message(...)
    duration = time.time() - start
    
    assert duration < 3.0  # Must respond in < 3 seconds
```

---

## 📝 Deliverables

- ✅ 80%+ test coverage
- ✅ All tests passing
- ✅ Quality metrics met
- ✅ Performance benchmarks met

---

## ⏭️ Next Phase

Proceed to **Phase 6: Deployment & Monitoring**.
