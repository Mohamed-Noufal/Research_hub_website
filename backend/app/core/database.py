from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
from app.core.config import settings

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # 20 connections in pool
    max_overflow=10,           # 10 extra if needed (total 30)
    pool_pre_ping=True,        # Check connection health before using
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=False,                # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database and create tables"""
    # Import all models here to ensure they are registered with SQLAlchemy
    from app.models.paper import Paper
    from app.models.user_models import (
        LocalUser, UserSavedPaper, UserNote,
        UserLiteratureReview, UserUpload, UserSearchHistory
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    print("📊 Tables created: papers, local_users, user_saved_papers, user_notes, user_literature_reviews, user_uploads, user_search_history")
