"""
Rate Limiter - Per-user request limiting and tool timeouts
Protects against abuse and runaway LLM calls.
"""
from typing import Dict, Optional, Callable, Any
import time
import asyncio
import functools
import logging

logger = logging.getLogger(__name__)

# Try to import redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    
    Features:
    - Per-user limits (not global)
    - Redis-backed for distributed systems
    - Memory fallback for single instance
    - Configurable burst and refill rate
    
    Usage:
        limiter = RateLimiter(
            requests_per_minute=20,
            burst_size=5,
            redis_url="redis://localhost:6379"
        )
        
        if limiter.allow("user_123"):
            process_request()
        else:
            raise RateLimitExceeded()
    """
    
    def __init__(
        self,
        requests_per_minute: int = 20,
        burst_size: int = 5,
        redis_url: Optional[str] = None,
        prefix: str = "ratelimit:"
    ):
        """
        Args:
            requests_per_minute: Sustained limit
            burst_size: Max burst above limit
            redis_url: Redis connection (None for memory-only)
            prefix: Key prefix for Redis
        """
        self.rate = requests_per_minute / 60.0  # Requests per second
        self.burst = burst_size
        self.prefix = prefix
        self.redis_client = None
        
        # Memory-based storage: {user_id: (tokens, last_update_time)}
        self.memory_buckets: Dict[str, tuple] = {}
        
        # Try Redis connection
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Rate limiter connected to Redis")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - using memory")
                self.redis_client = None
    
    def _get_redis_key(self, user_id: str) -> str:
        return f"{self.prefix}{user_id}"
    
    def allow(self, user_id: str) -> bool:
        """
        Check if request is allowed for user.
        
        Uses token bucket algorithm:
        - Bucket refills at `rate` tokens per second
        - Max bucket size is `burst`
        - Each request consumes 1 token
        
        Returns:
            True if allowed, False if rate limited
        """
        now = time.time()
        
        if self.redis_client:
            return self._allow_redis(user_id, now)
        else:
            return self._allow_memory(user_id, now)
    
    def _allow_memory(self, user_id: str, now: float) -> bool:
        """Memory-based rate limiting."""
        if user_id in self.memory_buckets:
            tokens, last_update = self.memory_buckets[user_id]
        else:
            tokens, last_update = self.burst, now
        
        # Refill tokens based on elapsed time
        elapsed = now - last_update
        tokens = min(self.burst, tokens + elapsed * self.rate)
        
        if tokens >= 1:
            # Consume a token
            self.memory_buckets[user_id] = (tokens - 1, now)
            return True
        else:
            # Not enough tokens
            self.memory_buckets[user_id] = (tokens, now)
            return False
    
    def _allow_redis(self, user_id: str, now: float) -> bool:
        """Redis-based rate limiting (distributed)."""
        key = self._get_redis_key(user_id)
        
        try:
            # Atomic Lua script for token bucket
            script = """
            local key = KEYS[1]
            local rate = tonumber(ARGV[1])
            local burst = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            
            local data = redis.call('HMGET', key, 'tokens', 'last_update')
            local tokens = tonumber(data[1]) or burst
            local last_update = tonumber(data[2]) or now
            
            -- Refill tokens
            local elapsed = now - last_update
            tokens = math.min(burst, tokens + elapsed * rate)
            
            if tokens >= 1 then
                tokens = tokens - 1
                redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                redis.call('EXPIRE', key, 120)  -- Cleanup after 2 minutes idle
                return 1
            else
                redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
                redis.call('EXPIRE', key, 120)
                return 0
            end
            """
            
            result = self.redis_client.eval(
                script, 1, key, self.rate, self.burst, now
            )
            return result == 1
            
        except Exception as e:
            logger.warning(f"Redis rate limit failed: {e} - allowing request")
            return True  # Fail open
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining tokens for user."""
        now = time.time()
        
        if self.redis_client:
            try:
                key = self._get_redis_key(user_id)
                data = self.redis_client.hgetall(key)
                tokens = float(data.get('tokens', self.burst))
                last_update = float(data.get('last_update', now))
                elapsed = now - last_update
                tokens = min(self.burst, tokens + elapsed * self.rate)
                return int(tokens)
            except:
                return self.burst
        
        if user_id in self.memory_buckets:
            tokens, last_update = self.memory_buckets[user_id]
            elapsed = now - last_update
            tokens = min(self.burst, tokens + elapsed * self.rate)
            return int(tokens)
        
        return self.burst
    
    def reset(self, user_id: str):
        """Reset rate limit for user (admin use)."""
        if self.redis_client:
            try:
                self.redis_client.delete(self._get_redis_key(user_id))
            except:
                pass
        
        if user_id in self.memory_buckets:
            del self.memory_buckets[user_id]


class ToolTimeout:
    """
    Timeout wrapper for tool execution.
    
    Usage:
        @with_timeout(30)
        async def slow_tool():
            ...
            
        # Or manually:
        result = await ToolTimeout.run(slow_tool(), timeout=30)
    """
    
    @staticmethod
    async def run(coro, timeout: float = 30.0, default=None):
        """
        Run coroutine with timeout.
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds
            default: Value to return on timeout
            
        Returns:
            Coroutine result or default on timeout
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Tool execution timed out after {timeout}s")
            return default


def with_timeout(seconds: float = 30.0):
    """
    Decorator to add timeout to async functions.
    
    Usage:
        @with_timeout(30)
        async def slow_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.warning(f"{func.__name__} timed out after {seconds}s")
                return {"error": f"Timeout after {seconds}s"}
        return wrapper
    return decorator


def with_rate_limit(limiter: RateLimiter, user_id_arg: str = "user_id"):
    """
    Decorator to add rate limiting to functions.
    
    Usage:
        limiter = RateLimiter(requests_per_minute=20)
        
        @with_rate_limit(limiter, user_id_arg="user_id")
        async def api_endpoint(user_id: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user_id from kwargs
            user_id = kwargs.get(user_id_arg)
            if not user_id:
                # Try to find it in args based on function signature
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if user_id_arg in params:
                    idx = params.index(user_id_arg)
                    if idx < len(args):
                        user_id = args[idx]
            
            if not user_id:
                logger.warning("No user_id found for rate limiting")
                return await func(*args, **kwargs)
            
            if not limiter.allow(user_id):
                logger.warning(f"Rate limited: {user_id}")
                return {
                    "error": "Rate limit exceeded",
                    "retry_after": 60 / limiter.rate
                }
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global instances (can be configured at startup)
_default_limiter: Optional[RateLimiter] = None


def get_rate_limiter(
    requests_per_minute: int = 20,
    burst_size: int = 5,
    redis_url: Optional[str] = None
) -> RateLimiter:
    """Get or create default rate limiter."""
    global _default_limiter
    
    if _default_limiter is None:
        _default_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
            redis_url=redis_url
        )
    
    return _default_limiter
