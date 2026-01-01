# Complete Implementation Plan

## AI Research Hub - Production-Ready Literature Review Platform

**Version**: 1.0  
**Last Updated**: January 2026  
**Estimated Duration**: 6 Weeks  

---

## Executive Summary

This plan transforms the AI Research Hub from a working prototype into a production-ready platform. The focus is on the **Literature Review MVP** with full AI Assistant integration.

### Current State
- ✅ Frontend: Search, Results, Workspace, 6 Literature Review tabs
- ✅ Backend: APIs for all tabs, AI Agent with ReAct loop
- ⚠️ RAG Engine: Working but slow (1-2 min/paper)
- ❌ Background Processing: None
- ❌ Production Infrastructure: Missing

### Target State
- ✅ Sub-second uploads with async processing
- ✅ AI can read AND write to all tabs
- ✅ Real-time processing status updates
- ✅ 99.9% uptime with monitoring
- ✅ 100+ concurrent users supported

---

## Phase 0: Validation (Days 1-2)

### Goal
Verify the entire flow works end-to-end before building infrastructure.

### Tasks

#### 0.1 Manual Paper Ingestion
```
[ ] Create simple_ingest.py script
[ ] Manually ingest 3 test papers
[ ] Verify papers appear in database
[ ] Verify chunks stored in data_paper_chunks
```

**Deliverable**: 3 papers indexed and searchable

#### 0.2 AI Flow Test
```
[ ] Open AI Assistant
[ ] Test: "Search for papers about transformers"
[ ] Test: "Compare methodologies of paper 1 and 2"
[ ] Verify response contains actual paper content
```

**Deliverable**: AI can search and compare indexed papers

#### 0.3 Tab Integration Test
```
[ ] Create test project with 3 papers
[ ] Test each tab loads correctly
[ ] Test AI "update_comparison" tool writes to Comparison tab
[ ] Refresh tab and verify data persisted
```

**Deliverable**: AI → Tab data flow confirmed

### Test Criteria
| Test | Pass Criteria |
|------|---------------|
| Paper search | Returns relevant chunks |
| Paper compare | Generates meaningful comparison |
| Tab update | Data visible after refresh |

---

## Phase 1: Background Processing (Days 3-7)

### Goal
Implement async paper ingestion so uploads don't block.

### 1.1 Infrastructure Setup

#### Install Dependencies
```bash
pip install celery[redis] flower watchdog
```

#### Create Celery Configuration
```
[ ] Create backend/app/workers/__init__.py
[ ] Create backend/app/workers/celery_app.py
[ ] Create backend/app/workers/tasks.py
```

**File: celery_app.py**
```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "research_hub",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,
    worker_concurrency=4,
)
```

### 1.2 Background Task Definition

**File: tasks.py**
```python
@celery_app.task(bind=True, max_retries=3)
def ingest_paper_task(self, paper_id: int, pdf_path: str):
    """Background paper ingestion"""
    try:
        # Update status
        update_paper_status(paper_id, "processing")
        
        # Run Docling + embeddings
        stats = rag_engine.ingest_paper_with_docling(paper_id, pdf_path)
        
        # Update status
        update_paper_status(paper_id, "completed", chunk_count=stats["chunks"])
        
    except Exception as e:
        update_paper_status(paper_id, "failed", error=str(e))
        raise self.retry(countdown=60)
```

### 1.3 Database Schema Update

**Migration: 023_processing_status.sql**
```sql
ALTER TABLE papers ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE papers ADD COLUMN chunk_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN error_message TEXT;
ALTER TABLE papers ADD COLUMN local_file_path TEXT;

CREATE INDEX idx_papers_processing_status ON papers(processing_status);
```

### 1.4 Update Upload Endpoint

```python
@router.post("/upload")
async def upload_paper(file: UploadFile):
    # Save file (instant)
    path = save_file(file)
    
    # Create DB record (instant)
    paper = create_paper(title=file.filename, status="pending")
    
    # Queue background task (instant)
    ingest_paper_task.delay(paper.id, path)
    
    # Return immediately
    return {"paper_id": paper.id, "status": "processing"}
```

### 1.5 Docker Configuration

**Update docker-compose.yml**
```yaml
services:
  celery_worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker -l info -c 4
    depends_on:
      - redis
      - postgres
    volumes:
      - ./backend/uploads:/app/uploads

  celery_flower:
    build: ./backend
    command: celery -A app.workers.celery_app flower --port=5555
    ports:
      - "5555:5555"
```

### Test Criteria
| Test | Pass Criteria |
|------|---------------|
| Upload response | < 1 second |
| Background processing | Task appears in queue |
| Status update | WebSocket notification received |
| Error handling | Failed papers marked as failed |

