"""
User Service for ResearchHub
Handles user-specific research data operations
"""

import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime

from app.models.user_models import (
    LocalUser, UserSavedPaper, UserNote,
    UserLiteratureReview, UserUpload, UserSearchHistory
)
from app.models.paper import Paper

class UserService:
    """Service for managing user research data"""

    def __init__(self):
        pass

    def init_local_user(self, db: Session, device_info: Optional[Dict[str, Any]] = None) -> str:
        """Create or get a local user (no authentication required)"""
        try:
            # For now, return a fixed test user ID
            # In production, you might want to generate unique IDs per browser/device
            user_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440000')

            # Check if user exists
            user = db.query(LocalUser).filter(LocalUser.id == user_id).first()

            if not user:
                # Create new user
                user = LocalUser(
                    id=user_id,
                    device_info=device_info or {"browser": "unknown"}
                )
                db.add(user)
                db.commit()
                print(f"✅ Created new local user: {user_id}")
            else:
                # Update last active
                user.last_active = datetime.utcnow()
                db.commit()
                print(f"✅ Found existing local user: {user_id}")

            return str(user_id)

        except Exception as e:
            print(f"❌ Error initializing local user: {e}")
            db.rollback()
            raise

    def save_paper(self, db: Session, user_id: str, paper_id: int,
                   tags: Optional[List[str]] = None,
                   personal_notes: Optional[str] = None) -> Dict[str, Any]:
        """Save a paper to user's library"""
        try:
            user_uuid = uuid.UUID(user_id)

            # Check if already saved
            existing = db.query(UserSavedPaper).filter(
                UserSavedPaper.user_id == user_uuid,
                UserSavedPaper.paper_id == paper_id
            ).first()

            if existing:
                # Update existing save
                if tags is not None:
                    existing.tags = tags
                if personal_notes is not None:
                    existing.personal_notes = personal_notes
                db.commit()
                return {"status": "updated", "id": existing.id}

            # Create new saved paper
            saved_paper = UserSavedPaper(
                user_id=user_uuid,
                paper_id=paper_id,
                tags=tags or [],
                personal_notes=personal_notes
            )

            db.add(saved_paper)
            db.commit()

            return {"status": "saved", "id": saved_paper.id}

        except Exception as e:
            print(f"❌ Error saving paper: {e}")
            db.rollback()
            raise

    def unsave_paper(self, db: Session, user_id: str, paper_id: int) -> bool:
        """Remove a paper from user's library"""
        try:
            user_uuid = uuid.UUID(user_id)

            deleted = db.query(UserSavedPaper).filter(
                UserSavedPaper.user_id == user_uuid,
                UserSavedPaper.paper_id == paper_id
            ).delete()

            db.commit()
            return deleted > 0

        except Exception as e:
            print(f"❌ Error unsaving paper: {e}")
            db.rollback()
            raise

    def get_saved_papers(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get user's saved papers with full paper details"""
        try:
            user_uuid = uuid.UUID(user_id)

            saved_papers = db.query(UserSavedPaper).filter(
                UserSavedPaper.user_id == user_uuid
            ).join(Paper).all()

            result = []
            for saved in saved_papers:
                paper_data = saved.paper.to_dict()
                paper_data.update({
                    "saved_at": saved.saved_at.isoformat() if saved.saved_at else None,
                    "tags": saved.tags or [],
                    "personal_notes": saved.personal_notes,
                    "read_status": saved.read_status,
                    "rating": saved.rating
                })
                result.append(paper_data)

            return result

        except Exception as e:
            print(f"❌ Error getting saved papers: {e}")
            raise

    def is_paper_saved(self, db: Session, user_id: str, paper_id: int) -> bool:
        """Check if a paper is saved by user"""
        try:
            user_uuid = uuid.UUID(user_id)

            count = db.query(UserSavedPaper).filter(
                UserSavedPaper.user_id == user_uuid,
                UserSavedPaper.paper_id == paper_id
            ).count()

            return count > 0

        except Exception as e:
            print(f"❌ Error checking if paper is saved: {e}")
            raise

    def create_note(self, db: Session, user_id: str, paper_id: Optional[int],
                   title: Optional[str], content: str,
                   content_type: str = "markdown") -> Dict[str, Any]:
        """Create a new note"""
        try:
            user_uuid = uuid.UUID(user_id)

            note = UserNote(
                user_id=user_uuid,
                paper_id=paper_id,
                title=title,
                content=content,
                content_type=content_type
            )

            db.add(note)
            db.commit()

            return {
                "id": note.id,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat()
            }

        except Exception as e:
            print(f"❌ Error creating note: {e}")
            db.rollback()
            raise

    def update_note(self, db: Session, user_id: str, note_id: int,
                   title: Optional[str] = None, content: Optional[str] = None) -> bool:
        """Update an existing note"""
        try:
            user_uuid = uuid.UUID(user_id)

            note = db.query(UserNote).filter(
                UserNote.id == note_id,
                UserNote.user_id == user_uuid
            ).first()

            if not note:
                return False

            if title is not None:
                note.title = title
            if content is not None:
                note.content = content

            db.commit()
            return True

        except Exception as e:
            print(f"❌ Error updating note: {e}")
            db.rollback()
            raise

    def get_notes_flat(self, db: Session, user_id: str, paper_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get user's notes as flat list, optionally filtered by paper (legacy method for backward compatibility)"""
        try:
            user_uuid = uuid.UUID(user_id)

            query = db.query(UserNote).filter(UserNote.user_id == user_uuid)

            if paper_id is not None:
                query = query.filter(UserNote.paper_id == paper_id)

            notes = query.order_by(desc(UserNote.updated_at)).all()

            return [{
                "id": note.id,
                "paper_id": note.paper_id,
                "title": note.title,
                "content": note.content,
                "content_type": note.content_type,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat()
            } for note in notes]

        except Exception as e:
            print(f"❌ Error getting notes: {e}")
            raise

    def get_notes_hierarchy(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get user's notes with full folder hierarchy"""
        try:
            user_uuid = uuid.UUID(user_id)

            # Get all notes for user
            notes = db.query(UserNote).filter(
                UserNote.user_id == user_uuid
            ).order_by(UserNote.level, UserNote.title).all()

            # Build hierarchy
            hierarchy = []
            note_map = {note.id: note for note in notes}

            for note in notes:
                if note.parent_id is None:  # Root level items
                    hierarchy.append(self._note_to_dict(note))

            return hierarchy

        except Exception as e:
            print(f"❌ Error getting notes hierarchy: {e}")
            raise

    def _note_to_dict(self, note: UserNote) -> Dict[str, Any]:
        """Convert note model to dictionary with children"""
        result = {
            "id": note.id,
            "paper_id": note.paper_id,
            "title": note.title,
            "content": note.content,
            "content_type": note.content_type,
            "parent_id": note.parent_id,
            "path": note.path,
            "is_folder": note.is_folder,
            "level": note.level,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
            "children": []
        }

        # Add children if it's a folder
        if note.is_folder and hasattr(note, 'children'):
            result["children"] = [self._note_to_dict(child) for child in note.children]

        return result

    def create_note_folder(self, db: Session, user_id: str,
                          title: str, parent_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new note folder"""
        try:
            user_uuid = uuid.UUID(user_id)

            # Calculate level and path
            level = 0
            path = f"/{title}"

            if parent_id:
                parent = db.query(UserNote).filter(
                    UserNote.id == parent_id,
                    UserNote.user_id == user_uuid,
                    UserNote.is_folder == True
                ).first()

                if not parent:
                    raise ValueError("Parent folder not found")

                level = parent.level + 1
                path = f"{parent.path}/{title}"

            folder = UserNote(
                user_id=user_uuid,
                title=title,
                content=None,
                content_type="folder",
                parent_id=parent_id,
                path=path,
                is_folder=True,
                level=level
            )

            db.add(folder)
            db.commit()

            return {
                "id": folder.id,
                "title": folder.title,
                "is_folder": True,
                "parent_id": folder.parent_id,
                "path": folder.path,
                "level": folder.level,
                "created_at": folder.created_at.isoformat()
            }

        except Exception as e:
            print(f"❌ Error creating note folder: {e}")
            db.rollback()
            raise

    def create_note_in_folder(self, db: Session, user_id: str,
                             title: str, content: str = "",
                             content_type: str = "markdown",
                             parent_id: Optional[int] = None,
                             paper_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new note (file) in a folder or at root level"""
        try:
            user_uuid = uuid.UUID(user_id)

            # Calculate level and path
            level = 0
            path = f"/{title}"

            if parent_id:
                parent = db.query(UserNote).filter(
                    UserNote.id == parent_id,
                    UserNote.user_id == user_uuid,
                    UserNote.is_folder == True
                ).first()

                if parent:
                    level = parent.level + 1
                    path = f"{parent.path}/{title}.md"
                else:
                    # Parent folder not found, create at root
                    pass

            note = UserNote(
                user_id=user_uuid,
                paper_id=paper_id,
                title=title,
                content=content,
                content_type=content_type,
                parent_id=parent_id,
                path=path,
                is_folder=False,
                level=level
            )

            db.add(note)
            db.commit()

            return {
                "id": note.id,
                "title": note.title,
                "is_folder": False,
                "parent_id": note.parent_id,
                "path": note.path,
                "level": note.level,
                "content": note.content,
                "content_type": note.content_type,
                "created_at": note.created_at.isoformat()
            }

        except Exception as e:
            print(f"❌ Error creating note in folder: {e}")
            db.rollback()
            raise

    def move_note_folder(self, db: Session, user_id: str,
                        item_id: int, new_parent_id: Optional[int]) -> bool:
        """Move a note or folder to a new parent folder"""
        try:
            user_uuid = uuid.UUID(user_id)

            item = db.query(UserNote).filter(
                UserNote.id == item_id,
                UserNote.user_id == user_uuid
            ).first()

            if not item:
                return False

            # Prevent moving into self or descendants
            if new_parent_id:
                parent_candidate = db.query(UserNote).filter(
                    UserNote.id == new_parent_id,
                    UserNote.user_id == user_uuid
                ).first()

                if not parent_candidate or not parent_candidate.is_folder:
                    raise ValueError("Invalid parent folder")

                # Check if new parent is a descendant of current item
                current_parent = parent_candidate
                while current_parent:
                    if current_parent.id == item_id:
                        raise ValueError("Cannot move folder into its own descendant")
                    current_parent = current_parent.parent
            else:
                # Moving to root level
                pass

            # Update parent
            old_parent_id = item.parent_id
            item.parent_id = new_parent_id

            # Recalculate path and level
            self._update_note_path_and_level(db, item)

            db.commit()
            return True

        except Exception as e:
            print(f"❌ Error moving note/folder: {e}")
            db.rollback()
            raise

    def _update_note_path_and_level(self, db: Session, note: UserNote):
        """Update path and level for a note/folder and all descendants"""
        # Calculate new level and path
        level = 0
        path = f"/{note.title}"

        if note.is_folder:
            path = f"/{note.title}"
        else:
            path = f"/{note.title}.md"

        if note.parent_id:
            parent = db.query(UserNote).filter(UserNote.id == note.parent_id).first()
            if parent:
                level = parent.level + 1
                if note.is_folder:
                    path = f"{parent.path}/{note.title}"
                else:
                    path = f"{parent.path}/{note.title}.md"

        note.level = level
        note.path = path

        # Update descendants recursively
        if note.is_folder:
            for child in note.children:
                if child:  # SQLAlchemy relationship might be lazy
                    self._update_note_path_and_level(db, child)

    def rename_note_folder(self, db: Session, user_id: str,
                          item_id: int, new_title: str) -> bool:
        """Rename a note or folder"""
        try:
            user_uuid = uuid.UUID(user_id)

            item = db.query(UserNote).filter(
                UserNote.id == item_id,
                UserNote.user_id == user_uuid
            ).first()

            if not item:
                return False

            # Prevent duplicate names in same folder
            sibling_query = db.query(UserNote.id).filter(
                UserNote.user_id == user_uuid,
                UserNote.parent_id == item.parent_id,
                UserNote.title == new_title,
                UserNote.id != item_id
            )

            if db.query(sibling_query.exists()).scalar():
                raise ValueError("Item with this name already exists in the folder")

            old_title = item.title
            item.title = new_title

            # Update path for item and descendants
            self._update_note_path_and_level(db, item)

            db.commit()
            return True

        except Exception as e:
            print(f"❌ Error renaming note/folder: {e}")
            db.rollback()
            raise

    def delete_note_folder_recursive(self, db: Session, user_id: str, item_id: int) -> bool:
        """Delete a note or folder and all its contents"""
        try:
            user_uuid = uuid.UUID(user_id)

            item = db.query(UserNote).filter(
                UserNote.id == item_id,
                UserNote.user_id == user_uuid
            ).first()

            if not item:
                return False

            # Use CASCADE delete (SQLAlchemy will handle this due to relationship settings)
            db.delete(item)
            db.commit()
            return True

        except Exception as e:
            print(f"❌ Error deleting note/folder: {e}")
            db.rollback()
            raise

    # Backward compatibility - alias get_notes to flat version
    def get_notes(self, db: Session, user_id: str, paper_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Backward compatibility method - use get_notes_flat or get_notes_hierarchy"""
        return self.get_notes_flat(db, user_id, paper_id)

    def delete_note(self, db: Session, user_id: str, note_id: int) -> bool:
        """Delete a note"""
        try:
            user_uuid = uuid.UUID(user_id)

            deleted = db.query(UserNote).filter(
                UserNote.id == note_id,
                UserNote.user_id == user_uuid
            ).delete()

            db.commit()
            return deleted > 0

        except Exception as e:
            print(f"❌ Error deleting note: {e}")
            db.rollback()
            raise

    def create_literature_review(self, db: Session, user_id: str,
                               title: str, description: Optional[str] = None,
                               paper_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Create a new literature review"""
        try:
            user_uuid = uuid.UUID(user_id)

            review = UserLiteratureReview(
                user_id=user_uuid,
                title=title,
                description=description,
                paper_ids=paper_ids or []
            )

            db.add(review)
            db.commit()

            # Sync project_papers table
            if paper_ids:
                self._sync_project_papers(db, review.id, paper_ids, str(user_uuid))

            return {
                "id": review.id,
                "created_at": review.created_at.isoformat(),
                "updated_at": review.updated_at.isoformat()
            }

        except Exception as e:
            print(f"❌ Error creating literature review: {e}")
            db.rollback()
            raise

    def get_literature_reviews(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get user's literature reviews"""
        try:
            user_uuid = uuid.UUID(user_id)

            reviews = db.query(UserLiteratureReview).filter(
                UserLiteratureReview.user_id == user_uuid
            ).order_by(desc(UserLiteratureReview.updated_at)).all()

            return [{
                "id": review.id,
                "title": review.title,
                "description": review.description,
                "paper_ids": review.paper_ids or [],
                "created_at": review.created_at.isoformat() if review.created_at else None,
                "updated_at": review.updated_at.isoformat() if review.updated_at else None
            } for review in reviews]

        except Exception as e:
            print(f"❌ Error getting literature reviews: {e}")
            raise

    def update_literature_review(self, db: Session, user_id: str, review_id: int,
                               title: Optional[str] = None,
                               description: Optional[str] = None,
                               paper_ids: Optional[List[int]] = None) -> bool:
        """Update a literature review"""
        try:
            user_uuid = uuid.UUID(user_id)

            review = db.query(UserLiteratureReview).filter(
                UserLiteratureReview.id == review_id,
                UserLiteratureReview.user_id == user_uuid
            ).first()

            if not review:
                return False

            if title is not None:
                review.title = title
            if description is not None:
                review.description = description
            if paper_ids is not None:
                review.paper_ids = paper_ids
                # Sync project_papers table
                self._sync_project_papers(db, review_id, paper_ids, user_id)

            db.commit()
            return True

        except Exception as e:
            print(f"❌ Error updating literature review: {e}")
            db.rollback()
            raise

    def delete_literature_review(self, db: Session, user_id: str, review_id: int) -> bool:
        """Delete a literature review"""
        try:
            user_uuid = uuid.UUID(user_id)

            deleted = db.query(UserLiteratureReview).filter(
                UserLiteratureReview.id == review_id,
                UserLiteratureReview.user_id == user_uuid
            ).delete()

            db.commit()
            return deleted > 0

        except Exception as e:
            print(f"❌ Error deleting literature review: {e}")
            db.rollback()
            raise

    def add_search_to_history(self, db: Session, user_id: str,
                            query: str, category: Optional[str],
                            results_count: int = 0):
        """Add a search to user's history"""
        try:
            user_uuid = uuid.UUID(user_id)

            search = UserSearchHistory(
                user_id=user_uuid,
                query=query,
                category=category,
                results_count=results_count
            )

            db.add(search)
            db.commit()

        except Exception as e:
            print(f"❌ Error adding search to history: {e}")
            db.rollback()

    def get_search_history(self, db: Session, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's search history"""
        try:
            user_uuid = uuid.UUID(user_id)

            searches = db.query(UserSearchHistory).filter(
                UserSearchHistory.user_id == user_uuid
            ).order_by(desc(UserSearchHistory.searched_at)).limit(limit).all()

            return [{
                "id": search.id,
                "query": search.query,
                "category": search.category,
                "results_count": search.results_count,
                "searched_at": search.searched_at.isoformat()
            } for search in searches]

        except Exception as e:
            print(f"❌ Error getting search history: {e}")
            raise

    def _sync_project_papers(self, db: Session, project_id: int, paper_ids: List[int], user_id: str):
        """Sync paper_ids to project_papers table for JOIN queries"""
        try:
            # Delete existing
            db.execute(
                text("DELETE FROM project_papers WHERE project_id = :project_id"),
                {"project_id": project_id}
            )
            
            if not paper_ids:
                return

            # Insert new
            values = []
            for pid in set(paper_ids):  # Ensure unique
                values.append(f"({project_id}, {pid}, '{user_id}')")
            
            if values:
                # Use raw SQL for bulk insert
                sql = f"""
                    INSERT INTO project_papers (project_id, paper_id, added_by)
                    VALUES {','.join(values)}
                    ON CONFLICT (project_id, paper_id) DO NOTHING
                """
                db.execute(text(sql))
                db.commit()
                
        except Exception as e:
            print(f"❌ Error syncing project papers: {e}")
            # Don't raise, just log - main update succeeded

    def seed_project_with_demo_data(self, db: Session, user_id: str, project_id: int) -> bool:
        """
        Seed a project with comprehensive demo papers and template data for ALL tabs.
        Creates papers if they don't exist, adds them to the project,
        and populates ALL literature review tabs with realistic example data.
        This gives new users a complete vision of how to use the feature.
        """
        try:
            user_uuid = uuid.UUID(user_id)
            
            # 1. Define Mock Papers (matches frontend mockData.ts roughly)
            demo_papers = [
                {
                    "id": 1,
                    "title": "Deep Learning for Medical Diagnosis: A Systematic Review",
                    "authors": ["Smith, J.", "Johnson, M.", "Williams, R."],
                    "publication_date": datetime(2023, 1, 15),
                    "year": 2023,
                    "abstract": "We review deep learning applications in medical imaging, analyzing 150 studies published between 2018-2023. Our meta-analysis compares DL algorithms to radiologists across multiple diagnostic tasks.",
                    "venue": "Nature Medicine",
                    "citation_count": 150,
                    "source": "demo",
                    "methodology": "Systematic Review",
                    "methodology_type": "Meta-Analysis"
                },
                {
                    "id": 2,
                    "title": "AI Adoption in Clinical Practice: Barriers and Opportunities",
                    "authors": ["Johnson, K.", "Lee, S."],
                    "publication_date": datetime(2022, 5, 20),
                    "year": 2022,
                    "abstract": "Survey of 500 clinics regarding AI adoption challenges and success factors. Identifies key barriers and provides implementation framework.",
                    "venue": "JAMA",
                    "citation_count": 89,
                    "source": "demo",
                    "methodology": "Survey Study",
                    "methodology_type": "Quantitative"
                },
                {
                    "id": 3,
                    "title": "Neural Networks in Radiology: Real-World Implementation",
                    "authors": ["Chen, L.", "Wang, X."],
                    "publication_date": datetime(2023, 3, 10),
                    "year": 2023,
                    "abstract": "Case study of neural network deployment in a large hospital system. Documents implementation challenges and clinical outcomes over 18 months.",
                    "venue": "Radiology",
                    "citation_count": 45,
                    "source": "demo",
                    "methodology": "Case Study",
                    "methodology_type": "Qualitative"
                },
                {
                    "id": 4,
                    "title": "Machine Learning in Predictive Healthcare Analytics",
                    "authors": ["Brown, A.", "Davis, M."],
                    "publication_date": datetime(2023, 8, 5),
                    "year": 2023,
                    "abstract": "Meta-analysis of ML models for patient outcome prediction. Evaluates 85 studies across multiple healthcare domains.",
                    "venue": "The Lancet Digital Health",
                    "citation_count": 210,
                    "source": "demo",
                    "methodology": "Meta-Analysis",
                    "methodology_type": "Quantitative"
                },
                {
                    "id": 5,
                    "title": "Ethical Considerations in AI-Driven Diagnosis",
                    "authors": ["Martinez, R."],
                    "publication_date": datetime(2022, 11, 12),
                    "year": 2022,
                    "abstract": "Review of ethical frameworks for AI in healthcare. Proposes guidelines for responsible AI deployment in clinical settings.",
                    "venue": "AI & Ethics",
                    "citation_count": 35,
                    "source": "demo",
                    "methodology": "Literature Review",
                    "methodology_type": "Qualitative"
                }
            ]

            paper_ids = []
            
            # 2. Insert Papers if they don't exist
            for p_data in demo_papers:
                paper = db.query(Paper).filter(Paper.id == p_data["id"]).first()
                if not paper:
                    paper = Paper(
                        id=p_data["id"],
                        title=p_data["title"],
                        authors=p_data["authors"],
                        publication_date=p_data["publication_date"],
                        year=p_data.get("year"),
                        abstract=p_data["abstract"],
                        venue=p_data["venue"],
                        citation_count=p_data["citation_count"],
                        source=p_data["source"],
                        methodology=p_data.get("methodology"),
                        methodology_type=p_data.get("methodology_type"),
                        is_processed=True
                    )
                    db.add(paper)
                    db.flush()
                
                paper_ids.append(paper.id)
                
                # Ensure saved to user library
                self.save_paper(db, user_id, paper.id, tags=["demo", "template"])

            db.commit()

            # 3. Link to Project
            current_review = db.query(UserLiteratureReview).filter(
                UserLiteratureReview.id == project_id,
                UserLiteratureReview.user_id == user_uuid
            ).first()

            if not current_review:
                return False

            # Merge existing IDs with new demo IDs
            existing_ids = current_review.paper_ids or []
            updated_ids = list(set(existing_ids + paper_ids))
            current_review.paper_ids = updated_ids
            
            # Sync project_papers
            self._sync_project_papers(db, project_id, updated_ids, str(user_uuid))
            
            # 4. POPULATE ALL TAB DATA WITH COMPREHENSIVE TEMPLATES
            try:
                # ===== METHODOLOGY TAB =====
                methodology_data = [
                    {
                        "paper_id": "1",
                        "description": "Systematic review of 150 studies published between 2018-2023 comparing DL algorithms to radiologists across multiple diagnostic tasks.",
                        "context": "Medical Imaging Diagnosis - Focus on X-ray, CT, and MRI interpretation",
                        "novelty": "First comprehensive meta-analysis including multi-modal imaging data and diverse patient demographics"
                    },
                    {
                        "paper_id": "2",
                        "description": "Cross-sectional survey of 500 healthcare facilities across 15 countries. Mixed-methods approach combining quantitative metrics and qualitative interviews.",
                        "context": "Healthcare Technology Adoption - Primary care and hospital settings",
                        "novelty": "Largest international survey on AI adoption barriers with validated measurement instruments"
                    },
                    {
                        "paper_id": "3",
                        "description": "18-month longitudinal case study tracking neural network deployment in a 600-bed hospital. Includes implementation timeline, training protocols, and outcome metrics.",
                        "context": "Clinical Implementation - Real-world radiology workflow integration",
                        "novelty": "First detailed documentation of end-to-end AI deployment in a large healthcare system"
                    },
                    {
                        "paper_id": "4",
                        "description": "Meta-analysis of 85 machine learning studies for patient outcome prediction. Includes risk stratification, readmission prediction, and mortality forecasting models.",
                        "context": "Predictive Analytics - Multiple clinical domains and patient populations",
                        "novelty": "Comprehensive comparison of ML architectures with standardized performance metrics"
                    },
                    {
                        "paper_id": "5",
                        "description": "Systematic literature review of 120 papers on AI ethics in healthcare. Synthesizes existing frameworks and proposes unified guidelines.",
                        "context": "Healthcare Ethics - Focus on diagnostic AI and clinical decision support",
                        "novelty": "First unified ethical framework specifically designed for AI-driven medical diagnosis"
                    }
                ]
                
                for meth in methodology_data:
                    db.execute(text("""
                        INSERT INTO methodology_data (
                            user_id, project_id, paper_id,
                            methodology_description, methodology_context, approach_novelty
                        ) VALUES (
                            :user_id, :project_id, :paper_id,
                            :description, :context, :novelty
                        ) ON CONFLICT (user_id, project_id, paper_id) DO UPDATE
                        SET methodology_description = EXCLUDED.methodology_description,
                            methodology_context = EXCLUDED.methodology_context,
                            approach_novelty = EXCLUDED.approach_novelty
                    """), {
                        "user_id": str(user_uuid),
                        "project_id": project_id,
                        "paper_id": meth["paper_id"],
                        "description": meth["description"],
                        "context": meth["context"],
                        "novelty": meth["novelty"]
                    })
                
                # ===== FINDINGS TAB =====
                findings_data = [
                    {
                        "paper_id": "1",
                        "key_finding": "Deep Learning models achieved parity with radiologists in 85% of diagnostic tasks, with superior performance in fracture detection (AUC 0.94 vs 0.89) and lung nodule classification (AUC 0.92 vs 0.87).",
                        "limitations": "Most studies lacked external validation sets and diverse demographic representation. Limited data on rare conditions and pediatric populations."
                    },
                    {
                        "paper_id": "2",
                        "key_finding": "Key barriers to AI adoption: lack of technical expertise (78%), integration challenges (65%), and cost concerns (61%). Successful implementations had dedicated AI champions and phased rollout strategies.",
                        "limitations": "Survey response bias toward early adopters. Limited longitudinal data on sustained AI usage and clinical impact."
                    },
                    {
                        "paper_id": "3",
                        "key_finding": "Neural network reduced average radiology report turnaround time by 35% and improved diagnostic accuracy for fractures by 12%. Radiologist satisfaction increased after 6-month adaptation period.",
                        "limitations": "Single-site study limits generalizability. Implementation costs and resource requirements may not be feasible for smaller facilities."
                    },
                    {
                        "paper_id": "4",
                        "key_finding": "Ensemble ML models outperformed single algorithms across all prediction tasks. Best performance: gradient boosting for readmission (AUC 0.88), neural networks for mortality (AUC 0.91).",
                        "limitations": "High heterogeneity in study quality and outcome definitions. Limited reporting of model calibration and clinical utility metrics."
                    },
                    {
                        "paper_id": "5",
                        "key_finding": "Identified 7 core ethical principles for AI in diagnosis: transparency, accountability, fairness, privacy, safety, human oversight, and continuous monitoring. Proposes 3-tier governance framework.",
                        "limitations": "Framework requires validation in real-world settings. Limited guidance on resolving conflicts between competing ethical principles."
                    }
                ]
                
                for finding in findings_data:
                    db.execute(text("""
                        INSERT INTO findings (
                            user_id, project_id, paper_id,
                            key_finding, limitations
                        ) VALUES (
                            :user_id, :project_id, :paper_id,
                            :key_finding, :limitations
                        ) ON CONFLICT (user_id, project_id, paper_id) DO UPDATE
                        SET key_finding = EXCLUDED.key_finding,
                            limitations = EXCLUDED.limitations
                    """), {
                        "user_id": str(user_uuid),
                        "project_id": project_id,
                        "paper_id": finding["paper_id"],
                        "key_finding": finding["key_finding"],
                        "limitations": finding["limitations"]
                    })
                
                # ===== RESEARCH GAPS TAB =====
                research_gaps = [
                    {
                        "description": "Lack of diverse, representative datasets for AI training",
                        "priority": "High",
                        "notes": "Most studies use datasets from academic medical centers in developed countries. Need for datasets representing diverse demographics, healthcare settings, and geographic regions."
                    },
                    {
                        "description": "Limited long-term clinical outcome data",
                        "priority": "High",
                        "notes": "Most studies report technical performance metrics but lack data on patient outcomes, cost-effectiveness, and sustained clinical impact over time."
                    },
                    {
                        "description": "Insufficient research on AI implementation strategies",
                        "priority": "Medium",
                        "notes": "Gap between proof-of-concept studies and real-world deployment. Need for implementation science research on change management, training, and workflow integration."
                    },
                    {
                        "description": "Unclear regulatory frameworks for AI medical devices",
                        "priority": "Medium",
                        "notes": "Regulatory pathways vary across jurisdictions. Need for harmonized standards and guidelines for AI validation, approval, and post-market surveillance."
                    }
                ]
                
                for gap in research_gaps:
                    db.execute(text("""
                        INSERT INTO research_gaps (
                            id, user_id, project_id, description, priority, notes
                        ) VALUES (
                            gen_random_uuid(), :user_id, :project_id, :description, :priority, :notes
                        ) ON CONFLICT DO NOTHING
                    """), {
                        "user_id": str(user_uuid),
                        "project_id": project_id,
                        "description": gap["description"],
                        "priority": gap["priority"],
                        "notes": gap["notes"]
                    })
                
                # ===== COMPARISON TAB =====
                # Set up comparison configuration
                db.execute(text("""
                    INSERT INTO comparison_configs (
                        user_id, project_id, selected_paper_ids,
                        insights_similarities, insights_differences
                    ) VALUES (
                        :user_id, :project_id, :paper_ids,
                        :similarities, :differences
                    ) ON CONFLICT (user_id, project_id) DO UPDATE
                    SET selected_paper_ids = EXCLUDED.selected_paper_ids,
                        insights_similarities = EXCLUDED.insights_similarities,
                        insights_differences = EXCLUDED.insights_differences
                """), {
                    "user_id": str(user_uuid),
                    "project_id": project_id,
                    "paper_ids": [1, 2, 3, 4],
                    "similarities": "All studies focus on AI in healthcare with emphasis on clinical validation. Common themes: need for diverse datasets, importance of clinician involvement, and regulatory challenges.",
                    "differences": "Methodological diversity: systematic reviews (Papers 1,4,5) vs. empirical studies (Papers 2,3). Geographic focus varies from single-site (Paper 3) to international (Paper 2). Outcome measures range from technical performance to implementation success."
                })
                
                # Add comparison attributes for key papers
                comparison_attributes = [
                    {"paper_id": 1, "attr": "sample_size", "value": "150 studies"},
                    {"paper_id": 1, "attr": "study_design", "value": "Systematic Review"},
                    {"paper_id": 1, "attr": "key_metric", "value": "AUC 0.94"},
                    {"paper_id": 2, "attr": "sample_size", "value": "500 clinics"},
                    {"paper_id": 2, "attr": "study_design", "value": "Cross-sectional Survey"},
                    {"paper_id": 2, "attr": "key_metric", "value": "78% cite expertise gap"},
                    {"paper_id": 3, "attr": "sample_size", "value": "1 hospital (600 beds)"},
                    {"paper_id": 3, "attr": "study_design", "value": "Longitudinal Case Study"},
                    {"paper_id": 3, "attr": "key_metric", "value": "35% time reduction"},
                    {"paper_id": 4, "attr": "sample_size", "value": "85 ML studies"},
                    {"paper_id": 4, "attr": "study_design", "value": "Meta-Analysis"},
                    {"paper_id": 4, "attr": "key_metric", "value": "AUC 0.88-0.91"},
                ]
                
                for attr in comparison_attributes:
                    db.execute(text("""
                        INSERT INTO comparison_attributes (
                            user_id, project_id, paper_id, attribute_name, attribute_value
                        ) VALUES (
                            :user_id, :project_id, :paper_id, :attr_name, :attr_value
                        ) ON CONFLICT (user_id, project_id, paper_id, attribute_name) DO UPDATE
                        SET attribute_value = EXCLUDED.attribute_value
                    """), {
                        "user_id": str(user_uuid),
                        "project_id": project_id,
                        "paper_id": attr["paper_id"],
                        "attr_name": attr["attr"],
                        "attr_value": attr["value"]
                    })
                
                # ===== SYNTHESIS TAB =====
                # Create synthesis table structure
                import json
                synthesis_columns = [
                    {"id": "col1", "title": "Theme 1: Clinical Performance"},
                    {"id": "col2", "title": "Theme 2: Implementation Challenges"},
                    {"id": "col3", "title": "Theme 3: Ethical & Regulatory"}
                ]
                
                synthesis_rows = [
                    {"id": "row1", "label": "Deep Learning Review (Paper 1)"},
                    {"id": "row2", "label": "AI Adoption Survey (Paper 2)"},
                    {"id": "row3", "label": "Neural Networks Case (Paper 3)"},
                    {"id": "row4", "label": "ML Predictive Analytics (Paper 4)"},
                    {"id": "row5", "label": "Ethical Considerations (Paper 5)"}
                ]
                
                db.execute(text("""
                    INSERT INTO synthesis_configs (
                        user_id, project_id, columns, rows
                    ) VALUES (
                        :user_id, :project_id, :columns, :rows
                    ) ON CONFLICT (user_id, project_id) DO UPDATE
                    SET columns = EXCLUDED.columns, rows = EXCLUDED.rows
                """), {
                    "user_id": str(user_uuid),
                    "project_id": project_id,
                    "columns": json.dumps(synthesis_columns),
                    "rows": json.dumps(synthesis_rows)
                })
                
                # Populate synthesis cells with example content
                synthesis_cells = [
                    {"row": "row1", "col": "col1", "value": "DL models achieve parity with radiologists in 85% of tasks. Superior in fracture detection (AUC 0.94)."},
                    {"row": "row1", "col": "col2", "value": "Requires large labeled datasets and computational resources. Integration with PACS systems needed."},
                    {"row": "row1", "col": "col3", "value": "Lacks diverse demographic representation. Need for external validation and bias assessment."},
                    {"row": "row2", "col": "col1", "value": "Not directly measured - focuses on adoption factors rather than clinical outcomes."},
                    {"row": "row2", "col": "col2", "value": "Key barriers: 78% lack expertise, 65% integration issues, 61% cost concerns. Success requires AI champions."},
                    {"row": "row2", "col": "col3", "value": "Regulatory uncertainty cited as adoption barrier. Need for clear governance frameworks."},
                    {"row": "row3", "col": "col1", "value": "12% improvement in fracture detection accuracy. 35% reduction in report turnaround time."},
                    {"row": "row3", "col": "col2", "value": "18-month implementation with 6-month radiologist adaptation period. Workflow redesign required."},
                    {"row": "row3", "col": "col3", "value": "Radiologist oversight maintained. Continuous monitoring protocols established."},
                    {"row": "row4", "col": "col1", "value": "Ensemble models best: gradient boosting for readmission (AUC 0.88), neural nets for mortality (AUC 0.91)."},
                    {"row": "row4", "col": "col2", "value": "High heterogeneity in study quality. Limited reporting of implementation details."},
                    {"row": "row4", "col": "col3", "value": "Need for standardized validation protocols and fairness metrics across studies."},
                    {"row": "row5", "col": "col1", "value": "Proposes safety and continuous monitoring as core principles for clinical AI."},
                    {"row": "row5", "col": "col2", "value": "Framework requires real-world validation. Implementation guidance needed."},
                    {"row": "row5", "col": "col3", "value": "7 core principles identified: transparency, accountability, fairness, privacy, safety, oversight, monitoring."}
                ]
                
                for cell in synthesis_cells:
                    db.execute(text("""
                        INSERT INTO synthesis_cells (
                            user_id, project_id, row_id, column_id, value
                        ) VALUES (
                            :user_id, :project_id, :row_id, :col_id, :value
                        ) ON CONFLICT (user_id, project_id, row_id, column_id) DO UPDATE
                        SET value = EXCLUDED.value
                    """), {
                        "user_id": str(user_uuid),
                        "project_id": project_id,
                        "row_id": cell["row"],
                        "col_id": cell["col"],
                        "value": cell["value"]
                    })
                
                # ===== ANALYSIS TAB =====
                # Set up analysis preferences
                db.execute(text("""
                    INSERT INTO analysis_configs (
                        user_id, project_id, chart_preferences, custom_metrics
                    ) VALUES (
                        :user_id, :project_id, :preferences, :metrics
                    ) ON CONFLICT (user_id, project_id) DO UPDATE
                    SET chart_preferences = EXCLUDED.chart_preferences,
                        custom_metrics = EXCLUDED.custom_metrics
                """), {
                    "user_id": str(user_uuid),
                    "project_id": project_id,
                    "preferences": json.dumps({
                        "methodology_chart_type": "pie",
                        "timeline_chart_type": "bar",
                        "show_quality_cards": True,
                        "color_scheme": "default"
                    }),
                    "metrics": json.dumps([])
                })
                
                print("✅ Successfully seeded all literature review tabs with template data")
                
            except Exception as ex:
                print(f"⚠️ Warning: Could not seed some tab data: {ex}")
                import traceback
                traceback.print_exc()
                # Continue even if some tab seeding fails
            
            db.commit()
            return True

        except Exception as e:
            print(f"❌ Error seeding project: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise
