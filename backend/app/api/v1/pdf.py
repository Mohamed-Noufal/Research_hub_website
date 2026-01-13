"""
PDF Processing API - Trigger PDF extraction and store content
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pdf", tags=["pdf"])


class ProcessPDFRequest(BaseModel):
    paper_id: int
    pdf_path: Optional[str] = None  # If not provided, will look up from papers table
    user_id: Optional[str] = None


class ProcessPDFResponse(BaseModel):
    status: str
    message: str
    sections: int = 0
    tables: int = 0
    equations: int = 0


@router.post("/process", response_model=ProcessPDFResponse)
async def process_pdf(
    request: ProcessPDFRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process a PDF file and extract content (sections, tables, equations).
    
    This is triggered:
    - When user uploads a PDF
    - When user saves a paper with PDF URL
    - Manually via this API endpoint
    
    Processing happens in background. Check paper.processing_status for status.
    """
    from sqlalchemy import text
    
    # Get paper info
    result = db.execute(text("""
        SELECT id, title, pdf_url, processing_status
        FROM papers 
        WHERE id = :paper_id
    """), {'paper_id': request.paper_id})
    paper = result.fetchone()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.processing_status == 'completed':
        return ProcessPDFResponse(
            status="already_processed",
            message=f"Paper {request.paper_id} already processed"
        )
    
    if paper.processing_status == 'processing':
        return ProcessPDFResponse(
            status="processing",
            message=f"Paper {request.paper_id} is currently being processed"
        )
    
    # Determine PDF path
    pdf_path = request.pdf_path or paper.pdf_url
    
    if not pdf_path:
        raise HTTPException(
            status_code=400, 
            detail="No PDF path/URL available for this paper"
        )
    
    # Get user_id (default to test user if not provided)
    user_id = request.user_id or "550e8400-e29b-41d4-a716-446655440000"
    
    logger.info(f"📄 Queueing PDF processing for paper {request.paper_id}")
    
    # Process in background
    async def process_in_background():
        try:
            from app.core.pdf_extractor import process_and_store_pdf
            from app.core.database import SessionLocal
            
            # Create new session for background task
            bg_db = SessionLocal()
            try:
                # Get existing embedding model from AgentService
                from app.services.agent_service import AgentService
                service = AgentService.get_instance()
                embed_model = None
                
                # Try to get from active service
                if service._orchestrator and service._orchestrator.rag:
                    embed_model = service._orchestrator.rag.embed_model
                
                # FALLBACK: If service doesn't have it (e.g. first run), initialize strictly for background task
                if not embed_model:
                    logger.info("⚠️ Embedding model not found in AgentService, initializing for background task...")
                    try:
                        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                        embed_model = HuggingFaceEmbedding(
                            model_name="nomic-ai/nomic-embed-text-v1.5",
                            trust_remote_code=True
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to fallback-initialize embedding model: {e}")

                stats = await process_and_store_pdf(
                    db=bg_db,
                    paper_id=request.paper_id,
                    pdf_path=pdf_path,
                    user_id=user_id,
                    embed_model=embed_model
                )
                logger.info(f"✅ PDF sections extracted: {stats}")
                
                # ALSO queue RAG ingestion via Celery
                try:
                    from app.workers.tasks import ingest_paper_task
                    task = ingest_paper_task.delay(
                        paper_id=request.paper_id,
                        pdf_path=pdf_path,
                        user_id=user_id,
                        title=None  # Will be fetched from DB
                    )
                    logger.info(f"✅ RAG ingestion queued: task_id={task.id}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not queue RAG ingestion (Celery may not be running): {e}")
            finally:
                bg_db.close()
        except Exception as e:
            logger.error(f"❌ PDF processing failed: {e}")
    
    background_tasks.add_task(process_in_background)
    
    # Update status to pending
    db.execute(text("""
        UPDATE papers SET processing_status = 'pending' WHERE id = :paper_id
    """), {'paper_id': request.paper_id})
    db.commit()
    
    return ProcessPDFResponse(
        status="queued",
        message=f"PDF processing queued for paper {request.paper_id}"
    )


@router.get("/status/{paper_id}")
async def get_processing_status(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Get PDF processing status for a paper"""
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, title, processing_status, processing_started_at, processing_completed_at,
               section_count, table_count, equation_count, processing_error
        FROM papers 
        WHERE id = :paper_id
    """), {'paper_id': paper_id})
    paper = result.fetchone()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {
        "paper_id": paper.id,
        "title": paper.title,
        "status": paper.processing_status or "not_processed",
        "started_at": paper.processing_started_at,
        "completed_at": paper.processing_completed_at,
        "sections": paper.section_count or 0,
        "tables": paper.table_count or 0,
        "equations": paper.equation_count or 0,
        "error": paper.processing_error
    }


@router.post("/batch-process")
async def batch_process_pdfs(
    limit: int = 10,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Process multiple unprocessed PDFs in batch.
    Only processes papers that have ACTUAL local PDF files (local_file_path).
    """
    from sqlalchemy import text
    import os
    
    # Find papers with LOCAL PDFs that haven't been processed
    result = db.execute(text("""
        SELECT id, title, local_file_path
        FROM papers 
        WHERE local_file_path IS NOT NULL 
          AND local_file_path != ''
          AND (processing_status IS NULL OR processing_status = 'pending')
          AND is_processed = FALSE
        LIMIT :limit
    """), {'limit': limit})
    
    papers = result.fetchall()
    
    if not papers:
        return {
            "status": "no_papers",
            "message": "No unprocessed papers with local PDF files found"
        }
    
    queued = []
    skipped = []
    
    for paper in papers:
        # Verify file actually exists
        if not paper.local_file_path or not os.path.exists(paper.local_file_path):
            skipped.append({"id": paper.id, "title": paper.title, "reason": "File not found"})
            continue
        
        # Queue each paper for processing
        db.execute(text("""
            UPDATE papers SET processing_status = 'pending' WHERE id = :paper_id
        """), {'paper_id': paper.id})
        queued.append({
            "id": paper.id, 
            "title": paper.title,
            "pdf_path": paper.local_file_path
        })
    
    db.commit()
    
    # Actually process the queued papers in background
    if queued and background_tasks:
        for paper_info in queued:
            async def process_one(p_id, p_path):
                try:
                    from app.core.pdf_extractor import process_and_store_pdf
                    from app.core.database import SessionLocal
                    bg_db = SessionLocal()
                    try:
                        await process_and_store_pdf(
                            db=bg_db,
                            paper_id=p_id,
                            pdf_path=p_path,
                            user_id=None
                        )
                        logger.info(f"✅ Batch processed paper {p_id}")
                    finally:
                        bg_db.close()
                except Exception as e:
                    logger.error(f"❌ Batch process failed for paper {p_id}: {e}")
            
            background_tasks.add_task(process_one, paper_info["id"], paper_info["pdf_path"])
    
    return {
        "status": "queued",
        "queued_count": len(queued),
        "skipped_count": len(skipped),
        "papers": queued,
        "skipped": skipped,
        "message": f"Processing {len(queued)} papers with local PDFs. Skipped {len(skipped)}."
    }
