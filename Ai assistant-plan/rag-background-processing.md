# RAG Background Processing Implementation Plan

## Overview

This plan outlines how to implement **scalable, non-blocking paper ingestion** that can handle 100+ concurrent users without crashing the system.

## Problem Statement

Current architecture processes papers **synchronously**:
- Docling PDF parsing: ~30-60 seconds per paper
- Nomic embedding generation: ~10-20 seconds per paper
- Total blocking time: **1-2 minutes per paper**

With 100 users uploading simultaneously, the system will crash.

---

## Proposed Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│    Redis    │────▶│   Celery    │
│  (API Layer)│     │   (Queue)   │     │  (Workers)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       │ Immediate Response                    │ Background Processing
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│  Frontend   │                         │  RAG Engine │
│  (Status UI)│◀────WebSocket──────────│  (Docling)  │
└─────────────┘                         └─────────────┘
```

---

## Phase 1: Core Infrastructure

### 1.1 Install Dependencies

```bash
pip install celery[redis] flower
```

**Files to create:**
- `backend/app/workers/celery_app.py` - Celery configuration
- `backend/app/workers/tasks.py` - Background tasks
- `backend/app/workers/__init__.py` - Module init

### 1.2 Celery Configuration

```python
# backend/app/workers/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "research_hub",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min max per task
    worker_concurrency=4,  # 4 parallel workers
    worker_prefetch_multiplier=1,  # One task at a time per worker
)
```

### 1.3 Background Tasks Definition

```python
# backend/app/workers/tasks.py
from app.workers.celery_app import celery_app
from app.core.rag_engine import RAGEngine
from app.core.database import SessionLocal
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def ingest_paper_task(self, paper_id: int, pdf_path: str, metadata: dict):
    """
    Background task to ingest a paper into RAG engine.
    Called immediately after PDF upload.
    """
    try:
        # Update status to "processing"
        with SessionLocal() as db:
            db.execute(
                text("UPDATE papers SET processing_status = 'processing' WHERE id = :id"),
                {"id": paper_id}
            )
            db.commit()
        
        # Run RAG ingestion (the slow part)
        import asyncio
        rag = RAGEngine()
        stats = asyncio.run(rag.ingest_paper_with_docling(
            paper_id=paper_id,
            pdf_path=pdf_path,
            metadata=metadata
        ))
        
        # Update status to "completed"
        with SessionLocal() as db:
            db.execute(
                text("""
                    UPDATE papers 
                    SET processing_status = 'completed', 
                        is_processed = TRUE,
                        chunk_count = :chunks
                    WHERE id = :id
                """),
                {"id": paper_id, "chunks": stats.get("text_chunks", 0)}
            )
            db.commit()
        
        return {"status": "success", "paper_id": paper_id, "stats": stats}
        
    except Exception as e:
        logger.error(f"Ingestion failed for paper {paper_id}: {e}")
        
        # Update status to "failed"
        with SessionLocal() as db:
            db.execute(
                text("UPDATE papers SET processing_status = 'failed', error_message = :error WHERE id = :id"),
                {"id": paper_id, "error": str(e)[:500]}
            )
            db.commit()
        
        raise self.retry(exc=e, countdown=60)  # Retry in 60 seconds
```

---

## Phase 2: Database Schema Updates

### 2.1 Add Processing Status Column

```sql
-- backend/migrations/022_processing_status.sql
ALTER TABLE papers ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE papers ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS local_file_path TEXT;

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_papers_processing_status ON papers(processing_status);
```

**Status Values:**
- `pending` - Uploaded, waiting in queue
- `processing` - Currently being indexed
- `completed` - Successfully indexed
- `failed` - Error during processing

---

## Phase 3: API Integration

### 3.1 Update Upload Endpoint

```python
# backend/app/api/v1/papers.py (updated upload endpoint)
from app.workers.tasks import ingest_paper_task

