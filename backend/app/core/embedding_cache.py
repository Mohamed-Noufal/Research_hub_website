"""
Embedding Cache - Redis-based caching for embeddings
Reduces API calls and latency for repeated text.
"""
from typing import List, Optional, Dict, Any
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Try to import redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed - caching disabled")


class EmbeddingCache:
    """
    Cache embeddings by text hash.
    
    Features:
    - Hash-based key generation (deterministic)
    - Configurable TTL (default 24 hours)
    - Fallback to in-memory cache if Redis unavailable
    - Batch get/set for efficiency
    
    Usage:
        cache = EmbeddingCache(redis_url="redis://localhost:6379")
        
        # Check cache first
        embedding = cache.get(text)
        if not embedding:
            embedding = embed_model.get_embedding(text)
            cache.set(text, embedding)
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl_seconds: int = 86400,  # 24 hours
        prefix: str = "emb:",
        max_memory_cache: int = 1000
    ):
        """
        Args:
            redis_url: Redis connection URL (None for memory-only)
            ttl_seconds: Cache TTL in seconds
            prefix: Key prefix for Redis
            max_memory_cache: Max items in memory fallback
        """
        self.ttl = ttl_seconds
        self.prefix = prefix
        self.redis_client = None
        self.memory_cache: Dict[str, List[float]] = {}
        self.max_memory = max_memory_cache
        
        # Try to connect to Redis
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=False  # Need bytes for embedding storage
                )
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - using memory cache")
                self.redis_client = None
    
    def _hash_text(self, text: str) -> str:
        """Generate deterministic hash for text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def _make_key(self, text: str) -> str:
        """Generate Redis key from text."""
        return f"{self.prefix}{self._hash_text(text)}"
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from cache.
        
        Returns:
            Embedding list or None if not cached
        """
        key = self._make_key(text)
        
        # Try Redis first
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Fallback to memory
        return self.memory_cache.get(key)
    
    def set(self, text: str, embedding: List[float]) -> bool:
        """
        Store embedding in cache.
        
        Returns:
            True if stored successfully
        """
        key = self._make_key(text)
        
        # Try Redis first
        if self.redis_client:
            try:
                data = json.dumps(embedding)
                self.redis_client.setex(key, self.ttl, data)
                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        # Fallback to memory
        if len(self.memory_cache) >= self.max_memory:
            # Simple LRU: remove oldest (first) item
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = embedding
        return True
    
    def get_many(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """
        Batch get embeddings.
        
        Returns:
            Dict mapping text to embedding (or None if not cached)
        """
        results = {}
        
        if self.redis_client:
            try:
                keys = [self._make_key(t) for t in texts]
                values = self.redis_client.mget(keys)
                for text, value in zip(texts, values):
                    results[text] = json.loads(value) if value else None
                return results
            except Exception as e:
                logger.warning(f"Redis mget failed: {e}")
        
        # Fallback to memory
        for text in texts:
            key = self._make_key(text)
            results[text] = self.memory_cache.get(key)
        
        return results
    
    def set_many(self, embeddings: Dict[str, List[float]]) -> int:
        """
        Batch set embeddings.
        
        Args:
            embeddings: Dict mapping text to embedding
            
        Returns:
            Number of items stored
        """
        stored = 0
        
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                for text, embedding in embeddings.items():
                    key = self._make_key(text)
                    data = json.dumps(embedding)
                    pipe.setex(key, self.ttl, data)
                pipe.execute()
                return len(embeddings)
            except Exception as e:
                logger.warning(f"Redis mset failed: {e}")
        
        # Fallback to memory
        for text, embedding in embeddings.items():
            if self.set(text, embedding):
                stored += 1
        
        return stored
    
    def clear(self) -> bool:
        """Clear all cached embeddings."""
        self.memory_cache.clear()
        
        if self.redis_client:
            try:
                # Only delete our prefixed keys
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor,
                        match=f"{self.prefix}*",
                        count=100
                    )
                    if keys:
                        self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
                return True
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")
                return False
        
        return True
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_items": len(self.memory_cache),
            "redis_connected": self.redis_client is not None
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info("memory")
                stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
            except:
                pass
        
        return stats


class CachedEmbedModel:
    """
    Wrapper around embedding model with caching.
    
    Usage:
        embed_model = NomicEmbeddings()
        cached = CachedEmbedModel(embed_model, cache)
        
        embedding = await cached.get_embedding(text)  # Uses cache automatically
    """
    
    def __init__(self, embed_model, cache: EmbeddingCache):
        self.model = embed_model
        self.cache = cache
        self.hits = 0
        self.misses = 0
    
    def get_text_embedding(self, text: str) -> List[float]:
        """Get embedding with caching (sync version)."""
        # Check cache
        cached = self.cache.get(text)
        if cached:
            self.hits += 1
            return cached
        
        # Generate embedding
        self.misses += 1
        embedding = self.model.get_text_embedding(text)
        
        # Store in cache
        self.cache.set(text, embedding)
        
        return embedding
    
    async def aget_text_embedding(self, text: str) -> List[float]:
        """Get embedding with caching (async version)."""
        # Check cache
        cached = self.cache.get(text)
        if cached:
            self.hits += 1
            return cached
        
        # Generate embedding (await if model is async)
        self.misses += 1
        if hasattr(self.model, 'aget_text_embedding'):
            embedding = await self.model.aget_text_embedding(text)
        else:
            embedding = self.model.get_text_embedding(text)
        
        # Store in cache
        self.cache.set(text, embedding)
        
        return embedding
    
    def get_query_embedding(self, text: str) -> List[float]:
        """Get query embedding (same as text for most models)."""
        return self.get_text_embedding(text)
    
    def cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