---

## Phase 2: AI-Tab Integration (Days 8-14)

### Goal
AI Assistant can read AND write to all Literature Review tabs.

### 2.1 Fix Missing AI Tools

#### Tool: update_methodology
```python
async def update_methodology(
    project_id: int,
    paper_id: int,
    methodology_description: str,
    methodology_context: str,
    approach_novelty: str,
    db = None
):
    """Update methodology tab for a paper"""
    # Calls PATCH /projects/{id}/methodology/{paper_id}
```

#### Tool: add_research_gap
```python
async def add_research_gap(
    project_id: int,
    description: str,
    priority: str,  # high, medium, low
    notes: str = None,
    db = None
):
    """Add a new research gap to Findings tab"""
    # Calls POST /projects/{id}/gaps
```

#### Tool: summarize_paper
```python
async def summarize_paper(
    paper_id: int,
    length: str = "medium",  # short, medium, long
    rag_engine = None,
    llm_client = None
):
    """Generate AI summary for a paper"""
    chunks = await rag_engine.retrieve_only(paper_id=paper_id)
    summary = await llm_client.summarize(chunks, length)
    return summary
```

### 2.2 Update Orchestrator

```python
# orchestrator.py - Add new tools
def _create_tools(self):
    return [
        # ... existing tools ...
        Tool(
            name="update_methodology",
            description="Update methodology data for a paper in the Methodology tab",
            function=self._wrap_db_tool(update_methodology)
        ),
        Tool(
            name="add_research_gap",
            description="Add a research gap to the Findings tab",
            function=self._wrap_db_tool(add_research_gap)
        ),
        Tool(
            name="summarize_paper",
            description="Generate a summary for a paper",
            function=self._wrap_rag_tool(summarize_paper)
        ),
    ]
```

### 2.3 Add Auto-Fill Buttons

**Frontend: Each tab gets an "Auto-fill with AI" button**

```tsx
// ComparisonView.tsx
<Button onClick={handleAutoFill}>
  <Sparkles /> Auto-fill with AI
</Button>

const handleAutoFill = async () => {
  await sendToAI({
    message: `Auto-extract comparison data for papers ${paperIds.join(", ")}`,
    project_id: projectId
  });
  refetchData(); // Reload tab data
};
```

### 2.4 WebSocket Tab Refresh

```tsx
// When AI updates a tab, send refresh notification
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "tab_updated") {
    // Refresh the specific tab
    refetchTabData(data.tab_name);
  }
};
```

### Test Criteria
| Test | Pass Criteria |
|------|---------------|
| Update methodology | Data visible in tab after AI call |
| Add research gap | Gap appears in Findings list |
| Auto-fill button | Tab populated with AI content |
| WebSocket refresh | Tab updates without manual refresh |

---

## Phase 3: Testing Infrastructure (Days 15-21)

### Goal
Comprehensive test suite for reliability.

### 3.1 Unit Tests

```
backend/tests/
├── unit/
│   ├── test_rag_engine.py
│   ├── test_celery_tasks.py
│   ├── test_api_papers.py
│   ├── test_api_synthesis.py
│   └── test_agent_tools.py
```

**Example: test_rag_engine.py**
```python
import pytest
from app.core.rag_engine import RAGEngine

@pytest.fixture
async def rag_engine():
    return RAGEngine()

@pytest.mark.asyncio
async def test_query_returns_results(rag_engine):
    results = await rag_engine.query("transformer attention mechanism")
    assert len(results["source_nodes"]) > 0

@pytest.mark.asyncio
async def test_hybrid_retriever_combines_results(rag_engine):
    results = await rag_engine.query("BERT NLP", top_k=10)
    # Should have both semantic and keyword matches
    assert results["retriever_type"] == "hybrid"
```

### 3.2 Integration Tests

```
backend/tests/
├── integration/
│   ├── test_upload_flow.py
│   ├── test_ai_tab_update.py
│   ├── test_project_workflow.py
│   └── test_websocket_chat.py
```

**Example: test_upload_flow.py**
```python
@pytest.mark.asyncio
async def test_full_upload_to_search_flow():
    # 1. Upload PDF
    response = await client.post("/papers/upload", files={"file": pdf_file})
    paper_id = response.json()["paper_id"]
    
    # 2. Wait for processing
    await wait_for_status(paper_id, "completed", timeout=120)
    
    # 3. Search for content
    search_result = await client.post("/agent/chat", json={
        "message": f"Search paper {paper_id} for methodology"
    })
    
    # 4. Verify content found
    assert "methodology" in search_result.json()["content"].lower()
```

