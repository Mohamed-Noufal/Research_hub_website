import redis
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

class CacheService:
    """Cache service with Redis or in-memory fallback"""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize cache service with optional Redis"""
        self.use_redis = bool(redis_url and redis_url.strip())
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

        if self.use_redis:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self.default_ttl = 3600  # 1 hour
            except Exception as e:
                print(f"Redis connection failed: {e}. Using in-memory cache.")
                self.use_redis = False

        if not self.use_redis:
            print("Using in-memory cache")
            self.default_ttl = 300  # 5 minutes for memory cache
    
    def _generate_cache_key(self, prefix: str, query: str, **kwargs) -> str:
        """Generate a unique cache key from query and parameters"""
        # Create a string from query and kwargs
        key_parts = [prefix, query]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        
        # Hash for consistent length
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_search_results(self, query: str, limit: int = 20, semantic_rerank: bool = True) -> Optional[dict]:
        """Get cached search results"""
        cache_key = self._generate_cache_key("search", query, limit=limit, semantic_rerank=semantic_rerank)

        if self.use_redis:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Redis cache get error: {str(e)}")
                return None
        else:
            # Check in-memory cache
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                # Check if expired
                if datetime.now() < entry['expires']:
                    return entry['data']

                # Remove expired entry
                del self.memory_cache[cache_key]

        return None
    
    async def set_search_results(
        self,
        query: str,
        results: dict,
        limit: int = 20,
        semantic_rerank: bool = True,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache search results"""
        cache_key = self._generate_cache_key("search", query, limit=limit, semantic_rerank=semantic_rerank)
        ttl = ttl or self.default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)

        if self.use_redis:
            try:
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(results)
                )
                return True
            except Exception as e:
                print(f"Redis cache set error: {str(e)}")
                return False
        else:
            # Store in memory cache
            self.memory_cache[cache_key] = {
                'data': results,
                'expires': expires
            }
            return True
    
    async def invalidate_search(self, query: str, limit: int = 20) -> bool:
        """Invalidate specific search cache"""
        try:
            cache_key = self._generate_cache_key("search", query, limit=limit)
            self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            print(f"Cache invalidate error: {str(e)}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache (use with caution)"""
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False
