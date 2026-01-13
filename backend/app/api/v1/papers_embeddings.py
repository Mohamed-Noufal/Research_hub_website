"""
Paper Embeddings Endpoints
- Generate embeddings
- Regenerate/Upgrade embeddings
- Embedding statistics
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.services.enhanced_vector_service import EnhancedVectorService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers/embeddings", tags=["embeddings"])

def get_enhanced_vector_service():
    return EnhancedVectorService()

@router.post("/generate")
async def generate_paper_embeddings(
    max_papers: int = Query(50, ge=1, le=1000, description="Maximum papers to convert"),
    batch_size: int = Query(10, ge=1, le=50, description="Batch size for processing"),
    force_regenerate: bool = Query(False, description="Regenerate existing embeddings"),
    db: Session = Depends(get_db),
    vector_service: EnhancedVectorService = Depends(get_enhanced_vector_service)
):
    """
    Generate enhanced embeddings for papers (Title + Authors + Abstract)
    """
    try:
        print(f"🔄 Starting embedding generation process...")
        
        result = await vector_service.generate_embeddings_for_papers(
            db=db,
            batch_size=batch_size,
            max_papers=max_papers,
            force_regenerate=force_regenerate
        )
        
        print(f"✅ Embedding generation completed: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}"
        )

@router.post("/regenerate")
async def regenerate_enhanced_embeddings(
    max_papers: int = Query(500, ge=1, le=5000, description="Maximum papers to upgrade"),
    batch_size: int = Query(25, ge=5, le=100, description="Batch size for processing"),
    db: Session = Depends(get_db),
    vector_service: EnhancedVectorService = Depends(get_enhanced_vector_service)
):
    """
    Upgrade existing papers to enhanced embeddings (Title + Authors + Abstract)
    """
    try:
        print(f"🔄 Starting embedding regeneration...")

        result = await vector_service.regenerate_enhanced_embeddings(
            db=db,
            batch_size=batch_size,
            max_papers=max_papers
        )

        print(f"✅ Embedding regeneration completed: {result}")

        return result

    except Exception as e:
        print(f"❌ Embedding regeneration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding regeneration failed: {str(e)}"
        )

@router.get("/stats")
async def get_embedding_statistics(db: Session = Depends(get_db)):
    """
    Get embedding statistics and version information
    """
    try:
        from app.models.paper import Paper
        from sqlalchemy import func

        # Get embedding statistics
        total_papers = db.query(func.count(Paper.id)).scalar()
        papers_with_embeddings = db.query(func.count(Paper.id)).filter(
            Paper.embedding.isnot(None)
        ).scalar()

        # Get version distribution
        version_stats = db.query(
            Paper.paper_metadata['embedding_version'].astext,
            func.count(Paper.id)
        ).filter(
            Paper.embedding.isnot(None)
        ).group_by(
            Paper.paper_metadata['embedding_version'].astext
        ).all()

        version_distribution = {version or 'legacy': count for version, count in version_stats}

        # Get processing status
        processed_papers = db.query(func.count(Paper.id)).filter(
            Paper.is_processed == True
        ).scalar()

        return {
            "total_papers": total_papers,
            "papers_with_embeddings": papers_with_embeddings,
            "embedding_coverage": f"{(papers_with_embeddings/total_papers*100):.1f}%" if total_papers > 0 else "0%",
            "processed_papers": processed_papers,
            "processing_coverage": f"{(processed_papers/total_papers*100):.1f}%" if total_papers > 0 else "0%",
            "embedding_versions": version_distribution,
            "recommended_version": "enhanced_v2",
            "enhanced_features": ["title", "authors", "abstract"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get embedding statistics: {str(e)}"
        )