### 3.3 End-to-End Tests (Playwright)

```
frontend/tests/e2e/
├── search.spec.ts
├── library.spec.ts
├── literature-review.spec.ts
└── ai-assistant.spec.ts
```

**Example: literature-review.spec.ts**
```typescript
test('create project and compare papers', async ({ page }) => {
  // Navigate to Literature Review
  await page.goto('/workspace');
  await page.click('[data-testid="lit-review-tab"]');
  
  // Create project
  await page.click('text=New Project');
  await page.fill('input[name="title"]', 'Test Project');
  await page.click('text=Create');
  
  // Add papers
  await page.click('text=Add Papers');
  await page.click('[data-testid="paper-checkbox-1"]');
  await page.click('[data-testid="paper-checkbox-2"]');
  await page.click('text=Add Selected');
  
  // Go to Comparison tab
  await page.click('text=Comparison');
  
  // Auto-fill with AI
  await page.click('text=Auto-fill with AI');
  await page.waitForSelector('[data-testid="comparison-table"]');
  
  // Verify data
  const cells = await page.$$('[data-testid="comparison-cell"]');
  expect(cells.length).toBeGreaterThan(0);
});
```

### 3.4 Load Testing (Locust)

```python
# backend/tests/load/locustfile.py
from locust import HttpUser, task, between

class ResearchHubUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def search_papers(self):
        self.client.get("/api/v1/papers/search?q=machine+learning")
    
    @task(2)
    def ai_chat(self):
        self.client.post("/api/v1/agent/chat", json={
            "message": "Compare methodologies",
            "user_id": self.user_id
        })
    
    @task(1)
    def upload_paper(self):
        self.client.post("/api/v1/papers/upload", 
            files={"file": open("test.pdf", "rb")})
```

### Test Execution

```bash
# Unit tests
pytest backend/tests/unit/ -v

# Integration tests
pytest backend/tests/integration/ -v --asyncio-mode=auto

# E2E tests
npx playwright test

# Load tests (100 users, 5 min)
locust -f backend/tests/load/locustfile.py --users 100 --spawn-rate 10 -t 5m
```

### Test Criteria
| Test Type | Coverage Target | Pass Criteria |
|-----------|-----------------|---------------|
| Unit | 80%+ | All pass |
| Integration | Critical paths | All pass |
| E2E | User journeys | All pass |
| Load | 100 users | p95 < 3s, error < 1% |

---

## Phase 4: Monitoring & Observability (Days 22-28)

### Goal
Full visibility into system health and performance.

### 4.1 Prometheus Metrics

**File: backend/app/core/metrics.py**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Counters
papers_uploaded = Counter('papers_uploaded_total', 'Papers uploaded', ['status'])
rag_queries = Counter('rag_queries_total', 'RAG queries', ['scope'])
ai_tool_calls = Counter('ai_tool_calls_total', 'AI tool invocations', ['tool'])

# Histograms
rag_query_duration = Histogram('rag_query_duration_seconds', 'RAG query time')
ingestion_duration = Histogram('ingestion_duration_seconds', 'Paper ingestion time')
api_request_duration = Histogram('api_request_duration_seconds', 'API request time', ['endpoint'])

# Gauges
active_websockets = Gauge('active_websockets', 'Active WebSocket connections')
pending_ingestions = Gauge('pending_ingestions', 'Papers waiting for ingestion')
celery_queue_length = Gauge('celery_queue_length', 'Celery task queue length')
```

### 4.2 Prometheus Endpoint

```python
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 4.3 Grafana Dashboards

**Dashboard 1: System Overview**
- Request rate (req/sec)
- Error rate (%)
- Response time (p50, p95, p99)
- Active users

**Dashboard 2: RAG Performance**
- Query latency histogram
- Queries by scope
- Cache hit rate
- Vector store size

**Dashboard 3: Celery Workers**
- Active workers
- Queue length
- Task success/failure rate
- Average task duration

### 4.4 Health Check Endpoints

```python
@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": get_uptime()
    }

@router.get("/health/ready")
async def readiness():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "celery": await check_celery(),
        "rag_engine": await check_rag()
    }
    
    healthy = all(v == "ok" for v in checks.values())
    return {
        "ready": healthy,
        "checks": checks
    }
```

### 4.5 Alerting Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: research_hub
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowQueries
        expr: histogram_quantile(0.95, rag_query_duration_seconds) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "RAG queries are slow"
          
      - alert: WorkerDown
        expr: celery_workers_active < 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Celery workers down"
```

### 4.6 Logging (Structured)

```python
import structlog

logger = structlog.get_logger()

