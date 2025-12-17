"""
API endpoints for Comparison tab data management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()


# Request/Response Models
class ComparisonConfig(BaseModel):
    selected_paper_ids: List[int]
    insights_similarities: Optional[str] = None
    insights_differences: Optional[str] = None


class ComparisonConfigUpdate(BaseModel):
    selected_paper_ids: Optional[List[int]] = None
    insights_similarities: Optional[str] = None
    insights_differences: Optional[str] = None


class AttributeUpdate(BaseModel):
    attribute_name: str
    attribute_value: str


# ===== COMPARISON CONFIG ENDPOINTS =====

@router.get("/projects/{project_id}/comparison/config")
async def get_comparison_config(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get comparison configuration for a project"""
    
    # Note: Use selected_paper_ids to match DB schema, mapped to selected_paper_ids in response
    query = """
        SELECT selected_paper_ids, selected_attributes, view_mode
        FROM comparison_configs
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    result = db.execute(text(query), {"user_id": user_id, "project_id": project_id}).fetchone()
    
    if result:
        return {
            "selected_paper_ids": result.selected_paper_ids or [],
            "selected_attributes": result.selected_attributes or {},
            "view_mode": result.view_mode or "table"
        }
    
    return {
        "selected_paper_ids": [],
        "selected_attributes": {},
        "view_mode": "table"
    }


@router.put("/projects/{project_id}/comparison/config")
async def update_comparison_config(
    project_id: int,
    config: ComparisonConfigUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update comparison configuration"""
    
    # Check if config exists
    check_query = """
        SELECT id FROM comparison_configs
        WHERE user_id = :user_id AND project_id = :project_id
    """
    
    existing = db.execute(
        text(check_query),
        {"user_id": user_id, "project_id": project_id}
    ).fetchone()
    
    if existing:
        # Update existing
        update_fields = []
        params = {"user_id": user_id, "project_id": project_id}
        
        if config.selected_paper_ids is not None:
            update_fields.append("selected_paper_ids = :selected_paper_ids")
            params["selected_paper_ids"] = config.selected_paper_ids
            
        if config.insights_similarities is not None:
            update_fields.append("insights_similarities = :insights_similarities")
            params["insights_similarities"] = config.insights_similarities
            
        if config.insights_differences is not None:
            update_fields.append("insights_differences = :insights_differences")
            params["insights_differences"] = config.insights_differences
        
        if update_fields:
            query = f"""
                UPDATE comparison_configs
                SET {', '.join(update_fields)}
                WHERE user_id = :user_id AND project_id = :project_id
            """
            db.execute(text(query), params)
            db.commit()
    else:
        # Insert new
        query = """
            INSERT INTO comparison_configs (
                user_id, project_id, selected_paper_ids, 
                insights_similarities, insights_differences
            ) VALUES (
                :user_id, :project_id, :selected_paper_ids,
                :insights_similarities, :insights_differences
            )
        """
        
        db.execute(text(query), {
            "user_id": user_id,
            "project_id": project_id,
            "selected_paper_ids": config.selected_paper_ids or [],
            "insights_similarities": config.insights_similarities or "",
            "insights_differences": config.insights_differences or ""
        })
        db.commit()
    
    return {"message": "Comparison config updated successfully"}


# ===== COMPARISON ATTRIBUTES ENDPOINTS =====

@router.get("/projects/{project_id}/comparison/attributes")
async def get_comparison_attributes(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Get all comparison attributes for a project"""
    
    query = """
        SELECT paper_id, attribute_name, attribute_value
        FROM comparison_attributes
        WHERE user_id = :user_id AND project_id = :project_id
        ORDER BY attribute_name, paper_id
    """
    
    result = db.execute(text(query), {"user_id": user_id, "project_id": project_id})
    attributes = {}
    
    for row in result:
        key = f"{row.paper_id}_{row.attribute_name}"
        attributes[key] = row.attribute_value or ""
    
    return {"attributes": attributes}


@router.patch("/projects/{project_id}/comparison/attributes/{paper_id}")
async def update_comparison_attribute(
    project_id: int,
    paper_id: int,
    attribute: AttributeUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Update a comparison attribute for a specific paper"""
    
    # Check if attribute exists
    check_query = """
        SELECT id FROM comparison_attributes
        WHERE user_id = :user_id 
        AND project_id = :project_id 
        AND paper_id = :paper_id
        AND attribute_name = :attribute_name
    """
    
    existing = db.execute(text(check_query), {
        "user_id": user_id,
        "project_id": project_id,
        "paper_id": paper_id,
        "attribute_name": attribute.attribute_name
    }).fetchone()
    
    if existing:
        # Update
        query = """
            UPDATE comparison_attributes
            SET attribute_value = :attribute_value
            WHERE user_id = :user_id 
            AND project_id = :project_id 
            AND paper_id = :paper_id
            AND attribute_name = :attribute_name
        """
    else:
        # Insert
        query = """
            INSERT INTO comparison_attributes (
                user_id, project_id, paper_id, attribute_name, attribute_value
            ) VALUES (
                :user_id, :project_id, :paper_id, :attribute_name, :attribute_value
            )
        """
    
    db.execute(text(query), {
        "user_id": user_id,
        "project_id": project_id,
        "paper_id": paper_id,
        "attribute_name": attribute.attribute_name,
        "attribute_value": attribute.attribute_value
    })
    db.commit()
    
    return {"message": "Attribute updated successfully"}
