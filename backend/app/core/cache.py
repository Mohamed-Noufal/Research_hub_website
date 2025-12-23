import json
import logging
from typing import Optional, Any, Callable
from functools import wraps
import hashlib
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages Redis caching for agent tools and expensive operations.
    """
    _instance = None
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[redis.Redis] = None
        self._connect()
        
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
        
    def _connect(self):
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"✅ Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis = None

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis: return None
        try:
            val = await self.redis.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.redis: return
        try:
            await self.redis.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

def cached_tool(ttl: int = 3600):
    """
    Decorator to cache tool results based on arguments.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get cache manager
            try:
                manager = CacheManager.get_instance()
                if not manager.redis:
                    return await func(*args, **kwargs)
            except:
                return await func(*args, **kwargs)

            # Create cache key from function name and args
            # We strictly sort kwargs to ensure stability
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            
            key_str = "|".join(key_parts)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_key = f"tool_cache:{func.__name__}:{key_hash}"
            
            # Check cache
            cached_result = await manager.get(cache_key)
            if cached_result:
                logger.info(f"⚡ Cache hit for {func.__name__}")
                return cached_result
            
            # Execute
            result = await func(*args, **kwargs)
            
            # Store
            await manager.set(cache_key, result, ttl)
            return result
            
        return wrapper
    return decorator
