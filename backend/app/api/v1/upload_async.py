"""
Async Paper Upload API
Endpoints for uploading papers with background processing
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.api.v1.users import get_current_user_id
from app.workers.tasks import ingest_paper_task

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent.parent / "uploads" / "pdfs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload/async")
async def upload_paper_async(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    project_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a PDF for async background processing.
    Returns immediately with paper_id and task_id.
    
    Args:
        file: PDF file to upload
        title: Optional title (defaults to filename)
        project_id: Optional project to add paper to
    
    Returns:
        paper_id: ID of created paper record
        task_id: Celery task ID for tracking progress
        status: "queued"
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # Create paper record
    paper_title = title or file.filename.replace(".pdf", "").replace("_", " ").title()
    
    try:
        result = db.execute(
            text("""
                INSERT INTO papers (title, source, is_manual, user_id, local_file_path, pdf_url, is_processed, processing_status)
                VALUES (:title, 'async_upload', TRUE, :user_id, :file_path, :file_path, FALSE, 'pending')
                RETURNING id
            """),
            {
                "title": paper_title,
                "user_id": user_id,
                "file_path": str(file_path)
            }
        )
        db.commit()
        paper_id = result.fetchone()[0]
    except Exception as e:
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to create paper record: {e}")
    
    # Queue RAG ingestion task (embeddings for vector search)
    task = ingest_paper_task.delay(
        paper_id=paper_id,
        pdf_path=str(file_path),
        user_id=user_id,
        title=paper_title,
        project_id=project_id
    )
    
    # Also trigger content extraction (sections/tables/equations) in background
    import asyncio
    from app.core.pdf_extractor import process_and_store_pdf
    
    async def extract_content():
        try:
            from app.core.database import SessionLocal
            bg_db = SessionLocal()
            try:
                await process_and_store_pdf(
                    db=bg_db,
                    paper_id=paper_id,
                    pdf_path=str(file_path),
                    user_id=user_id
                )
            finally:
                bg_db.close()
        except Exception as e:
            print(f"⚠️ Content extraction failed: {e}")
    
    # Fire-and-forget
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(extract_content())
    except RuntimeError:
        pass  # No event loop available, will be processed via /pdf/process API
    
    return {
        "paper_id": paper_id,
        "task_id": task.id,
        "status": "queued",
        "message": f"Paper '{paper_title}' queued for processing (RAG + content extraction)"
    }


@router.get("/upload/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background ingestion task.
    
    Returns:
        task_id: The task ID
        status: pending, started, success, failure
        result: Task result (if completed)
    """
    from app.workers.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": result.status.lower(),
    }
    
    if result.ready():
        response["result"] = result.result
    
    if result.failed():
        response["error"] = str(result.result)
    
    return response


@router.get("/papers/{paper_id}/processing-status")
async def get_paper_processing_status(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the processing status of a specific paper.
    
    Returns:
        paper_id: Paper ID
        status: pending, processing, completed, failed
        is_processed: Boolean
        chunk_count: Number of RAG chunks
    """
    result = db.execute(
        text("""
            SELECT id, title, is_processed, local_file_path
            FROM papers
            WHERE id = :paper_id
        """),
        {"paper_id": paper_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Try to get chunk count
    chunk_count = 0
    try:
        chunk_result = db.execute(
            text("""
                SELECT COUNT(*) FROM data_paper_chunks
                WHERE metadata_->>'paper_id' = :pid
            """),
            {"pid": str(paper_id)}
        ).fetchone()
        chunk_count = chunk_result[0] if chunk_result else 0
    except Exception:
        pass
    
    return {
        "paper_id": result.id,
        "title": result.title,
        "is_processed": result.is_processed,
        "has_file": bool(result.local_file_path),
        "chunk_count": chunk_count,
        "status": "completed" if result.is_processed else "pending"
    }


@router.get("/upload/queue-stats")
async def get_queue_stats():
    """
    Get Celery queue statistics.
    """
    from app.workers.celery_app import celery_app
    
    try:
        inspect = celery_app.control.inspect()
        
        # Get active and reserved tasks
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        
        total_active = sum(len(tasks) for tasks in active.values())
        total_reserved = sum(len(tasks) for tasks in reserved.values())
        
        return {
            "active_tasks": total_active,
            "queued_tasks": total_reserved,
            "workers": list(active.keys()) if active else []
        }
    except Exception as e:
        return {
            "error": str(e),
            "active_tasks": 0,
            "queued_tasks": 0,
            "workers": []
        }