async def process_query(query: str, user_id: str):
    logger.info("rag_query_started", 
        query=query, 
        user_id=user_id
    )
    
    result = await rag_engine.query(query)
    
    logger.info("rag_query_completed",
        query=query,
        user_id=user_id,
        result_count=len(result["source_nodes"]),
        duration_ms=elapsed
    )
```

### 4.7 Docker Compose Monitoring

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3001:3000"
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
```

### Monitoring Criteria
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Uptime | 99.9% | < 99% |
| API Latency (p95) | < 500ms | > 2s |
| RAG Latency (p95) | < 3s | > 10s |
| Error Rate | < 0.1% | > 1% |
| Queue Length | < 10 | > 50 |

---

## Phase 5: Security & Hardening (Days 29-35)

### Goal
Production-grade security and error handling.

### 5.1 Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)

@app.get("/api/v1/papers")
@limiter.limit("100/minute")
async def list_papers():
    pass

@app.post("/api/v1/agent/chat")
@limiter.limit("30/minute")
async def chat():
    pass
```

### 5.2 Input Validation

```python
from pydantic import BaseModel, validator, constr
import bleach

class ChatRequest(BaseModel):
    message: constr(min_length=1, max_length=10000)
    
    @validator('message')
    def sanitize(cls, v):
        # Remove HTML
        v = bleach.clean(v)
        # Prevent prompt injection
        forbidden = ["ignore previous", "system:"]
        if any(f in v.lower() for f in forbidden):
            raise ValueError("Invalid content")
        return v
```

### 5.3 Error Handling

```python
class AppError(Exception):
    def __init__(self, message: str, code: str, status: int = 500):
        self.message = message
        self.code = code
        self.status = status

@app.exception_handler(AppError)
async def handle_app_error(request, exc):
    logger.error("app_error", code=exc.code, message=exc.message)
    return JSONResponse(
        status_code=exc.status,
        content={"error": exc.code, "message": exc.message}
    )
```

### 5.4 CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

### Security Checklist
```
[ ] Rate limiting on all endpoints
[ ] Input validation on all inputs
[ ] CORS properly configured
[ ] Secrets in environment variables
[ ] SQL injection prevention (parameterized queries)
[ ] XSS prevention (sanitized output)
[ ] Error messages don't leak internals
```

---

## Phase 6: Deployment & Launch (Days 36-42)

### Goal
Production deployment with zero downtime.

### 6.1 Environment Configuration

**.env.production**
```
DATABASE_URL=postgresql://user:pass@prod-db:5432/research_db
REDIS_URL=redis://prod-redis:6379/0
GROQ_API_KEY=xxx
NOMIC_API_KEY=xxx
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 6.2 Docker Production Build

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### 6.3 Docker Compose Production

```yaml
version: '3.8'
services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    deploy:
      replicas: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      
  celery_worker:
    deploy:
      replicas: 4
      
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
```

### 6.4 Pre-Launch Checklist

```
[ ] All tests passing
[ ] Load test completed (100 users)
[ ] Monitoring dashboards ready
[ ] Alerting configured
[ ] Backup strategy in place
[ ] Rollback plan documented
[ ] SSL certificates configured
[ ] DNS configured
[ ] Health checks passing
[ ] Error tracking (Sentry) configured
```

### 6.5 Launch Sequence

```
1. [ ] Deploy to staging environment
2. [ ] Run full E2E test suite
3. [ ] Performance test on staging
4. [ ] Fix any issues found
5. [ ] Deploy to production
6. [ ] Smoke test core flows
7. [ ] Monitor metrics for 24 hours
8. [ ] Gradual traffic increase
9. [ ] Full launch
```

---

## Summary Timeline

| Week | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| 1 | 0-1 | Foundation | Celery, async upload working |
| 2 | 2 | AI Integration | All tools connected to tabs |
| 3 | 3 | Testing | 80% coverage, E2E passing |
| 4 | 4 | Monitoring | Dashboards, alerts configured |
| 5 | 5 | Security | Rate limiting, hardening |
| 6 | 6 | Deployment | Production launch |

---

## Success Metrics

| Metric | Current | Week 3 | Week 6 |
|--------|---------|--------|--------|
| Upload time | 60s+ | < 1s | < 1s |
| Search latency | - | < 3s | < 2s |
| Error rate | Unknown | < 5% | < 0.1% |
| Test coverage | 0% | 80% | 90% |
| Concurrent users | 1 | 50 | 100+ |
| Uptime | Manual | 95% | 99.9% |

---

## Next Step

**Recommended**: Start with Phase 0 (Validation) today to confirm the flow works, then begin Phase 1 (Background Processing) implementation.

Would you like me to start implementing Phase 0?
