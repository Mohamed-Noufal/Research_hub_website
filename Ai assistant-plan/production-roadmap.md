# Production Readiness Roadmap

## AI Research Hub - Enterprise-Grade Implementation Plan

This document outlines the complete roadmap for transforming the AI Research Hub into a production-ready, enterprise-grade application with focus on **quality, performance, and long-term maintainability**.

---

## Executive Summary

| Category | Current State | Production Target |
|----------|--------------|-------------------|
| **Scalability** | Single-threaded, blocking | 100+ concurrent users |
| **Paper Ingestion** | 1-2 min/paper (blocking) | < 1s upload, async processing |
| **Response Time** | Variable (30s+ for RAG) | < 3s for most queries |
| **Error Rate** | No tracking | < 0.1% |
| **Uptime** | Manual restart | 99.9% SLA |
| **Security** | Basic auth | Enterprise security |

---

## Phase 1: Core Infrastructure (Week 1-2)

### 1.1 Background Processing with Celery

**Priority: CRITICAL**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │
│  (API)      │     │  (Broker)   │     │  (Workers)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       ▼                                       ▼
   Immediate                              Background
   Response                               Processing
```

**Files to Create:**
- [ ] `backend/app/workers/celery_app.py` - Celery configuration
- [ ] `backend/app/workers/tasks.py` - Background tasks
- [ ] `backend/app/workers/__init__.py` - Module init

**Tasks to Queue:**
1. Paper PDF ingestion (Docling parsing + embeddings)
2. Batch embedding generation
3. Email notifications
4. Cache invalidation
5. Analytics aggregation

**Docker Services:**
```yaml
celery_worker:
  command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
  
celery_beat:
  command: celery -A app.workers.celery_app beat --loglevel=info
  
flower:
  command: celery -A app.workers.celery_app flower --port=5555
```

---

### 1.2 Database Schema Enhancements

**Priority: HIGH**

| Table | New Columns | Purpose |
|-------|-------------|---------|
| `papers` | `processing_status` | Track ingestion state |
| `papers` | `chunk_count` | Verify successful indexing |
| `papers` | `error_message` | Debug failed ingestions |
| `papers` | `local_file_path` | Link to physical file |
| `papers` | `file_hash` | Detect duplicate uploads |

**Migration Script:**
```sql
-- 023_production_schema.sql
ALTER TABLE papers ADD COLUMN processing_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE papers ADD COLUMN chunk_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN error_message TEXT;
ALTER TABLE papers ADD COLUMN local_file_path TEXT;
ALTER TABLE papers ADD COLUMN file_hash VARCHAR(64);

CREATE INDEX idx_papers_processing_status ON papers(processing_status);
CREATE INDEX idx_papers_file_hash ON papers(file_hash);

-- Add soft delete
ALTER TABLE papers ADD COLUMN deleted_at TIMESTAMP;
CREATE INDEX idx_papers_deleted_at ON papers(deleted_at) WHERE deleted_at IS NULL;
```

---

### 1.3 Caching Strategy (Redis)

**Priority: HIGH**

**Cache Layers:**

| Layer | TTL | Use Case |
|-------|-----|----------|
| **Query Cache** | 5 min | RAG query results |
| **Embedding Cache** | 1 hour | Nomic embeddings |
| **Session Cache** | 24 hours | User sessions |
| **Rate Limit** | 1 min | API throttling |

**Implementation:**
```python
# backend/app/core/cache.py
from redis import Redis
from functools import wraps
import hashlib
import json

redis_client = Redis.from_url(settings.REDIS_URL)

