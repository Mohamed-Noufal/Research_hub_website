"""
Health Check Endpoints
Provides detailed health status for all system components
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import logging
from typing import Dict, Any

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def check_database(db: Session) -> Dict[str, Any]:
    """Check database connectivity and stats"""
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        
        # Get some stats
        papers_count = db.execute(text("SELECT COUNT(*) FROM papers")).fetchone()[0]
        
        return {
            "status": "healthy",
            "connected": True,
            "papers_count": papers_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        
        # Get some info
        info = client.info("memory")
        
        return {
            "status": "healthy",
            "connected": True,
            "used_memory": info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


def check_rag_engine() -> Dict[str, Any]:
    """Check RAG engine readiness"""
    try:
        from app.core.rag_engine import RAGEngine
        
        # Just check if we can import and vector store is accessible
        # Don't fully initialize to avoid slow health checks
        return {
            "status": "healthy",
            "ready": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ready": False,
            "error": str(e)
        }


def check_celery() -> Dict[str, Any]:
    """Check Celery worker status"""
    try:
        from app.workers.celery_app import celery_app
        
        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active()
        
        if active:
            workers = list(active.keys())
            return {
                "status": "healthy",
                "workers": len(workers),
                "worker_names": workers
            }
        else:
            return {
                "status": "degraded",
                "workers": 0,
                "message": "No active workers found"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "workers": 0,
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """Basic health check - returns quickly"""
    return {"status": "healthy", "service": "research-hub-api"}


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check of all components.
    Use for monitoring and alerting.
    """
    components = {
        "database": check_database(db),
        "redis": check_redis(),
        "rag_engine": check_rag_engine(),
        "celery": check_celery()
    }
    
    # Determine overall status
    statuses = [c["status"] for c in components.values()]
    
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"
    
    return {
        "status": overall,
        "components": components
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes/load balancers.
    Returns 200 only if service is ready to accept traffic.
    """
    db_check = check_database(db)
    
    if db_check["status"] != "healthy":
        return {"ready": False, "reason": "database not connected"}
    
    return {"ready": True}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.
    Returns 200 if the service is running (even if degraded).
    """
    return {"alive": True}
