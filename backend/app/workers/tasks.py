"""
Celery Tasks for Background Processing
Paper ingestion, embedding updates, and other async operations
"""
import os
import logging
import hashlib
from pathlib import Path
from typing import Optional

from app.workers.celery_app import celery_app
from celery import Task

# Configure logging
logger = logging.getLogger(__name__)


class RAGTask(Task):
    """Base task class with RAG engine initialization"""
    _rag_engine = None
    _db_session = None
    
    @property
    def rag_engine(self):
        if self._rag_engine is None:
            from app.core.rag_engine import RAGEngine
            self._rag_engine = RAGEngine()
        return self._rag_engine
    
    @property
    def db(self):
        if self._db_session is None:
            from app.core.database import SessionLocal
            self._db_session = SessionLocal()
        return self._db_session
    
    def after_return(self, *args, **kwargs):
        """Clean up database session after task completes"""
        if self._db_session:
            self._db_session.close()
            self._db_session = None


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file for duplicate detection"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_paper_status(db, paper_id: int, status: str, **kwargs):
    """Update paper processing status in database"""
    from sqlalchemy import text
    
    update_fields = ["is_processed = :processed"]
    params = {"paper_id": paper_id, "processed": status == "completed"}
    
    # Try to set processing_status if column exists
    try:
        update_fields.append("processing_status = :status")
        params["status"] = status
    except Exception:
        pass
    
    if "chunk_count" in kwargs:
        try:
            update_fields.append("chunk_count = :chunks")
            params["chunks"] = kwargs["chunk_count"]
        except Exception:
            pass
    
    if "error_message" in kwargs:
        try:
            update_fields.append("error_message = :error")
            params["error"] = kwargs["error_message"]
        except Exception:
            pass
    
    if "file_hash" in kwargs:
        try:
            update_fields.append("file_hash = :hash")
            params["hash"] = kwargs["file_hash"]
        except Exception:
            pass
    
    query = f"UPDATE papers SET {', '.join(update_fields)} WHERE id = :paper_id"
    db.execute(text(query), params)
    db.commit()


@celery_app.task(bind=True, base=RAGTask, max_retries=3, default_retry_delay=60)
def ingest_paper_task(
    self,
    paper_id: int,
    pdf_path: str,
    user_id: str = None,
    title: str = None,
    project_id: int = None
) -> dict:
    """
    Background task to ingest a paper into the RAG system
    
    Args:
        paper_id: ID of the paper in the database
        pdf_path: Path to the PDF file
        user_id: User who owns the paper
        title: Paper title
        project_id: Optional project ID
    
    Returns:
        dict with ingestion stats
    """
    logger.info(f"[Task {self.request.id}] Starting ingestion for paper {paper_id}")
    
    try:
        # 1. Update status to processing
        update_paper_status(self.db, paper_id, "processing")
        
        # 2. Calculate file hash for duplicate detection
        file_hash = None
        if os.path.exists(pdf_path):
            file_hash = calculate_file_hash(pdf_path)
            logger.info(f"  File hash: {file_hash[:16]}...")
        
        # 3. Run RAG ingestion
        import asyncio
        stats = asyncio.run(
            self.rag_engine.ingest_paper_with_docling(
                paper_id=paper_id,
                pdf_path=pdf_path,
                user_id=user_id,
                title=title,
                project_id=project_id
            )
        )
        
        # 4. Update status to completed
        update_paper_status(
            self.db, 
            paper_id, 
            "completed",
            chunk_count=stats.get("text_chunks", 0),
            file_hash=file_hash
        )
        
        logger.info(f"[Task {self.request.id}] ✅ Paper {paper_id} ingested: {stats.get('text_chunks', 0)} chunks")
        
        return {
            "success": True,
            "paper_id": paper_id,
            "chunks": stats.get("text_chunks", 0),
            "file_hash": file_hash
        }
        
    except Exception as e:
        logger.error(f"[Task {self.request.id}] ❌ Failed to ingest paper {paper_id}: {e}")
        
        # Update status to failed
        update_paper_status(
            self.db, 
            paper_id, 
            "failed",
            error_message=str(e)
        )
        
        # Retry if not max retries
        if self.request.retries < self.max_retries:
            logger.info(f"  Retrying in {self.default_retry_delay}s...")
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "paper_id": paper_id,
            "error": str(e)
        }


@celery_app.task(bind=True, base=RAGTask)
def update_embeddings_task(self, paper_ids: list) -> dict:
    """
    Re-generate embeddings for existing papers
    Useful for batch updates or model changes
    """
    logger.info(f"[Task {self.request.id}] Updating embeddings for {len(paper_ids)} papers")
    
    results = {"success": [], "failed": []}
    
    for paper_id in paper_ids:
        try:
            # Get paper info from DB
            from sqlalchemy import text
            result = self.db.execute(
                text("SELECT title, local_file_path, user_id FROM papers WHERE id = :id"),
                {"id": paper_id}
            ).fetchone()
            
            if not result or not result.local_file_path:
                logger.warning(f"  Paper {paper_id}: No file path found")
                results["failed"].append(paper_id)
                continue
            
            # Re-ingest
            import asyncio
            stats = asyncio.run(
                self.rag_engine.ingest_paper_with_docling(
                    paper_id=paper_id,
                    pdf_path=result.local_file_path,
                    user_id=result.user_id,
                    title=result.title
                )
            )
            
            results["success"].append(paper_id)
            
        except Exception as e:
            logger.error(f"  Paper {paper_id}: {e}")
            results["failed"].append(paper_id)
    
    return results


@celery_app.task
def health_check() -> dict:
    """Simple health check task"""
    return {"status": "healthy", "task": "health_check"}
