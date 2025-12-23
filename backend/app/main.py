from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import init_db
from .api.v1 import papers, users, search_history, admin, folders, table_config, methodology, findings, comparison, synthesis, analysis, agent

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events"""
    # Startup
    print("🚀 Starting Research Paper Search API...")
    
    # Initialize Monitoring (Phoenix/OTel)
    from .core.monitoring import MonitoringManager
    MonitoringManager.get_instance()
    
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

# Mount static files for uploads
from fastapi.staticfiles import StaticFiles
import os

# Ensure uploads directory exists
os.makedirs("uploads/pdfs", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


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
app.include_router(
    papers.router,
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





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
