from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import init_db
from .api.v1 import (
    papers_core, papers_embeddings, papers_doi, papers_pdf, papers_manual,
    users, search_history, admin, folders, table_config, 
    methodology, findings, comparison, synthesis, analysis, agent, pdf
)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    # Startup
    print("🚀 Starting Research Paper Search API...")
    
    # Initialize Monitoring (Phoenix/OTel)
    from .core.monitoring import MonitoringManager
    MonitoringManager.get_instance()
    
    # ✅ Initialize Model Cache (load model ONCE at startup)
    print("📊 Initializing embedding model cache...")
    from .core.model_cache import ModelCache
    ModelCache.initialize()
    print("✅ Model cached successfully!")
    
    init_db()
    print("✅ Application ready!")

    yield

    # Shutdown (if needed in the future)
    print("🛑 Shutting down Research Paper Search API...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered research paper search platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middlewares
from .core.security import RateLimitMiddleware, SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# Mount static files for uploads - PDFs served via custom endpoint
import os

# Ensure uploads directory exists
os.makedirs("uploads/pdfs", exist_ok=True)

# Custom PDF endpoint without X-Frame-Options (allows iframe embedding)
from fastapi import HTTPException
from fastapi.responses import FileResponse

@app.get("/uploads/pdfs/{filename}")
async def serve_pdf(filename: str):
    """Serve PDF files without X-Frame-Options header to allow iframe embedding"""
    file_path = f"uploads/pdfs/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    # Return file without X-Frame-Options header
    response = FileResponse(
        file_path,
        media_type="application/pdf",
        headers={
            "Cache-Control": "public, max-age=3600",
            # X-Frame-Options deliberately NOT set - allows iframe embedding
        }
    )
    return response


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Research Paper Search API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/papers/health"
    }


# Health check
@app.get("/health")
async def health():
    """General health check"""
    return {"status": "healthy", "service": "api"}


# Include routers
# Include routers
# Refactored papers modules
app.include_router(
    papers_core.router,
    prefix=settings.API_V1_PREFIX,
    tags=["papers"]
)
app.include_router(
    papers_embeddings.router,
    prefix=settings.API_V1_PREFIX,
    tags=["embeddings"]
)
app.include_router(
    papers_doi.router,
    prefix=settings.API_V1_PREFIX,
    tags=["papers"]
)
app.include_router(
    papers_pdf.router,
    prefix=settings.API_V1_PREFIX,
    tags=["papers"]
)
app.include_router(
    papers_manual.router,
    prefix=settings.API_V1_PREFIX,
    tags=["papers"]
)

app.include_router(
    users.router,
    prefix=settings.API_V1_PREFIX,
    tags=["users"]
)

app.include_router(
    search_history.router,
    prefix=settings.API_V1_PREFIX,
    tags=["search-history"]
)

app.include_router(
    admin.router,
    prefix=settings.API_V1_PREFIX,
    tags=["admin"]
)

app.include_router(
    folders.router,
    prefix=settings.API_V1_PREFIX,
    tags=["folders"]
)

app.include_router(
    table_config.router,
    prefix=settings.API_V1_PREFIX,
    tags=["table-config"]
)

app.include_router(
    methodology.router,
    prefix=settings.API_V1_PREFIX,
    tags=["methodology"]
)

app.include_router(
    findings.router,
    prefix=settings.API_V1_PREFIX,
    tags=["findings"]
)

app.include_router(
    comparison.router,
    prefix=settings.API_V1_PREFIX,
    tags=["comparison"]
)

app.include_router(
    synthesis.router,
    prefix=settings.API_V1_PREFIX,
    tags=["synthesis"]
)

app.include_router(
    analysis.router,
    prefix=settings.API_V1_PREFIX,
    tags=["analysis"]
)

app.include_router(
    agent.router,
    prefix=settings.API_V1_PREFIX,
    tags=["agent"]
)

from .api.v1 import knowledge_base
app.include_router(
    knowledge_base.router,
    prefix=settings.API_V1_PREFIX,
    tags=["knowledge-base"]
)

# Async upload with background processing
from .api.v1 import upload_async
app.include_router(
    upload_async.router,
    prefix=settings.API_V1_PREFIX,
    tags=["async-upload"]
)

# PDF processing endpoints
app.include_router(
    pdf.router,
    prefix=settings.API_V1_PREFIX,
    tags=["pdf"]
)

# Health checks and monitoring
from .api.v1 import health, metrics
app.include_router(
    health.router,
    prefix=settings.API_V1_PREFIX,
    tags=["health"]
)
app.include_router(
    metrics.router,
    prefix=settings.API_V1_PREFIX,
    tags=["metrics"]
)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
