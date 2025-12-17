"""
Admin Dashboard API Endpoints
Provides comprehensive system statistics and health monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.database import get_db
from app.models.paper import Paper
from app.models.user_models import LocalUser, UserSavedPaper

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def get_admin_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive admin dashboard with all system statistics
    
    Returns:
        - Database statistics (total counts)
        - Embedding status (processed vs unprocessed)
        - Recent activity (last 24 hours)
        - Data quality metrics
        - Category and source distribution
    """
    
    # ==================== DATABASE STATISTICS ====================
    total_papers = db.query(Paper).count()
    total_users = db.query(LocalUser).count()
    total_saved_papers = db.query(UserSavedPaper).count()
    
    # Papers with embeddings
    papers_with_embeddings = db.query(Paper).filter(
        Paper.embedding.isnot(None),
        Paper.is_processed == True
    ).count()
    
    # Papers without embeddings (need processing)
    papers_without_embeddings = db.query(Paper).filter(
        and_(
            Paper.embedding.is_(None),
            Paper.is_processed == False
        )
    ).count()
    
    # Papers being processed (have embedding but not marked as processed)
    papers_being_processed = db.query(Paper).filter(
        and_(
            Paper.embedding.isnot(None),
            Paper.is_processed == False
        )
    ).count()
    
    # ==================== RECENT ACTIVITY (Last 24 hours) ====================
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    papers_added_today = db.query(Paper).filter(
        Paper.date_added >= yesterday
    ).count()
    
    papers_updated_today = db.query(Paper).filter(
        Paper.last_updated >= yesterday
    ).count()
    
    # ==================== DATA QUALITY METRICS ====================
    papers_with_doi = db.query(Paper).filter(Paper.doi.isnot(None)).count()
    papers_with_pdf = db.query(Paper).filter(Paper.pdf_url.isnot(None)).count()
    papers_with_abstract = db.query(Paper).filter(
        and_(
            Paper.abstract.isnot(None),
            Paper.abstract != ''
        )
    ).count()
    papers_with_venue = db.query(Paper).filter(Paper.venue.isnot(None)).count()
    
    # ==================== CATEGORY BREAKDOWN ====================
    category_stats = db.query(
        Paper.category,
        func.count(Paper.id).label('count')
    ).filter(
        Paper.category.isnot(None)
    ).group_by(Paper.category).all()
    
    category_distribution = {
        cat: count for cat, count in category_stats
    }
    
    # Papers without category
    papers_without_category = db.query(Paper).filter(
        and_(
            Paper.category.is_(None),
            Paper.category == ''
        )
    ).count()
    
    # ==================== SOURCE DISTRIBUTION ====================
    source_stats = db.query(
        Paper.source,
        func.count(Paper.id).label('count')
    ).filter(
        Paper.source.isnot(None)
    ).group_by(Paper.source).all()
    
    source_distribution = {
        source: count for source, count in source_stats
    }
    
    # ==================== EMBEDDING PROGRESS ====================
    embedding_progress_percentage = (
        (papers_with_embeddings / total_papers * 100) if total_papers > 0 else 0
    )
    
    # ==================== TOP SAVED PAPERS ====================
    top_saved_papers = db.query(
        Paper.title,
        func.count(UserSavedPaper.id).label('save_count')
    ).join(
        UserSavedPaper, Paper.id == UserSavedPaper.paper_id
    ).group_by(
        Paper.id, Paper.title
    ).order_by(
        desc('save_count')
    ).limit(10).all()
    
    top_saved_list = [
        {"title": title, "saves": count}
        for title, count in top_saved_papers
    ]
    
    # ==================== RECENT PAPERS ====================
    recent_papers = db.query(Paper).order_by(
        desc(Paper.date_added)
    ).limit(10).all()
    
    recent_papers_list = [
        {
            "id": p.id,
            "title": p.title,
            "source": p.source,
            "category": p.category,
            "has_embedding": p.embedding is not None,
            "is_processed": p.is_processed,
            "date_added": p.date_added.isoformat() if p.date_added else None
        }
        for p in recent_papers
    ]
    
    # ==================== COMPILE DASHBOARD ====================
    dashboard = {
        "timestamp": datetime.utcnow().isoformat(),
        
        "database_stats": {
            "total_papers": total_papers,
            "total_users": total_users,
            "total_saved_papers": total_saved_papers,
        },
        
        "embedding_status": {
            "papers_with_embeddings": papers_with_embeddings,
            "papers_without_embeddings": papers_without_embeddings,
            "papers_being_processed": papers_being_processed,
            "embedding_progress_percentage": round(embedding_progress_percentage, 2),
            "status": "healthy" if papers_without_embeddings < 1000 else "needs_attention"
        },
        
        "recent_activity": {
            "papers_added_last_24h": papers_added_today,
            "papers_updated_last_24h": papers_updated_today,
        },
        
        "data_quality": {
            "papers_with_doi": papers_with_doi,
            "papers_with_pdf": papers_with_pdf,
            "papers_with_abstract": papers_with_abstract,
            "papers_with_venue": papers_with_venue,
            "doi_coverage_percentage": round((papers_with_doi / total_papers * 100) if total_papers > 0 else 0, 2),
            "pdf_coverage_percentage": round((papers_with_pdf / total_papers * 100) if total_papers > 0 else 0, 2),
            "abstract_coverage_percentage": round((papers_with_abstract / total_papers * 100) if total_papers > 0 else 0, 2),
        },
        
        "category_distribution": category_distribution,
        "papers_without_category": papers_without_category,
        
        "source_distribution": source_distribution,
        
        "top_saved_papers": top_saved_list,
        
        "recent_papers": recent_papers_list,
        
        "health_status": {
            "overall": "healthy",
            "warnings": []
        }
    }
    
    # Add warnings if needed
    if papers_without_embeddings > 1000:
        dashboard["health_status"]["warnings"].append(
            f"{papers_without_embeddings} papers need embedding generation"
        )
    
    if papers_without_category > total_papers * 0.1:
        dashboard["health_status"]["warnings"].append(
            f"{papers_without_category} papers missing category assignment"
        )
    
    if papers_with_doi < total_papers * 0.5:
        dashboard["health_status"]["warnings"].append(
            f"Only {round(papers_with_doi / total_papers * 100, 1)}% of papers have DOIs"
        )
    
    if dashboard["health_status"]["warnings"]:
        dashboard["health_status"]["overall"] = "needs_attention"
    
    return dashboard


