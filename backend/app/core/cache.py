"""
Redis Cache Service
Provides caching for RAG queries, embeddings, and other expensive operations
"""
import json
import hashlib
import logging
from typing import Optional, Any
import redis
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service for performance optimization
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
            self.client = None
            self.enabled = False
        
        self._initialized = True
    
    @staticmethod
    def _generate_key(prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (default 1 hour)"""
        if not self.enabled:
            return False
        
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
        return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
            
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")
        return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled:
            return 0
            
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except Exception as e:
            logger.debug(f"Cache clear error: {e}")
        return 0
    
    # === Specialized Cache Methods ===
    
    def cache_rag_query(self, query: str, user_id: str, paper_ids: list = None, ttl: int = 1800) -> Optional[dict]:
        """
        Get cached RAG query result
        TTL: 30 minutes (queries may become stale after new papers added)
        """
        key = self._generate_key("rag_query", query=query, user_id=user_id, paper_ids=paper_ids)
        return self.get(key)
    
    def set_rag_query(self, query: str, user_id: str, result: dict, paper_ids: list = None, ttl: int = 1800):
        """Cache RAG query result"""
        key = self._generate_key("rag_query", query=query, user_id=user_id, paper_ids=paper_ids)
        return self.set(key, result, ttl)
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache for a user (when they add/remove papers)"""
        return self.clear_pattern(f"*:{user_id}:*")
    
    def cache_paper_summary(self, paper_id: int) -> Optional[dict]:
        """Get cached paper summary"""
        key = f"paper_summary:{paper_id}"
        return self.get(key)
    
    def set_paper_summary(self, paper_id: int, summary: dict, ttl: int = 86400):
        """Cache paper summary (24 hour TTL - summaries don't change)"""
        key = f"paper_summary:{paper_id}"
        return self.set(key, summary, ttl)


def cache_result(prefix: str, ttl: int = 3600):
    """
    Decorator to cache function results
    
    Usage:
        @cache_result("my_func", ttl=1800)
        async def my_expensive_function(arg1, arg2):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheService()
            
            if not cache.enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached = cache.get(key)
            if cached is not None:
                logger.debug(f"Cache HIT: {prefix}")
                return cached
            
            # Execute function
            logger.debug(f"Cache MISS: {prefix}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cached_tool(ttl: int = 3600, prefix: str = None):
    """
    Decorator to cache tool function results.
    Auto-generates prefix from function name if not provided.
    
    Usage:
        @cached_tool(ttl=3600)
        async def my_expensive_function(arg1, arg2):
            ...
    """
    def decorator(func):
        # Use function name as prefix if not provided
        actual_prefix = prefix or f"tool:{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheService()
            
            if not cache.enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key
            key = cache._generate_key(actual_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached = cache.get(key)
            if cached is not None:
                logger.debug(f"Cache HIT: {actual_prefix}")
                return cached
            
            # Execute function
            logger.debug(f"Cache MISS: {actual_prefix}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Singleton instance
cache_service = CacheService()
