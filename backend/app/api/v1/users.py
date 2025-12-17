"""
User API Endpoints for ResearchHub
Handles user-specific research data operations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

# Initialize service
user_service = UserService()

# Pydantic models for request/response
class SavePaperRequest(BaseModel):
    paper_id: int
    tags: Optional[List[str]] = None
    personal_notes: Optional[str] = None

class CreateNoteRequest(BaseModel):
    paper_id: Optional[int] = None
    title: Optional[str] = None
    content: str
    content_type: str = "markdown"

class UpdateNoteRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class CreateFolderRequest(BaseModel):
    title: str
    parent_id: Optional[int] = None

class CreateNoteFileRequest(BaseModel):
    title: str
    content: Optional[str] = ""
    content_type: str = "markdown"
    parent_id: Optional[int] = None
    paper_id: Optional[int] = None

class RenameItemRequest(BaseModel):
    new_title: str

class MoveItemRequest(BaseModel):
    new_parent_id: Optional[int] = None

class CreateReviewRequest(BaseModel):
    title: str
    description: Optional[str] = None
    paper_ids: Optional[List[int]] = None

class UpdateReviewRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    paper_ids: Optional[List[int]] = None

# Literature Review Enhanced Endpoints
class CreateAnnotationRequest(BaseModel):
    review_id: int
    paper_id: int
    methodology: Optional[str] = None
    sample_size: Optional[str] = None
    key_findings: List[str] = []
    limitations: List[str] = []
    notes: Optional[str] = None

class UpdateAnnotationRequest(BaseModel):
    methodology: Optional[str] = None
    sample_size: Optional[str] = None
    key_findings: Optional[List[str]] = None
    limitations: Optional[List[str]] = None
    notes: Optional[str] = None

class CreateFindingRequest(BaseModel):
    review_id: int
    description: str
    supporting_papers: List[int] = []
    finding_type: Optional[str] = None  # positive, negative, neutral
    evidence_level: Optional[str] = None  # strong, moderate, weak

class UpdateFindingRequest(BaseModel):
    description: Optional[str] = None
    supporting_papers: Optional[List[int]] = None
    finding_type: Optional[str] = None
    evidence_level: Optional[str] = None

# Phase 2: Research Analysis Models
class CreateComparisonRequest(BaseModel):
    project_id: int
    paper_ids: List[int]
    comparison_data: Optional[Dict[str, Any]] = None

class UpdateComparisonRequest(BaseModel):
    comparison_data: Optional[Dict[str, Any]] = None

class CreateCitationFormatRequest(BaseModel):
    project_id: int
    format_type: str  # 'APA', 'MLA', 'Chicago', 'Harvard'
    custom_template: Optional[str] = None

class UpdateCitationFormatRequest(BaseModel):
    format_type: Optional[str] = None
    custom_template: Optional[str] = None

class CreateThemeRequest(BaseModel):
    project_id: int
    theme_name: str
    theme_description: Optional[str] = None
    supporting_findings: List[int] = []
    theme_strength: Optional[str] = None  # strong, moderate, weak

class UpdateThemeRequest(BaseModel):
    theme_name: Optional[str] = None
    theme_description: Optional[str] = None
    supporting_findings: Optional[List[int]] = None
    theme_strength: Optional[str] = None

# Phase 3: Advanced Features Models
class CreateSpreadsheetTemplateRequest(BaseModel):
    project_id: int
    template_name: str
    template_config: Optional[Dict[str, Any]] = None

class UpdateSpreadsheetTemplateRequest(BaseModel):
    template_name: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None

class CreateSpreadsheetDataRequest(BaseModel):
    template_id: int
    project_id: int
    row_data: Dict[str, Any]
    cell_data: Optional[Dict[str, Any]] = None

class UpdateSpreadsheetDataRequest(BaseModel):
    row_data: Optional[Dict[str, Any]] = None
    cell_data: Optional[Dict[str, Any]] = None

class CreateAISynthesisRequest(BaseModel):
    project_id: int
    synthesis_type: str  # 'summary', 'comparison', 'theme_analysis', 'methodology', 'gap_analysis'
    input_data: Optional[Dict[str, Any]] = None
    ai_prompt: str

class CreateExportConfigurationRequest(BaseModel):
    project_id: int
    export_type: str  # 'word', 'excel', 'pdf', 'csv'
    template_name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

class UpdateExportConfigurationRequest(BaseModel):
    template_name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class CreateAnalysisTemplateRequest(BaseModel):
    project_id: int
    template_type: str  # 'comparison_matrix', 'evidence_table', 'methodology_table'
    template_config: Dict[str, Any]
    custom_fields: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None

class UpdateAnalysisTemplateRequest(BaseModel):
    template_type: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None

# Helper function to get user ID (for now, returns fixed test user)
def get_current_user_id() -> str:
    """Get current user ID - for now returns test user"""
    return "550e8400-e29b-41d4-a716-446655440000"

@router.post("/init")
async def init_user(db: Session = Depends(get_db)):
    """Initialize or get local user (no authentication required)"""
    try:
        user_id = user_service.init_local_user(db)
        return {"user_id": user_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize user: {str(e)}")

@router.post("/saved-papers")
async def save_paper(
    request: SavePaperRequest,
    db: Session = Depends(get_db)
):
    """Save a paper to user's library"""
    try:
        user_id = get_current_user_id()
        result = user_service.save_paper(
            db=db,
            user_id=user_id,
            paper_id=request.paper_id,
            tags=request.tags,
            personal_notes=request.personal_notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save paper: {str(e)}")

@router.delete("/saved-papers/{paper_id}")
async def unsave_paper(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Remove a paper from user's library"""
    try:
        user_id = get_current_user_id()
        success = user_service.unsave_paper(db, user_id, paper_id)
        if not success:
            raise HTTPException(status_code=404, detail="Paper not found in library")
        return {"status": "removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unsave paper: {str(e)}")

@router.get("/saved-papers")
async def get_saved_papers(db: Session = Depends(get_db)):
    """Get user's saved papers"""
    try:
        user_id = get_current_user_id()
        papers = user_service.get_saved_papers(db, user_id)
        return {"papers": papers, "total": len(papers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get saved papers: {str(e)}")

@router.get("/saved-papers/{paper_id}/check")
async def check_paper_saved(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Check if a paper is saved by user"""
    try:
        user_id = get_current_user_id()
        is_saved = user_service.is_paper_saved(db, user_id, paper_id)
        return {"is_saved": is_saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check paper status: {str(e)}")

@router.post("/notes")
async def create_note(
    request: CreateNoteRequest,
    db: Session = Depends(get_db)
):
    """Create a new note"""
    try:
        user_id = get_current_user_id()
        result = user_service.create_note(
            db=db,
            user_id=user_id,
            paper_id=request.paper_id,
            title=request.title,
            content=request.content,
            content_type=request.content_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")

@router.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    request: UpdateNoteRequest,
    db: Session = Depends(get_db)
):
    """Update an existing note"""
    try:
        user_id = get_current_user_id()
        success = user_service.update_note(
            db=db,
            user_id=user_id,
            note_id=note_id,
            title=request.title,
            content=request.content
        )
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update note: {str(e)}")

@router.get("/notes")
async def get_notes(
    paper_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get user's notes, optionally filtered by paper"""
    try:
        user_id = get_current_user_id()
        notes = user_service.get_notes(db, user_id, paper_id)
        return {"notes": notes, "total": len(notes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notes: {str(e)}")

@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    """Delete a note"""
    try:
        user_id = get_current_user_id()
        success = user_service.delete_note(db, user_id, note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {str(e)}")

@router.post("/notes/folder")
async def create_folder(
    request: CreateFolderRequest,
    db: Session = Depends(get_db)
):
    """Create a new folder"""
    try:
        user_id = get_current_user_id()
        result = user_service.create_note_folder(
            db=db,
            user_id=user_id,
            title=request.title,
            parent_id=request.parent_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create folder: {str(e)}")

@router.post("/notes/file")
async def create_note_file(
    request: CreateNoteFileRequest,
    db: Session = Depends(get_db)
):
    """Create a new note file"""
    try:
        user_id = get_current_user_id()
        result = user_service.create_note_in_folder(
            db=db,
            user_id=user_id,
            title=request.title,
            content=request.content,
            content_type=request.content_type,
            parent_id=request.parent_id,
            paper_id=request.paper_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create note: {str(e)}")

@router.patch("/notes/{item_id}/rename")
async def rename_item(
    item_id: int,
    request: RenameItemRequest,
    db: Session = Depends(get_db)
):
    """Rename a folder or note"""
    try:
        user_id = get_current_user_id()
        success = user_service.rename_note_folder(
            db=db,
            user_id=user_id,
            item_id=item_id,
            new_title=request.new_title
        )
        if not success:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "renamed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to rename item: {str(e)}")

@router.patch("/notes/{item_id}/move")
async def move_item(
    item_id: int,
    request: MoveItemRequest,
    db: Session = Depends(get_db)
):
    """Move a folder or note to a new parent"""
    try:
        user_id = get_current_user_id()
        success = user_service.move_note_folder(
            db=db,
            user_id=user_id,
            item_id=item_id,
            new_parent_id=request.new_parent_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "moved"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to move item: {str(e)}")

@router.delete("/notes/{item_id}/recursive")
async def delete_item_recursive(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete a folder or note with all contents"""
    try:
        user_id = get_current_user_id()
        success = user_service.delete_note_folder_recursive(db, user_id, item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")

@router.post("/literature-reviews")
async def create_literature_review(
    request: CreateReviewRequest,
    db: Session = Depends(get_db)
):
    """Create a new literature review"""
    try:
        user_id = get_current_user_id()
        result = user_service.create_literature_review(
            db=db,
            user_id=user_id,
            title=request.title,
            description=request.description,
            paper_ids=request.paper_ids
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create literature review: {str(e)}")

@router.post("/literature-reviews/{review_id}/seed")
async def seed_literature_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Seed a literature review with demo data (papers)"""
    try:
        user_id = get_current_user_id()
        success = user_service.seed_project_with_demo_data(db, user_id, review_id)
        if not success:
            raise HTTPException(status_code=404, detail="Literature review not found")
        return {"status": "seeded"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed project: {str(e)}")

@router.get("/literature-reviews")
async def get_literature_reviews(db: Session = Depends(get_db)):
    """Get user's literature reviews"""
    try:
        user_id = get_current_user_id()
        reviews = user_service.get_literature_reviews(db, user_id)
        return {"reviews": reviews, "total": len(reviews)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get literature reviews: {str(e)}")

@router.put("/literature-reviews/{review_id}")
async def update_literature_review(
    review_id: int,
    request: UpdateReviewRequest,
    db: Session = Depends(get_db)
):
    """Update a literature review"""
    try:
        user_id = get_current_user_id()
        success = user_service.update_literature_review(
            db=db,
            user_id=user_id,
            review_id=review_id,
            title=request.title,
            description=request.description,
            paper_ids=request.paper_ids
        )
        if not success:
            raise HTTPException(status_code=404, detail="Literature review not found")
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update literature review: {str(e)}")

@router.delete("/literature-reviews/{review_id}")
async def delete_literature_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Delete a literature review"""
    try:
        user_id = get_current_user_id()
        success = user_service.delete_literature_review(db, user_id, review_id)
        if not success:
            raise HTTPException(status_code=404, detail="Literature review not found")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete literature review: {str(e)}")

@router.get("/search-history")
async def get_search_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's search history"""
    try:
        user_id = get_current_user_id()
        history = user_service.get_search_history(db, user_id, limit)
        return {"history": history, "total": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get search history: {str(e)}")

@router.get("/stats")
async def get_user_stats(db: Session = Depends(get_db)):
    """Get user's research statistics"""
    try:
        user_id = get_current_user_id()
        user_uuid = user_id  # Already a string UUID

        # Get counts from database
        from app.models.user_models import (
            UserSavedPaper, UserNote, UserLiteratureReview, UserSearchHistory
        )

        saved_count = db.query(UserSavedPaper).filter(UserSavedPaper.user_id == user_uuid).count()
        notes_count = db.query(UserNote).filter(UserNote.user_id == user_uuid).count()
        reviews_count = db.query(UserLiteratureReview).filter(UserLiteratureReview.user_id == user_uuid).count()
        history_count = db.query(UserSearchHistory).filter(UserSearchHistory.user_id == user_uuid).count()

        return {
            "saved_papers": saved_count,
            "notes": notes_count,
            "literature_reviews": reviews_count,
            "search_history": history_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")




