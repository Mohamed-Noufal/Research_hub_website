"""
Prometheus Metrics
Exposes application metrics for monitoring and alerting
"""
from fastapi import APIRouter, Request, Response
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
)
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# === Metrics Definitions ===

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# RAG metrics
RAG_QUERIES = Counter(
    "rag_queries_total",
    "Total RAG queries",
    ["cache_hit", "user_scope"]
)

RAG_QUERY_LATENCY = Histogram(
    "rag_query_duration_seconds",
    "RAG query latency",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

RAG_CHUNKS_RETRIEVED = Histogram(
    "rag_chunks_retrieved",
    "Number of chunks retrieved per query",
    buckets=[1, 5, 10, 20, 50, 100]
)

# Paper ingestion metrics
PAPERS_INGESTED = Counter(
    "papers_ingested_total",
    "Total papers ingested",
    ["status"]  # success, failed
)

PAPER_INGESTION_LATENCY = Histogram(
    "paper_ingestion_duration_seconds",
    "Paper ingestion latency",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

PAPER_CHUNKS_CREATED = Histogram(
    "paper_chunks_created",
    "Number of chunks created per paper",
    buckets=[10, 50, 100, 200, 500, 1000]
)

# System metrics (gauges)
ACTIVE_CELERY_TASKS = Gauge(
    "celery_active_tasks",
    "Number of active Celery tasks"
)

QUEUED_CELERY_TASKS = Gauge(
    "celery_queued_tasks",
    "Number of queued Celery tasks"
)

TOTAL_PAPERS = Gauge(
    "total_papers",
    "Total number of papers in database"
)

TOTAL_RAG_CHUNKS = Gauge(
    "total_rag_chunks",
    "Total number of RAG chunks in database"
)

# App info
APP_INFO = Info(
    "app",
    "Application information"
)
APP_INFO.info({
    "name": "research-hub",
    "version": "1.0.0"
})


# === Metric Recording Functions ===

def record_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def record_rag_query(cache_hit: bool, user_scoped: bool, duration: float, chunks: int):
    """Record RAG query metrics"""
    RAG_QUERIES.labels(
        cache_hit="true" if cache_hit else "false",
        user_scope="true" if user_scoped else "false"
    ).inc()
    RAG_QUERY_LATENCY.observe(duration)
    RAG_CHUNKS_RETRIEVED.observe(chunks)


def record_paper_ingestion(success: bool, duration: float, chunks: int):
    """Record paper ingestion metrics"""
    PAPERS_INGESTED.labels(status="success" if success else "failed").inc()
    PAPER_INGESTION_LATENCY.observe(duration)
    if success:
        PAPER_CHUNKS_CREATED.observe(chunks)


def update_system_gauges(papers: int, chunks: int, active_tasks: int, queued_tasks: int):
    """Update system gauge metrics"""
    TOTAL_PAPERS.set(papers)
    TOTAL_RAG_CHUNKS.set(chunks)
    ACTIVE_CELERY_TASKS.set(active_tasks)
    QUEUED_CELERY_TASKS.set(queued_tasks)


# === Prometheus Endpoint ===

@router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# === Middleware for Request Metrics ===

class MetricsMiddleware:
    """Middleware to record request metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Get response status code
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start_time
            
            # Extract endpoint (simplified)
            path = scope.get("path", "/unknown")
            method = scope.get("method", "GET")
            
            # Skip metrics endpoint itself
            if path != "/api/v1/metrics":
                record_request(method, path, status_code, duration)
