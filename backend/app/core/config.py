from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Research Paper Search API"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    OPENALEX_EMAIL: Optional[str] = None  # For polite pool access
    GROQ_API_KEY: Optional[str] = None  # For AI query analysis
    CORE_API_KEY: Optional[str] = None  # For CORE repository access
    NCBI_API_KEY: Optional[str] = None  # For PubMed API access
    
    # Monitoring
    PHOENIX_COLLECTOR_URL: str = "http://localhost:4317"  # Phoenix OTLP endpoint

    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    
    # Search Settings
    DEFAULT_SEARCH_LIMIT: int = 50
    MAX_SEARCH_LIMIT: int = 100

    # Debug Settings
    DEBUG_MODE: bool = False
    DEBUG_LOG_LEVEL: str = "INFO"
    
    # AI Agent Configuration
    AGENT_MAX_ITERATIONS: int = 3  # Reduced from 10 for production (saves API costs)
    AGENT_TIMEOUT_SECONDS: int = 300
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    class Config:
        import os
        # Point to backend/.env
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
        case_sensitive = True


settings = Settings()
