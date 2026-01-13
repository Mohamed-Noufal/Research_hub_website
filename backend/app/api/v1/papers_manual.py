"""
Manual Paper Creation Endpoints
- Create paper manually via form
- Support optional PDF upload
"""
import logging
import time
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List

from app.core.database import get_db
from app.api.v1.users import get_current_user_id
from app.services.enhanced_vector_service import EnhancedVectorService
from app.api.v1.papers_pdf import process_pdf_background

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])

@router.post("/manual")
async def create_manual_paper(
    title: str = Form(...),
    authors: str = Form(...),  # Comma-separated
    category: str = Form(..., description="Paper category: ai_cs, medicine_biology, agriculture_animal, humanities_social, economics_business"),
    abstract: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    doi: Optional[str] = Form(None),
    venue: Optional[str] = Form(None),
    folder_id: Optional[int] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Create a paper manually with optional PDF upload
    """
    
    # Parse authors
    authors_list = [a.strip() for a in authors.split(',') if a.strip()]
    
    if not authors_list:
        raise HTTPException(status_code=400, detail="At least one author is required")
    
    # Handle PDF upload if provided
    pdf_url = None
    file_path = None
    
    if pdf_file:
        # Validate PDF
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Create uploads directory
        upload_dir = Path("uploads/pdfs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = int(time.time())
        filename = f"manual_{timestamp}_{pdf_file.filename}"
        file_path = upload_dir / filename
        
        # Save file
        try:
            with file_path.open("wb") as f:
                content = await pdf_file.read()
                f.write(content)
            
            pdf_url = f"http://localhost:8000/uploads/pdfs/{filename}"
            logger.info(f"Saved manual PDF: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")
            raise HTTPException(status_code=500, detail="Failed to save PDF file")
    
    # Create paper in database
    try:
        from app.models.paper import Paper
        
        # Prepare authors list
        # Ensure it's stored as a list, even if entered as string in form
        
        new_paper = Paper(
            user_id=str(user_id), # Ensure string if model expects string
            title=title,
            abstract=abstract,
            authors=authors_list,
            publication_date=None, # Will parse below if needed
            doi=doi,
            venue=venue,
            pdf_url=pdf_url,
            local_file_path=str(file_path.absolute()) if file_path else None,
            source="Manual Entry",
            is_manual=True,
            citation_count=0,
            category=category,
            is_processed=False,
            processing_status='pending' if pdf_file else 'completed'
        )

        # Parse year if provided
        if year:
            from datetime import datetime
            try:
                new_paper.publication_date = datetime(year, 1, 1)
            except:
                pass

        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)
        
        paper_id = new_paper.id
        
        # Save the paper to user's library
        # (This part is still using raw SQL which is fine for simple join table, 
        # or we could use UserSavedPaper model if it exists)
        try:
            db.execute(
                text("INSERT INTO user_saved_papers (user_id, paper_id) VALUES (:user_id, :paper_id)"),
                {"user_id": user_id, "paper_id": paper_id}
            )
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to save paper to library: {e}")
        
        # Add to folder if specified
        if folder_id:
            try:
                # Check folder ownership
                folder_check = db.execute(
                    text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
                    {"id": folder_id, "user_id": user_id}
                ).fetchone()
                
                if folder_check:
                    db.execute(
                        text("INSERT INTO folder_papers (folder_id, paper_id) VALUES (:folder_id, :paper_id)"),
                        {"folder_id": folder_id, "paper_id": paper_id}
                    )
                    db.commit()
            except Exception as e:
                logger.warning(f"Failed to add to folder: {e}")

        # Trigger Auto-Indexing if PDF exists
        if pdf_url and file_path:
             background_tasks.add_task(
                process_pdf_background,
                pdf_path=str(file_path.absolute()),
                paper_id=paper_id
            )
        
        # Generate embedding for searchability (even if no PDF, we use title/abstract)
        vector_service = EnhancedVectorService()
        async def generate_embedding():
            await vector_service.generate_embeddings_for_papers(
                db=db,
                batch_size=1,
                max_papers=1,
                force_regenerate=False,
                paper_ids=[new_paper.id] # More specific!
            )
            
        background_tasks.add_task(generate_embedding)
        
        return {
            "id": paper_id,
            "title": title,
            "message": "Paper created successfully and will be searchable in ~30 seconds!"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create manual paper: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create paper: {str(e)}")