@router.post("/upload")
async def upload_paper(
    file: UploadFile,
    project_id: int = None,
    user_id: str = None,
    db: Session = Depends(get_db)
):
    # 1. Save file
    file_path = f"uploads/pdfs/{uuid4()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # 2. Create paper record (INSTANT)
    paper = Paper(
        title=file.filename.replace(".pdf", ""),
        source="manual_upload",
        is_manual=True,
        local_file_path=file_path,
        processing_status="pending"
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    
    # 3. Queue background task (NON-BLOCKING)
    ingest_paper_task.delay(
        paper_id=paper.id,
        pdf_path=file_path,
        metadata={"paper_id": paper.id, "title": paper.title}
    )
    
    # 4. Return immediately
    return {
        "status": "uploaded",
        "paper_id": paper.id,
        "message": "Paper uploaded. Processing in background (~1-2 min)"
    }
```

### 3.2 Processing Status Endpoint

```python
@router.get("/processing-status/{paper_id}")
async def get_processing_status(
    paper_id: int,
    db: Session = Depends(get_db)
):
    result = db.execute(
        text("SELECT processing_status, chunk_count, error_message FROM papers WHERE id = :id"),
        {"id": paper_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(404, "Paper not found")
    
    return {
        "paper_id": paper_id,
        "status": result.processing_status,
        "chunks_indexed": result.chunk_count,
        "error": result.error_message
    }
```

---

## Phase 4: Frontend Integration

### 4.1 Processing Status UI Component

```tsx
// frontend/src/components/ProcessingStatus.tsx
const ProcessingStatus = ({ paperId }: { paperId: number }) => {
  const [status, setStatus] = useState("pending");
  
  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`/api/v1/papers/processing-status/${paperId}`);
      const data = await res.json();
      setStatus(data.status);
      
      if (data.status === "completed" || data.status === "failed") {
        clearInterval(interval);
      }
    }, 3000); // Poll every 3 seconds
    
    return () => clearInterval(interval);
  }, [paperId]);
  
  return (
    <div className="processing-status">
      {status === "pending" && <Spinner /> "Waiting in queue..."}
      {status === "processing" && <Spinner /> "Indexing paper..."}
      {status === "completed" && <CheckIcon /> "Ready for search!"}
      {status === "failed" && <ErrorIcon /> "Processing failed"}
    </div>
  );
};
```

---

## Phase 5: Docker & Deployment

### 5.1 Add Celery Worker to Docker Compose

```yaml
# docker-compose.yml (add this service)
celery_worker:
  build: ./backend
  command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
  environment:
    - REDIS_URL=redis://redis:6379/0
    - DATABASE_URL=postgresql://...
  depends_on:
    - redis
    - postgres
  volumes:
    - ./backend/uploads:/app/uploads
  restart: always

celery_flower:
  build: ./backend
  command: celery -A app.workers.celery_app flower --port=5555
  ports:
    - "5555:5555"
  depends_on:
    - celery_worker
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Install Celery and dependencies
- [ ] Create `celery_app.py` configuration
- [ ] Create `tasks.py` with `ingest_paper_task`

### Phase 2: Database Schema
- [ ] Create migration `022_processing_status.sql`
- [ ] Add `processing_status`, `chunk_count`, `error_message` columns
- [ ] Run migration

### Phase 3: API Integration
- [ ] Update paper upload endpoint to queue tasks
- [ ] Add `/processing-status/{paper_id}` endpoint
- [ ] Test with single paper upload

### Phase 4: Frontend
- [ ] Create `ProcessingStatus` component
- [ ] Show status after upload
- [ ] Poll for completion

### Phase 5: Deployment
- [ ] Add Celery worker to docker-compose
- [ ] Add Flower for monitoring
- [ ] Test concurrent uploads

---

## Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| Upload Response Time | 60+ seconds | < 1 second |
| Concurrent Uploads | 1 | 100+ |
| Processing Queue | None | ∞ (Redis backed) |
| Worker Scalability | None | Horizontal |

---

## Next Steps

1. **Immediate**: Create the Celery infrastructure files
2. **Short-term**: Add database migration and API changes
3. **Medium-term**: Frontend status UI
4. **Long-term**: Kubernetes scaling for workers

**Estimated Implementation Time**: 4-6 hours
