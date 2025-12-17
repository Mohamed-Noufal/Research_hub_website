"""
API endpoints for Methodology Explorer data management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()


# Request/Response Models
class MethodologyUpdate(BaseModel):
    methodology_description: Optional[str] = None
    methodology_context: Optional[str] = None
    approach_novelty: Optional[str] = None


class MethodologyData(BaseModel):
    paper_id: str
    title: str
    methodology: str
    methodology_type: str
    methodology_description: Optional[str]
    methodology_context: Optional[str]
    approach_novelty: Optional[str]


@router.get("/projects/{project_id}/methodology")
async def get_methodology_data(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get methodology data for all papers in a project"""
    
    # Query to get all papers with their methodology data
    query = """
        SELECT 
            p.id as paper_id,
            p.title,
            p.metadata->>'methodology' as methodology,
            p.metadata->>'methodology_type' as methodology_type,
            md.methodology_description,
            md.methodology_context,
            md.approach_novelty
        FROM papers p
        LEFT JOIN methodology_data md ON (
            md.paper_id = p.id
            AND md.user_id = :user_id 
            AND md.project_id = :project_id
        )
        WHERE p.id IN (
            SELECT paper_id 
            FROM project_papers 
            WHERE project_id = :project_id
        )
        ORDER BY p.publication_date DESC, p.title
    """
    
    result = db.execute(text(query), {"user_id": user_id, "project_id": project_id})
    papers = []
    
    for row in result:
        papers.append({
            "paper_id": str(row.paper_id),
            "title": row.title,
            "methodology": row.methodology or "",
            "methodology_type": row.methodology_type or "",
            "methodology_description": row.methodology_description or "",
            "methodology_context": row.methodology_context or "",
            "approach_novelty": row.approach_novelty or ""
        })
    
    return {"papers": papers}


@router.patch("/projects/{project_id}/methodology/{paper_id}")
async def update_methodology_data(
    project_id: int,
    paper_id: int,
    data: MethodologyUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update methodology data for a specific paper"""
    
    # Check if methodology data exists
    check_query = """
        SELECT id FROM methodology_data
        WHERE user_id = :user_id 
        AND project_id = :project_id 
        AND paper_id = :paper_id
    """
    
    existing = db.execute(
        text(check_query),
        {"user_id": user_id, "project_id": project_id, "paper_id": paper_id}
    ).fetchone()
    
    if existing:
        # Update existing record
        update_fields = []
        params = {"user_id": user_id, "project_id": project_id, "paper_id": paper_id}
        
        if data.methodology_description is not None:
            update_fields.append("methodology_description = :methodology_description")
            params["methodology_description"] = data.methodology_description
            
        if data.methodology_context is not None:
            update_fields.append("methodology_context = :methodology_context")
            params["methodology_context"] = data.methodology_context
            
        if data.approach_novelty is not None:
            update_fields.append("approach_novelty = :approach_novelty")
            params["approach_novelty"] = data.approach_novelty
        
        if update_fields:
            update_query = f"""
                UPDATE methodology_data
                SET {', '.join(update_fields)}
                WHERE user_id = :user_id 
                AND project_id = :project_id 
                AND paper_id = :paper_id
            """
            db.execute(text(update_query), params)
            db.commit()
    else:
        # Insert new record
        insert_query = """
            INSERT INTO methodology_data (
                user_id, project_id, paper_id,
                methodology_description, methodology_context, approach_novelty
            ) VALUES (
                :user_id, :project_id, :paper_id,
                :methodology_description, :methodology_context, :approach_novelty
            )
        """
        
        db.execute(text(insert_query), {
            "user_id": user_id,
            "project_id": project_id,
            "paper_id": paper_id,
            "methodology_description": data.methodology_description or "",
            "methodology_context": data.methodology_context or "",
            "approach_novelty": data.approach_novelty or ""
        })
        db.commit()
    
    return {"message": "Methodology data updated successfully"}