def cached_query(ttl_seconds=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"query:{hashlib.md5(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()}"
            
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## Phase 2: Performance Optimization (Week 2-3)

### 2.1 RAG Engine Optimization

**Current Issues:**
- Docling parsing: ~30-60s per paper
- Nomic embedding: ~10-20s per paper
- No batching or parallelization

**Optimizations:**

| Optimization | Impact | Implementation |
|--------------|--------|----------------|
| **Batch Embeddings** | 3x faster | Process 10 chunks at once |
| **GPU Acceleration** | 5x faster | CUDA for Nomic |
| **Pre-chunking** | 2x faster | Cache chunk boundaries |
| **Parallel Ingestion** | 4x faster | Multiple Celery workers |

**Code Changes:**
```python
# backend/app/core/rag_engine.py
class RAGEngine:
    def __init__(self):
        self.embed_model = HuggingFaceEmbedding(
            model_name="nomic-ai/nomic-embed-text-v1.5",
            device="cuda" if torch.cuda.is_available() else "cpu",
            embed_batch_size=32  # Batch embeddings
        )
```

---

### 2.2 Database Connection Pooling

**Current:** New connection per request
**Target:** Connection pool with recycling

```python
# backend/app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 min
    pool_pre_ping=True  # Health check before use
)
```

---

### 2.3 Query Optimization

**Add Database Indexes:**
```sql
-- Composite indexes for common queries
CREATE INDEX idx_papers_user_source ON papers(user_id, source);
CREATE INDEX idx_papers_created_processed ON papers(created_at, is_processed);
CREATE INDEX idx_paper_chunks_paper_section ON paper_chunks(paper_id, section_type);

-- Full-text search index
CREATE INDEX idx_papers_title_trgm ON papers USING gin(title gin_trgm_ops);
```

---

## Phase 3: Reliability & Observability (Week 3-4)

### 3.1 Error Handling Framework

```python
# backend/app/core/exceptions.py
class BaseAppException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code

class RAGIngestionError(BaseAppException):
    def __init__(self, paper_id: int, reason: str):
        super().__init__(
            message=f"Failed to ingest paper {paper_id}: {reason}",
            code="RAG_INGESTION_FAILED",
            status_code=500
        )

class RateLimitExceeded(BaseAppException):
    def __init__(self, user_id: str):
        super().__init__(
            message="Rate limit exceeded. Please wait.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429
        )
```

**Global Exception Handler:**
```python
# backend/app/main.py
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    logger.error(f"AppException: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message}
    )
```

---

### 3.2 Monitoring & Observability

**Stack:**
- **OpenTelemetry** - Distributed tracing
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards
- **Sentry** - Error tracking

**Key Metrics:**
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Counters
rag_queries_total = Counter('rag_queries_total', 'Total RAG queries', ['status'])
papers_ingested_total = Counter('papers_ingested_total', 'Papers ingested', ['status'])

# Histograms
rag_query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration')
ingestion_duration = Histogram('ingestion_duration_seconds', 'Paper ingestion duration')

# Gauges
active_workers = Gauge('celery_active_workers', 'Active Celery workers')
pending_ingestions = Gauge('pending_ingestions', 'Papers waiting for ingestion')
```

**Dashboard Alerts:**
| Alert | Condition | Action |
|-------|-----------|--------|
| High Error Rate | errors/min > 10 | Page on-call |
| Slow Queries | p95 latency > 5s | Investigate |
| Queue Backlog | pending > 100 | Scale workers |
| Worker Down | workers < 2 | Auto-restart |

---

### 3.3 Health Checks

```python
# backend/app/api/v1/health.py
@router.get("/health")
async def health_check():
    checks = {}
    
    # Database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except:
        checks["database"] = "unhealthy"
    
    # Redis
    try:
        redis_client.ping()
        checks["redis"] = "healthy"
    except:
        checks["redis"] = "unhealthy"
    
    # Celery
    try:
        celery_app.control.ping(timeout=1)
        checks["celery"] = "healthy"
    except:
        checks["celery"] = "unhealthy"
    
    status = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

---

## Phase 4: Security Hardening (Week 4-5)

### 4.1 Authentication & Authorization

| Feature | Implementation |
|---------|----------------|
| **JWT Auth** | Access + Refresh tokens |
| **Token Rotation** | 15 min access, 7 day refresh |
| **RBAC** | Admin, Researcher, Viewer roles |
| **API Keys** | For programmatic access |

```python
# backend/app/core/security.py
from jose import jwt
from datetime import datetime, timedelta

def create_tokens(user_id: str, role: str):
    access_payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "type": "access"
    }
    refresh_payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
        "type": "refresh"
    }
    return {
        "access_token": jwt.encode(access_payload, SECRET_KEY),
        "refresh_token": jwt.encode(refresh_payload, SECRET_KEY)
    }
```

---

### 4.2 Rate Limiting

```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

# Apply limits
@app.get("/api/v1/papers")
@limiter.limit("100/minute")
async def list_papers():
    pass

@app.post("/api/v1/papers/upload")
@limiter.limit("10/minute")
async def upload_paper():
    pass

@app.post("/api/v1/agent/chat")
@limiter.limit("30/minute")
async def chat():
    pass
```

---

### 4.3 Input Validation & Sanitization

```python
# backend/app/core/validation.py
from pydantic import BaseModel, validator, constr
import bleach

class PaperUpload(BaseModel):
    title: constr(min_length=1, max_length=500)
    
    @validator('title')
    def sanitize_title(cls, v):
        return bleach.clean(v, tags=[], strip=True)

class ChatMessage(BaseModel):
    message: constr(min_length=1, max_length=10000)
    
    @validator('message')
    def no_injection(cls, v):
        # Prevent prompt injection
        forbidden = ["ignore previous", "system:", "```system"]
        if any(f in v.lower() for f in forbidden):
            raise ValueError("Invalid message content")
        return v
```

---

## Phase 5: Scalability (Week 5-6)

### 5.1 Horizontal Scaling

**Docker Compose (Development):**
```yaml
version: '3.8'
services:
  api:
    deploy:
      replicas: 3
    
  celery_worker:
    deploy:
      replicas: 4
```

**Kubernetes (Production):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

### 5.2 Storage Optimization

**File Storage:**
- Use **S3/MinIO** for PDF storage
- CDN for PDF serving
- Presigned URLs for direct uploads

**Vector Storage:**
- **pgvector** for PostgreSQL (current)
- Consider **Pinecone/Weaviate** for massive scale

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Install Celery + Redis dependencies
- [ ] Create Celery configuration
- [ ] Create background task definitions
- [ ] Update upload endpoint to queue tasks
- [ ] Add processing status UI
- [ ] Run database migration

### Phase 2: Performance
- [ ] Implement query caching
- [ ] Enable batch embeddings
- [ ] Configure connection pooling
- [ ] Add database indexes

### Phase 3: Reliability
- [ ] Create exception hierarchy
- [ ] Add global error handler
- [ ] Set up Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Integrate Sentry
- [ ] Add health check endpoints

### Phase 4: Security
- [ ] Implement JWT authentication
- [ ] Add refresh token rotation
- [ ] Configure rate limiting
- [ ] Add input validation
- [ ] Security audit

### Phase 5: Scalability
- [ ] Docker Compose scaling
- [ ] Kubernetes manifests
- [ ] S3 integration for files
- [ ] Load testing

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Uptime** | 99.9% | Prometheus/Grafana |
| **API Latency (p95)** | < 500ms | OpenTelemetry |
| **RAG Query (p95)** | < 3s | Custom metrics |
| **Error Rate** | < 0.1% | Sentry |
| **Concurrent Users** | 100+ | Load testing |
| **Paper Ingestion** | < 2 min queue | Celery monitoring |

---

## Next Steps

1. **Immediate**: Implement Celery background processing
2. **Week 1**: Complete database schema enhancements
3. **Week 2**: Add caching and monitoring
4. **Week 3**: Security hardening
5. **Week 4**: Performance testing and optimization
6. **Week 5**: Production deployment

---

## File Structure After Implementation

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── health.py          # Health checks
│   ├── core/
│   │   ├── cache.py               # Redis caching
│   │   ├── exceptions.py          # Error handling
│   │   ├── metrics.py             # Prometheus metrics
│   │   ├── security.py            # JWT/Auth
│   │   └── validation.py          # Input validation
│   ├── middleware/
│   │   ├── rate_limit.py          # Rate limiting
│   │   └── auth.py                # Authentication
│   └── workers/
│       ├── celery_app.py          # Celery config
│       └── tasks.py               # Background tasks
├── migrations/
│   └── 023_production_schema.sql
└── docker-compose.prod.yml
```
