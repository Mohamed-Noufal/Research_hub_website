"""
Celery Application Configuration
Background task processing for AI Research Hub
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "research_hub",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    
    # Worker settings
    worker_concurrency=4,  # Number of parallel workers
    worker_prefetch_multiplier=1,  # Don't prefetch too many tasks
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Retry settings
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Retry if worker dies
    
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
)

# Use default queue for all tasks (simpler setup)
# For production, you might want separate queues:
# celery_app.conf.task_routes = {
#     "app.workers.tasks.ingest_paper_task": {"queue": "ingestion"},
#     "app.workers.tasks.update_embeddings_task": {"queue": "embeddings"},
# }
