"""
Search History Service
Handles saving and retrieving user search history
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any
from app.models.user_models import UserSearchHistory


class SearchHistoryService:
    """Service for managing user search history"""
    
    def save_search(
        self,
        db: Session,
        user_id: str,
        query: str,
        category: str = None,
        results_count: int = 0
    ) -> Dict[str, Any]:
        """
        Save a search to user's history
        
        Args:
            db: Database session
            user_id: User UUID
            query: Search query
            category: Search category
            results_count: Number of results returned
            
        Returns:
            Dict with saved search info
        """
        try:
            # Create new search history entry
            search_entry = UserSearchHistory(
                user_id=user_id,
                query=query,
                category=category,
                results_count=results_count,
                searched_at=datetime.utcnow()
            )
            
            db.add(search_entry)
            db.commit()
            db.refresh(search_entry)
            
            return {
                "id": search_entry.id,
                "query": search_entry.query,
                "category": search_entry.category,
                "results_count": search_entry.results_count,
                "searched_at": search_entry.searched_at.isoformat()
            }
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to save search history: {str(e)}")
    
    def get_search_history(
        self,
        db: Session,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get user's search history
        
        Args:
            db: Database session
            user_id: User UUID
            limit: Maximum number of entries to return
            
        Returns:
            List of search history entries
        """
        try:
            searches = db.query(UserSearchHistory)\
                .filter(UserSearchHistory.user_id == user_id)\
                .order_by(UserSearchHistory.searched_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    "id": s.id,
                    "query": s.query,
                    "category": s.category,
                    "results_count": s.results_count,
                    "searched_at": s.searched_at.isoformat()
                }
                for s in searches
            ]
        except Exception as e:
            raise Exception(f"Failed to get search history: {str(e)}")
    
    def clear_search_history(
        self,
        db: Session,
        user_id: str
    ) -> bool:
        """
        Clear all search history for a user
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            True if successful
        """
        try:
            db.query(UserSearchHistory)\
                .filter(UserSearchHistory.user_id == user_id)\
                .delete()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to clear search history: {str(e)}")
    
    def delete_search_entry(
        self,
        db: Session,
        user_id: str,
        search_id: int
    ) -> bool:
        """
        Delete a specific search history entry
        
        Args:
            db: Database session
            user_id: User UUID
            search_id: Search history entry ID
            
        Returns:
            True if successful
        """
        try:
            result = db.query(UserSearchHistory)\
                .filter(
                    UserSearchHistory.id == search_id,
                    UserSearchHistory.user_id == user_id
                )\
                .delete()
            db.commit()
            return result > 0
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to delete search entry: {str(e)}")
