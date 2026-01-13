"""
PDF Upload & Download Endpoints
- Upload PDF for existing paper
- Download PDF from URL
"""
import logging
import asyncio
import shutil
import httpx
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.paper import Paper
from app.core.pdf_extractor import process_and_store_pdf

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])

async def process_pdf_background(pdf_path: str, paper_id: int):
    """Background task to process PDF and extract content + RAG"""
    try:
        from app.core.database import SessionLocal
        bg_db = SessionLocal()
        try:
            # Get existing embedding model from AgentService
            from app.services.agent_service import AgentService
            service = AgentService.get_instance()
            embed_model = None
            if service._orchestrator and service._orchestrator.rag:
                embed_model = service._orchestrator.rag.embed_model
            
            # Check if we need to initialize it (fallback)
            if not embed_model:
                 # Try to initialize just for this task
                 try:
                    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                    embed_model = HuggingFaceEmbedding(
                        model_name="nomic-ai/nomic-embed-text-v1.5",
                        trust_remote_code=True
                    )
                 except:
                    pass

            # 1. Extract sections/tables/equations
            await process_and_store_pdf(
                db=bg_db,
                paper_id=paper_id,
                pdf_path=pdf_path,
                user_id=None,
                embed_model=embed_model
            )
            logger.info(f"✅ PDF sections extracted for paper {paper_id}")
            
            # 2. ALSO queue RAG ingestion via Celery
            try:
                from app.workers.tasks import ingest_paper_task
                task = ingest_paper_task.delay(
                    paper_id=paper_id,
                    pdf_path=pdf_path,
                    user_id=None,
                    title=None
                )
                logger.info(f"✅ RAG ingestion queued for paper {paper_id}: task_id={task.id}")
            except Exception as e:
                logger.warning(f"⚠️ Could not queue RAG ingestion for paper {paper_id} (Celery may not be running): {e}")
                
        finally:
            bg_db.close()
    except Exception as e:
        logger.error(f"❌ PDF processing failed for paper {paper_id}: {e}")

@router.post("/{paper_id}/upload-pdf")
async def upload_pdf(
    paper_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF file for a specific paper
    """
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create upload directory
    upload_dir = Path("uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{paper_id}.pdf"
    file_path = upload_dir / filename
    
    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save PDF file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Update paper PDF URL (relative)
    relative_url = f"http://localhost:8000/uploads/pdfs/{filename}"
    paper.pdf_url = relative_url
    paper.local_file_path = str(file_path)
    paper.processing_status = 'pending'
    
    db.commit()
    db.refresh(paper)
    
    # TRIGGER AUTO-INDEXING
    background_tasks.add_task(
        process_pdf_background, 
        pdf_path=str(file_path.absolute()), 
        paper_id=paper_id
    )
    
    return {
        "message": "PDF uploaded successfully",
        "pdf_url": relative_url,
        "paper_id": paper_id,
        "paper": {
            "id": paper.id,
            "title": paper.title,
            "pdf_url": paper.pdf_url
        }
    }

@router.post("/{paper_id}/download-pdf")
async def download_pdf(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Download PDF from external URL and save locally
    """
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if paper has external PDF URL
    if not paper.pdf_url:
        raise HTTPException(status_code=400, detail="Paper has no PDF URL")
    
    # Check if already local
    if paper.pdf_url.startswith("http://localhost") or paper.pdf_url.startswith("/uploads"):
        return {
            "message": "PDF already stored locally",
            "pdf_url": paper.pdf_url,
            "already_local": True
        }
    
    # Create upload directory
    upload_dir = Path("uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{paper_id}.pdf"
    file_path = upload_dir / filename
    
    try:
        # Download PDF with timeout
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            logger.info(f"Downloading PDF from {paper.pdf_url}")
            response = await client.get(paper.pdf_url)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"Unexpected content type: {content_type}")
            
            with file_path.open("wb") as f:
                f.write(response.content)
            
            logger.info(f"PDF downloaded successfully: {file_path}")
            
    except Exception as e:
        logger.error(f"Failed to download PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")
    
    # Update paper PDF URL to local
    relative_url = f"/uploads/pdfs/{filename}"
    full_url = f"http://localhost:8000/uploads/pdfs/{filename}"
    paper.pdf_url = relative_url
    paper.local_file_path = str(file_path)
    paper.processing_status = 'pending'
    
    db.commit()
    db.refresh(paper)
    
    # Auto-trigger processing
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(process_pdf_background(str(file_path), paper_id))
    except RuntimeError:
        pass
    
    return {
        "message": "PDF downloaded and saved successfully",
        "pdf_url": relative_url,
        "pdf_url_full": full_url,
        "paper_id": paper_id,
        "processing_queued": True
    }
