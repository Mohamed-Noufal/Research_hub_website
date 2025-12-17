"""
API endpoints for Findings & Gaps data management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from uuid import uuid4

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()


# Request/Response Models
class GapCreate(BaseModel):
    description: str
    priority: str  # 'High', 'Medium', 'Low'
    notes: Optional[str] = None


class GapUpdate(BaseModel):
    description: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class Gap(BaseModel):
    id: str
    description: str
    priority: str
    notes: Optional[str]
    related_paper_ids: List[int] = []


class FindingUpdate(BaseModel):
    key_finding: Optional[str] = None
    limitations: Optional[str] = None
    custom_notes: Optional[str] = None


class Finding(BaseModel):
    paper_id: int
    title: str
    key_finding: Optional[str]
    limitations: Optional[str]


# ===== RESEARCH GAPS ENDPOINTS =====

@router.get("/projects/{project_id}/gaps")
async def get_research_gaps(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get all research gaps for a project"""
    
    query = """
        SELECT 
            rg.id,
            rg.description,
            rg.priority,
            rg.status,
            COALESCE(
                json_agg(gpa.paper_id) FILTER (WHERE gpa.paper_id IS NOT NULL),
                '[]'::json
            ) as related_paper_ids
        FROM research_gaps rg
        LEFT JOIN gap_paper_associations gpa ON gpa.gap_id = rg.id
        WHERE rg.user_id = :user_id AND rg.project_id = :project_id
        GROUP BY rg.id, rg.description, rg.priority, rg.status
        ORDER BY 
            CASE rg.priority 
                WHEN 'High' THEN 1 
                WHEN 'Medium' THEN 2 
                WHEN 'Low' THEN 3 
            END,
            rg.created_at DESC
    """
    
    result = db.execute(text(query), {"user_id": user_id, "project_id": project_id})
    gaps = []
    
    for row in result:
        gaps.append({
            "id": str(row.id),
            "description": row.description,
            "priority": row.priority,
            "notes": row.notes or "",
            "related_paper_ids": row.related_paper_ids or []
        })
    
    return {"gaps": gaps}


@router.post("/projects/{project_id}/gaps")
async def create_research_gap(
    project_id: int,
    gap: GapCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new research gap"""
    gap_id = str(uuid4())
    
    query = """
        INSERT INTO research_gaps (id, user_id, project_id, description, priority, notes)
        VALUES (:id, :user_id, :project_id, :description, :priority, :notes)
        RETURNING id
    """
    
    result = db.execute(text(query), {
        "id": gap_id,
        "user_id": user_id,
        "project_id": project_id,
        "description": gap.description,
        "priority": gap.priority,
        "notes": gap.notes or ""
    })
    db.commit()
    
    return {"message": "Research gap created successfully", "id": gap_id}


@router.patch("/projects/{project_id}/gaps/{gap_id}")
async def update_research_gap(
    project_id: int,
    gap_id: str,
    gap: GapUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update a research gap"""
    
    update_fields = []
    params = {"user_id": user_id, "project_id": project_id, "gap_id": gap_id}
    
    if gap.description is not None:
        update_fields.append("description = :description")
        params["description"] = gap.description
        
    if gap.priority is not None:
        update_fields.append("priority = :priority")
        params["priority"] = gap.priority
        
    if gap.notes is not None:
        update_fields.append("notes = :notes")
        params["notes"] = gap.notes
    
    if update_fields:
        query = f"""
            UPDATE research_gaps
            SET {', '.join(update_fields)}
            WHERE id = :gap_id AND user_id = :user_id AND project_id = :project_id
        """
        db.execute(text(query), params)
        db.commit()
    
    return {"message": "Research gap updated successfully"}


@router.delete("/projects/{project_id}/gaps/{gap_id}")
async def delete_research_gap(
    project_id: int,
    gap_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Delete a research gap"""
    
    query = """
        DELETE FROM research_gaps
        WHERE id = :gap_id AND user_id = :user_id AND project_id = :project_id
    """
    
    db.execute(text(query), {"gap_id": gap_id, "user_id": user_id, "project_id": project_id})
    db.commit()
    
    return {"message": "Research gap deleted successfully"}


# ===== FINDINGS ENDPOINTS =====

@router.get("/projects/{project_id}/findings")
async def get_findings(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get findings for all papers in a project"""
    
    query = """
        SELECT 
            p.id as paper_id,
            p.title,
            f.key_finding,
            f.limitations
        FROM papers p
        LEFT JOIN findings f ON (
            f.paper_id = p.id
            AND f.user_id = :user_id 
            AND f.project_id = :project_id
        )
        WHERE p.id IN (
            SELECT paper_id 
            FROM project_papers 
            WHERE project_id = :project_id
        )
        ORDER BY p.publication_date DESC, p.title
    """
    
    result = db.execute(text(query), {"user_id": user_id, "project_id": project_id})
    findings = []
    
    for row in result:
        findings.append({
            "paper_id": str(row.paper_id),
            "title": row.title,
            "key_finding": row.key_finding or "",
            "limitations": row.limitations or ""
        })
    
    return {"findings": findings}


@router.patch("/projects/{project_id}/findings/{paper_id}")
async def update_finding(
    project_id: int,
    paper_id: int,
    finding: FindingUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update findings for a specific paper"""
    
    # Check if finding exists
    check_query = """
        SELECT id FROM findings
        WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
    """
    
    existing = db.execute(
        text(check_query),
        {"user_id": user_id, "project_id": project_id, "paper_id": paper_id}
    ).fetchone()
    
    if existing:
        # Update existing
        update_fields = []
        params = {"user_id": user_id, "project_id": project_id, "paper_id": paper_id}
        
        if finding.key_finding is not None:
            update_fields.append("key_finding = :key_finding")
            params["key_finding"] = finding.key_finding
            
        if finding.limitations is not None:
            update_fields.append("limitations = :limitations")
            params["limitations"] = finding.limitations
            
        if finding.custom_notes is not None:
            update_fields.append("custom_notes = :custom_notes")
            params["custom_notes"] = finding.custom_notes
        
        if update_fields:
            query = f"""
                UPDATE findings
                SET {', '.join(update_fields)}
                WHERE user_id = :user_id AND project_id = :project_id AND paper_id = :paper_id
            """
            db.execute(text(query), params)
            db.commit()
    else:
        # Insert new
        query = """
            INSERT INTO findings (user_id, project_id, paper_id, key_finding, limitations, custom_notes)
            VALUES (:user_id, :project_id, :paper_id, :key_finding, :limitations, :custom_notes)
        """
        
        db.execute(text(query), {
            "user_id": user_id,
            "project_id": project_id,
            "paper_id": paper_id,
            "key_finding": finding.key_finding or "",
            "limitations": finding.limitations or "",
            "custom_notes": finding.custom_notes or ""
        })
        db.commit()
    
    return {"message": "Finding updated successfully"}