@router.get("/embedding-queue")
async def get_embedding_queue(
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get papers that need embedding generation
    
    Args:
        limit: Maximum number of papers to return
    
    Returns:
        List of papers waiting for embedding generation
    """
    
    papers_needing_embeddings = db.query(Paper).filter(
        Paper.embedding.is_(None),
        Paper.is_processed == False
    ).order_by(desc(Paper.date_added)).limit(limit).all()
    
    queue = [
        {
            "id": p.id,
            "title": p.title,
            "source": p.source,
            "category": p.category,
            "date_added": p.date_added.isoformat() if p.date_added else None,
            "has_abstract": bool(p.abstract),
        }
        for p in papers_needing_embeddings
    ]
    
    return {
        "total_in_queue": len(queue),
        "papers": queue
    }


@router.post("/trigger-embedding-generation")
async def trigger_embedding_generation(
    max_papers: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manually trigger embedding generation for papers in queue
    
    Args:
        max_papers: Maximum number of papers to process
    
    Returns:
        Status of embedding generation task
    """
    
    from app.services.enhanced_vector_service import EnhancedVectorService
    
    vector_service = EnhancedVectorService()
    
    result = await vector_service.generate_embeddings_for_papers(
        db=db,
        batch_size=50,
        max_papers=max_papers,
        force_regenerate=False
    )
    
    return result


@router.get("/data-quality-report")
async def get_data_quality_report(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed data quality report showing papers with missing fields
    
    Returns:
        Comprehensive data quality metrics and lists of problematic papers
    """
    
    # Papers missing critical fields
    papers_missing_doi = db.query(Paper).filter(
        Paper.doi.is_(None)
    ).limit(20).all()
    
    papers_missing_abstract = db.query(Paper).filter(
        and_(
            Paper.abstract.is_(None),
            Paper.abstract == ''
        )
    ).limit(20).all()
    
    papers_missing_pdf = db.query(Paper).filter(
        Paper.pdf_url.is_(None)
    ).limit(20).all()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        
        "missing_doi": {
            "count": db.query(Paper).filter(Paper.doi.is_(None)).count(),
            "sample": [
                {
                    "id": p.id,
                    "title": p.title,
                    "source": p.source
                }
                for p in papers_missing_doi
            ]
        },
        
        "missing_abstract": {
            "count": db.query(Paper).filter(
                and_(Paper.abstract.is_(None), Paper.abstract == '')
            ).count(),
            "sample": [
                {
                    "id": p.id,
                    "title": p.title,
                    "source": p.source
                }
                for p in papers_missing_abstract
            ]
        },
        
        "missing_pdf": {
            "count": db.query(Paper).filter(Paper.pdf_url.is_(None)).count(),
            "sample": [
                {
                    "id": p.id,
                    "title": p.title,
                    "source": p.source
                }
                for p in papers_missing_pdf
            ]
        }
    }
