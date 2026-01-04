"""
Model Cache - Singleton Pattern for SentenceTransformer
Loads model ONCE at startup to avoid repeated loading (saves 12s per search)
"""
from sentence_transformers import SentenceTransformer
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ModelCache:
    """Singleton cache for embedding model to prevent repeated loading"""
    
    _instance: Optional['ModelCache'] = None
    _model: Optional[SentenceTransformer] = None
    _model_name: str = 'nomic-ai/nomic-embed-text-v1.5'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, model_name: str = None):
        """
        Initialize the model cache. Call this ONCE at application startup.
        
        Args:
            model_name: HuggingFace model name (default: nomic-ai/nomic-embed-text-v1.5)
        """
        if model_name:
            cls._model_name = model_name
            
        if cls._model is None:
            logger.info(f"🔄 Loading embedding model: {cls._model_name}")
            cls._model = SentenceTransformer(cls._model_name, trust_remote_code=True)
            logger.info(f"✅ Model cached successfully (dim: {cls._model.get_sentence_embedding_dimension()})")
        else:
            logger.info("✅ Model already cached, skipping load")
    
    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """
        Get the cached model instance.
        
        Returns:
            Cached SentenceTransformer model
            
        Raises:
            RuntimeError: If model not initialized
        """
        if cls._model is None:
            raise RuntimeError(
                "Model not initialized! Call ModelCache.initialize() at startup first."
            )
        return cls._model
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if model is initialized"""
        return cls._model is not None
    
    @classmethod
    def get_embedding_dim(cls) -> int:
        """Get embedding dimension"""
        if cls._model is None:
            raise RuntimeError("Model not initialized")
        return cls._model.get_sentence_embedding_dimension()
