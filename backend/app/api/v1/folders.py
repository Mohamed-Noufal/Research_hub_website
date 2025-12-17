from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.v1.users import get_current_user_id

router = APIRouter()

# Pydantic models
class FolderCreate(BaseModel):
    name: str
    description: Optional[str] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class FolderResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    paper_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Create folder
@router.post("/folders", response_model=FolderResponse)
def create_folder(
    folder: FolderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Create a new folder for organizing papers"""
    
    # Check if folder with same name already exists for this user
    existing = db.execute(
        text("SELECT id FROM folders WHERE user_id = :user_id AND name = :name"),
        {"user_id": user_id, "name": folder.name}
    ).fetchone()
    
    if existing:
        raise HTTPException(status_code=400, detail="Folder with this name already exists")
    
    # Create folder
    result = db.execute(
        text("""
        INSERT INTO folders (user_id, name, description)
        VALUES (:user_id, :name, :description)
        RETURNING id, name, description, created_at, updated_at
        """),
        {"user_id": user_id, "name": folder.name, "description": folder.description}
    )
    db.commit()
    
    folder_data = result.fetchone()
    
    return {
        "id": folder_data[0],
        "name": folder_data[1],
        "description": folder_data[2],
        "paper_count": 0,
        "created_at": folder_data[3],
        "updated_at": folder_data[4]
    }

# Get all folders for user
@router.get("/folders", response_model=List[FolderResponse])
def get_folders(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all folders for the current user with paper counts"""
    
    result = db.execute(
        text("""
        SELECT 
            f.id,
            f.name,
            f.description,
            f.created_at,
            f.updated_at,
            COUNT(fp.paper_id) as paper_count
        FROM folders f
        LEFT JOIN folder_papers fp ON f.id = fp.folder_id
        WHERE f.user_id = :user_id
        GROUP BY f.id, f.name, f.description, f.created_at, f.updated_at
        ORDER BY f.created_at DESC
        """),
        {"user_id": user_id}
    )
    
    folders = []
    for row in result.fetchall():
        folders.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "paper_count": row[5]
        })
    
    return folders

# Update folder
@router.put("/folders/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: int,
    folder_update: FolderUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update folder name or description"""
    
    # Check if folder exists and belongs to user
    existing = db.execute(
        text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
        {"id": folder_id, "user_id": user_id}
    ).fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Build update query
    updates = []
    params = {"id": folder_id, "user_id": user_id}
    
    if folder_update.name is not None:
        updates.append("name = :name")
        params["name"] = folder_update.name
    
    if folder_update.description is not None:
        updates.append("description = :description")
        params["description"] = folder_update.description
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    
    # Update folder
    db.execute(
        text(f"""
        UPDATE folders 
        SET {', '.join(updates)}
        WHERE id = :id AND user_id = :user_id
        """),
        params
    )
    db.commit()
    
    # Get updated folder with paper count
    result = db.execute(
        text("""
        SELECT 
            f.id, f.name, f.description, f.created_at, f.updated_at,
            COUNT(fp.paper_id) as paper_count
        FROM folders f
        LEFT JOIN folder_papers fp ON f.id = fp.folder_id
        WHERE f.id = :id
        GROUP BY f.id
        """),
        {"id": folder_id}
    ).fetchone()
    
    return {
        "id": result[0],
        "name": result[1],
        "description": result[2],
        "created_at": result[3],
        "updated_at": result[4],
        "paper_count": result[5]
    }

# Delete folder
@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Delete a folder (papers remain in library)"""
    
    # Check if folder exists and belongs to user
    existing = db.execute(
        text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
        {"id": folder_id, "user_id": user_id}
    ).fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Delete folder (cascade will delete folder_papers entries)
    db.execute(
        text("DELETE FROM folders WHERE id = :id AND user_id = :user_id"),
        {"id": folder_id, "user_id": user_id}
    )
    db.commit()
    
    return {"message": "Folder deleted successfully"}

# Add paper to folder
@router.post("/folders/{folder_id}/papers/{paper_id}")
def add_paper_to_folder(
    folder_id: int,
    paper_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Add a paper to a folder"""
    
    # Check if folder exists and belongs to user
    folder = db.execute(
        text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
        {"id": folder_id, "user_id": user_id}
    ).fetchone()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Check if paper exists (don't check user_id since papers can be from search results)
    paper = db.execute(
        text("SELECT id FROM papers WHERE id = :id"),
        {"id": paper_id}
    ).fetchone()
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if already in folder
    existing = db.execute(
        text("SELECT 1 FROM folder_papers WHERE folder_id = :folder_id AND paper_id = :paper_id"),
        {"folder_id": folder_id, "paper_id": paper_id}
    ).fetchone()
    
    if existing:
        return {"message": "Paper already in folder"}
    
    # Add to folder
    db.execute(
        text("INSERT INTO folder_papers (folder_id, paper_id) VALUES (:folder_id, :paper_id)"),
        {"folder_id": folder_id, "paper_id": paper_id}
    )
    db.commit()
    
    return {"message": "Paper added to folder"}

# Remove paper from folder
@router.delete("/folders/{folder_id}/papers/{paper_id}")
def remove_paper_from_folder(
    folder_id: int,
    paper_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Remove a paper from a folder"""
    
    # Check if folder exists and belongs to user
    folder = db.execute(
        text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
        {"id": folder_id, "user_id": user_id}
    ).fetchone()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Remove from folder
    db.execute(
        text("DELETE FROM folder_papers WHERE folder_id = :folder_id AND paper_id = :paper_id"),
        {"folder_id": folder_id, "paper_id": paper_id}
    )
    db.commit()
    
    return {"message": "Paper removed from folder"}

# Get papers in a folder
@router.get("/folders/{folder_id}/papers")
def get_folder_papers(
    folder_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all papers in a specific folder"""
    
    # Check if folder exists and belongs to user
    folder = db.execute(
        text("SELECT id FROM folders WHERE id = :id AND user_id = :user_id"),
        {"id": folder_id, "user_id": user_id}
    ).fetchone()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Get papers in folder (don't filter by user_id since papers can be from search results)
    result = db.execute(
        text("""
        SELECT p.id
        FROM papers p
        INNER JOIN folder_papers fp ON p.id = fp.paper_id
        WHERE fp.folder_id = :folder_id
        ORDER BY fp.added_at DESC
        """),
        {"folder_id": folder_id}
    )
    
    paper_ids = [row[0] for row in result.fetchall()]
    
    return {"paper_ids": paper_ids}
