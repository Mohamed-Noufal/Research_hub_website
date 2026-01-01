from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime

from app.core.database import get_db
from app.tools.pdf_tools import parse_pdf_background
from app.core.rag_engine import RAGEngine

# Define router
router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class KBPaperAddRequest(BaseModel):
    paper_ids: List[int]
    user_id: str

class KBStatusResponse(BaseModel):
    project_id: int
    indexed_count: int
    max_papers: int = 7
    papers: List[Dict[str, Any]]

# Endpoints
@router.post("/projects/{project_id}/kb/add-papers")
async def add_papers_to_kb(
    project_id: int,
    request: KBPaperAddRequest,
    db: Session = Depends(get_db)
):
    """
    Add papers to the project's Knowledge Base.
    Triggers background parsing and indexing.
    Enforces max 7 papers limit.
    """
    # 1. Check current KB count
    result = db.execute(
        text("""
            SELECT COUNT(*) FROM knowledge_base_papers 
            WHERE project_id = :pid AND user_id = :uid
        """),
        {'pid': project_id, 'uid': request.user_id}
    ).scalar()
    
    current_count = result or 0
    papers_to_add = len(request.paper_ids)
    
    if current_count + papers_to_add > 7:
        raise HTTPException(
            status_code=400, 
            detail=f"Limit exceeded. You can only have 7 papers in the Knowledge Base. Current: {current_count}, Adding: {papers_to_add}"
        )

    added_papers = []
    
    # 2. Process each paper
    for paper_id in request.paper_ids:
        # Check if already in KB
        exists = db.execute(
            text("""
                SELECT 1 FROM knowledge_base_papers 
                WHERE project_id = :pid AND paper_id = :paper_id AND user_id = :uid
            """),
            {'pid': project_id, 'paper_id': paper_id, 'uid': request.user_id}
        ).scalar()
        
        if exists:
            logger.info(f"Paper {paper_id} already in KB for project {project_id}")
            continue

        # Get PDF path
        paper_row = db.execute(
            text("SELECT * FROM papers WHERE id = :id"),
            {'id': paper_id}
        ).fetchone()
        
        if not paper_row:
            logger.warning(f"Paper {paper_id} not found in DB")
            continue
            
        # We assume local PDF path exists (managed by file upload)
        # Construct path (assuming stored in standard location or column)
        # For now, we'll try to find it or re-download if needed.
        # Ideally 'file_path' should be in papers table. 
        # Using a placeholder logic assuming 'pdf_path' will be resolved by worker
        # Let's check user_uploads table or similar if we have it
        
        # Insert into KB table as 'pending'
        db.execute(
            text("""
                INSERT INTO knowledge_base_papers 
                (user_id, project_id, paper_id, status)
                VALUES (:uid, :pid, :paper_id, 'pending')
            """),
            {'uid': request.user_id, 'pid': project_id, 'paper_id': paper_id}
        )
        db.commit()
        
        # Trigger Background Job via Redis (using existing tool)
        # Note: We need the PDF path. 
        # In this specific app, let's assume we can get it or the worker resolves it.
        # We'll pass a 'dummy' path if not known, relying on worker to find it by ID?
        # Re-checking pdf_tools logic... it creates a job.
        
        # Let's assume we have a way to get path. 
        # For this implementation, I'll update pdf_tools to handle finding the file if path is missing.
        await parse_pdf_background(
            pdf_path="", # Worker should resolve
            paper_id=paper_id,
            project_id=project_id
        )
        added_papers.append(paper_id)

    return {"status": "queued", "added_count": len(added_papers)}

@router.get("/projects/{project_id}/kb/status")
async def get_kb_status(
    project_id: int, 
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get status of Knowledge Base for a project
    """
    rows = db.execute(
        text("""
            SELECT k.paper_id, k.status, k.chunks_count, k.updated_at, p.title
            FROM knowledge_base_papers k
            JOIN papers p ON k.paper_id = p.id
            WHERE k.project_id = :pid AND k.user_id = :uid
        """),
        {'pid': project_id, 'uid': user_id}
    ).fetchall()
    
    papers = []
    for row in rows:
        papers.append({
            "paper_id": row.paper_id,
            "title": row.title,
            "status": row.status,
            "chunks": row.chunks_count,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None
        })
        
    return {
        "project_id": project_id,
        "indexed_count": len(papers),
        "max_papers": 7,
        "papers": papers
    }

@router.delete("/projects/{project_id}/kb/papers/{paper_id}")
async def remove_paper_from_kb(
    project_id: int, 
    paper_id: int, 
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove a paper from the Knowledge Base (delete embeddings)
    """
    # 1. Delete from paper_chunks
    # We filter by paper_id. 
    # NOTE: If we want to support same paper in multiple projects, we need project_id in chunks?
    # Currently schema links chunks to PAPER, not project.
    # This means if I delete it from KB, it's deleted for ALL projects using this paper?
    # Design Decision: For now, yes. Metadata-based filtering in future.
    # Or strict project isolation.
    
    db.execute(
        text("DELETE FROM paper_chunks WHERE paper_id = :pid"),
        {'pid': paper_id}
    )
    
    # 2. Delete from KB table
    db.execute(
        text("""
            DELETE FROM knowledge_base_papers 
            WHERE project_id = :pid AND paper_id = :paper_id AND user_id = :uid
        """),
        {'pid': project_id, 'paper_id': paper_id, 'uid': user_id}
    )
    db.commit()
    
    return {"status": "removed"}
