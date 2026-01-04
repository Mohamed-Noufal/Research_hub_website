"""
Workers Package
Background task processing with Celery
"""
from app.workers.celery_app import celery_app
from app.workers.tasks import ingest_paper_task, update_embeddings_task, health_check

__all__ = [
    "celery_app",
    "ingest_paper_task", 
    "update_embeddings_task",
    "health_check"
]
