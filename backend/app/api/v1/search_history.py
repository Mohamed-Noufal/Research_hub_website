"""
Search History API Endpoints
Handles user search history operations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.services.search_history_service import SearchHistoryService

router = APIRouter(prefix="/search-history", tags=["search-history"])

# Initialize service
search_history_service = SearchHistoryService()


# Pydantic models
class SaveSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    results_count: int = 0


# Helper to get user ID (matches users.py)
def get_current_user_id() -> str:
    """Get current user ID - for now returns test user"""
    return "550e8400-e29b-41d4-a716-446655440000"


@router.post("/save")
async def save_search(
    request: SaveSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Save a search to user's history
    
    **Request Body:**
    ```json
    {
      "query": "machine learning",
      "category": "ai_cs",
      "results_count": 20
    }
    ```
    """
    try:
        user_id = get_current_user_id()
        result = search_history_service.save_search(
            db=db,
            user_id=user_id,
            query=request.query,
            category=request.category,
            results_count=request.results_count
        )
        return {"status": "success", "search": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save search: {str(e)}"
        )


@router.get("/list")
async def get_search_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get user's search history
    
    **Query Parameters:**
    - limit: Maximum number of entries (default: 50)
    
    **Response:**
    ```json
    {
      "history": [
        {
          "id": 1,
          "query": "machine learning",
          "category": "ai_cs",
          "results_count": 20,
          "searched_at": "2025-11-22T15:30:00"
        }
      ],
      "total": 1
    }
    ```
    """
    try:
        user_id = get_current_user_id()
        history = search_history_service.get_search_history(
            db=db,
            user_id=user_id,
            limit=limit
        )
        return {"history": history, "total": len(history)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get search history: {str(e)}"
        )


@router.delete("/clear")
async def clear_search_history(
    db: Session = Depends(get_db)
):
    """Clear all search history for the current user"""
    try:
        user_id = get_current_user_id()
        search_history_service.clear_search_history(db=db, user_id=user_id)
        return {"status": "success", "message": "Search history cleared"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear search history: {str(e)}"
        )


@router.delete("/{search_id}")
async def delete_search_entry(
    search_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific search history entry"""
    try:
        user_id = get_current_user_id()
        success = search_history_service.delete_search_entry(
            db=db,
            user_id=user_id,
            search_id=search_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Search entry not found")
        return {"status": "success", "message": "Search entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete search entry: {str(e)}"
        )
