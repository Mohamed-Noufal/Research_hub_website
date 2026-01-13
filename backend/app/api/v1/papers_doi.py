"""
DOI Paper Import Endpoints
- Fetch paper by DOI
- Infer metadata
"""
import logging
import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.enhanced_vector_service import EnhancedVectorService
from app.api.v1.papers_core import paper_to_dict

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])

# === Models ===

class DOIRequest(BaseModel):
    doi: str = Field(..., min_length=5, max_length=200, description="Digital Object Identifier")
    category: Optional[str] = Field(None, description="Research category (optional, will be inferred if not provided)")

class DOIResponse(BaseModel):
    paper: dict
    status: str  # "created" or "already_exists"
    message: str
    already_in_library: bool = False
    source: Optional[str] = None  # Which API provided the data

# === Helpers ===

def _infer_category_from_metadata(paper_data: dict) -> str:
    """
    Infer research category from paper metadata
    Uses journal name, subject keywords, and venue to guess the category
    """
    # Get potential category indicators
    journal = (paper_data.get('journal') or paper_data.get('venue') or '').lower()
    subjects = paper_data.get('metadata', {}).get('subject', [])
    
    # Simple keyword-based inference
    if any(keyword in journal for keyword in ['nature', 'science', 'cell', 'lancet', 'jama', 'nejm', 'plos', 'bmc']):
        return 'medicine_biology'
    
    if any(keyword in journal for keyword in ['ieee', 'acm', 'computer', 'neural', 'machine learning', 'ai']):
        return 'ai_cs'
    
    if any(keyword in journal for keyword in ['physics', 'engineering', 'materials']):
        return 'engineering_physics'
    
    if any(keyword in journal for keyword in ['agriculture', 'animal', 'veterinary', 'crop']):
        return 'agriculture_animal'
    
    if any(keyword in journal for keyword in ['psychology', 'sociology', 'education', 'humanities']):
        return 'humanities_social'
    
    if any(keyword in journal for keyword in ['economics', 'business', 'finance', 'management']):
        return 'economics_business'
    
    # Check subjects if available
    if subjects:
        subjects_str = ' '.join(subjects).lower()
        if 'medicine' in subjects_str or 'biology' in subjects_str:
            return 'medicine_biology'
        if 'computer' in subjects_str or 'ai' in subjects_str:
            return 'ai_cs'
    
    # Default to general category
    return 'ai_cs'

# === Endpoints ===

@router.post("/fetch-by-doi")
async def fetch_paper_by_doi(
    request: DOIRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    🔍 **Fetch Paper by DOI** - Direct Paper Import
    """
    try:
        from app.services.doi_fetcher_service import DOIFetcherService
        from app.models.paper import Paper

        # Clean DOI (remove URL prefix if present)
        doi = request.doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
        
        # Validate DOI format (basic check)
        if not doi or "/" not in doi or not doi.startswith("10."):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid DOI format",
                    "message": f"DOI '{request.doi}' is not in valid format. DOIs should start with '10.' and contain a '/'",
                    "suggestions": [
                        "Check if the DOI is typed correctly",
                        "DOI format: 10.XXXX/YYYY",
                        "Example: 10.1038/nature12373"
                    ]
                }
            )

        logger.info(f"📥 Fetching paper by DOI: {doi}")

        # Check if paper already exists in database (deduplication)
        existing_paper = db.query(Paper).filter(Paper.doi == doi).first()
        
        if existing_paper:
            logger.info(f"✅ Paper already exists in database (ID: {existing_paper.id})")
            
            # TODO: Check if in user's library when auth is implemented
            already_in_library = False
            
            return {
                "paper": paper_to_dict(existing_paper),
                "status": "already_exists",
                "message": "Paper already in database",
                "already_in_library": already_in_library,
                "source": existing_paper.source
            }

        # Fetch from external sources
        logger.info(f"🔍 Fetching from external sources...")
        fetcher = DOIFetcherService()
        
        try:
            paper_data = await fetcher.fetch_paper_by_doi(doi)
        finally:
            await fetcher.close()

        if not paper_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DOI not found",
                    "message": f"Paper with DOI '{doi}' not found in any source",
                    "suggestions": [
                        "Verify the DOI is correct",
                        "Try searching by title instead",
                        "The paper may not be indexed in our sources (Crossref, Unpaywall, Semantic Scholar)"
                    ]
                }
            )

        logger.info(f"✅ Paper found from source: {paper_data.get('source')}")

        # Normalize data for database
        category = request.category or _infer_category_from_metadata(paper_data)
        
        # Convert authors to list of strings if needed
        authors_list = []
        if paper_data.get('authors'):
            for author in paper_data['authors']:
                if isinstance(author, dict):
                    name = author.get('name', '').strip()
                    if name: authors_list.append(name)
                else:
                    name = str(author).strip()
                    if name: authors_list.append(name)
        
        # Handle empty strings
        title = paper_data.get('title', '').strip() or 'Untitled'
        abstract = paper_data.get('abstract', '').strip() or None
        venue = (paper_data.get('journal') or paper_data.get('venue') or '').strip() or None

        # Create Paper model instance
        new_paper = Paper(
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors_list if authors_list else None,
            publication_date=paper_data.get('publication_date'),
            pdf_url=paper_data.get('pdf_url'),
            source=paper_data.get('source', 'unknown'),
            citation_count=paper_data.get('citation_count', 0),
            venue=venue,
            category=category,
            semantic_scholar_id=paper_data.get('semantic_scholar_id'),
            paper_metadata=paper_data.get('metadata', {}),
            is_processed=False,
            date_added=datetime.datetime.utcnow(),
            last_updated=datetime.datetime.utcnow()
        )

        # Save to database
        db.add(new_paper)
        db.commit()
        db.refresh(new_paper)

        logger.info(f"💾 Paper saved to database (ID: {new_paper.id})")

        # Schedule background embedding generation
        async def generate_embedding_background():
            try:
                logger.info(f"🔄 BACKGROUND: Generating embedding for paper {new_paper.id}")
                vector_service = EnhancedVectorService()
                await vector_service.generate_embeddings_for_papers(
                    db=db,
                    paper_ids=[str(new_paper.id)],
                    batch_size=1
                )
                logger.info(f"✅ BACKGROUND: Embedding generated for paper {new_paper.id}")
            except Exception as e:
                logger.error(f"❌ BACKGROUND: Embedding generation failed: {e}")

        background_tasks.add_task(generate_embedding_background)

        return {
            "paper": paper_to_dict(new_paper),
            "status": "created",
            "message": "Paper fetched and saved successfully",
            "already_in_library": False,
            "source": paper_data.get('source')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ DOI fetch failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch paper by DOI: {str(e)}"
        )
