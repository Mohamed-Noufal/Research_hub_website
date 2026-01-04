"""
Security Middleware and Utilities
Rate limiting, input validation, and security headers
"""
import time
import hashlib
import logging
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


# === Rate Limiter ===

class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm
    """
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self._client = None
        self.enabled = True
    
    @property
    def client(self):
        if self._client is None:
            try:
                self._client = redis.from_url(self.redis_url, decode_responses=True)
                self._client.ping()
            except Exception as e:
                logger.warning(f"Redis not available for rate limiting: {e}")
                self.enabled = False
                return None
        return self._client
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            (allowed: bool, info: dict with remaining, reset_at)
        """
        if not self.enabled or not self.client:
            return True, {"remaining": limit, "reset_at": 0}
        
        now = int(time.time())
        window_start = now - window_seconds
        
        # Redis key for this rate limit
        redis_key = f"ratelimit:{key}"
        
        try:
            pipe = self.client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current entries
            pipe.zcard(redis_key)
            
            # Add current request
            pipe.zadd(redis_key, {f"{now}:{hash(time.time())}": now})
            
            # Set expiry
            pipe.expire(redis_key, window_seconds)
            
            results = pipe.execute()
            current_count = results[1]
            
            allowed = current_count < limit
            remaining = max(0, limit - current_count - 1)
            reset_at = now + window_seconds
            
            return allowed, {
                "remaining": remaining,
                "reset_at": reset_at,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True, {"remaining": limit, "reset_at": 0}


# Global rate limiter instance
rate_limiter = RateLimiter()


# === Rate Limit Configurations ===

RATE_LIMITS = {
    # Endpoint pattern -> (limit, window_seconds)
    "default": (100, 60),           # 100 requests per minute
    "search": (30, 60),             # 30 searches per minute
    "agent": (20, 60),              # 20 AI queries per minute
    "upload": (10, 60),             # 10 uploads per minute
    "auth": (5, 60),                # 5 auth attempts per minute
}


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key from request"""
    # Use IP address + user ID if available
    client_ip = request.client.host if request.client else "unknown"
    user_id = request.headers.get("X-User-ID", "anonymous")
    
    return f"{client_ip}:{user_id}"


def get_endpoint_limit(path: str) -> tuple[int, int]:
    """Get rate limit for an endpoint"""
    if "/search" in path:
        return RATE_LIMITS["search"]
    elif "/agent" in path or "/chat" in path:
        return RATE_LIMITS["agent"]
    elif "/upload" in path:
        return RATE_LIMITS["upload"]
    elif "/auth" in path or "/login" in path:
        return RATE_LIMITS["auth"]
    else:
        return RATE_LIMITS["default"]


# === Rate Limit Middleware ===

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/api/v1/health", "/api/v1/metrics"]:
            return await call_next(request)
        
        # Get rate limit key and limits
        key = get_rate_limit_key(request)
        limit, window = get_endpoint_limit(request.url.path)
        
        # Check rate limit
        allowed, info = rate_limiter.is_allowed(
            key=f"{key}:{request.url.path}", 
            limit=limit, 
            window_seconds=window
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": info.get("reset_at", 60) - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get("reset_at", 0)),
                    "Retry-After": str(info.get("reset_at", 60) - int(time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(info.get("reset_at", 0))
        
        return response


# === Input Validation ===

import re
import html

def sanitize_string(value: str, max_length: int = 10000) -> str:
    """Sanitize a string input"""
    if not value:
        return ""
    
    # Truncate to max length
    value = value[:max_length]
    
    # Escape HTML entities
    value = html.escape(value)
    
    return value


def sanitize_query(query: str) -> str:
    """Sanitize a search/RAG query"""
    if not query:
        return ""
    
    # Max query length
    query = query[:2000]
    
    # Remove potential prompt injection patterns
    dangerous_patterns = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+prior",
        r"forget\s+everything",
        r"system\s*:\s*",
        r"<\|.*?\|>",  # Special tokens
    ]
    
    for pattern in dangerous_patterns:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE)
    
    return query.strip()


def validate_file_upload(filename: str, content_type: str, size_bytes: int) -> tuple[bool, str]:
    """Validate file upload"""
    # Check filename
    if not filename:
        return False, "Filename required"
    
    # Check extension
    allowed_extensions = [".pdf"]
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed: {allowed_extensions}"
    
    # Check content type
    allowed_types = ["application/pdf"]
    if content_type not in allowed_types:
        return False, f"Content type not allowed: {content_type}"
    
    # Check size (max 50MB)
    max_size = 50 * 1024 * 1024
    if size_bytes > max_size:
        return False, f"File too large. Max: {max_size / 1024 / 1024}MB"
    
    return True, "OK"


# === Security Headers Middleware ===

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # IMPORTANT: Do NOT set X-Frame-Options for PDF endpoints
        # This allows PDFs to be displayed in iframes
        if not request.url.path.startswith("/uploads/pdfs/"):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # Cache control for API responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
        
        return response


# === Decorator for rate limiting specific endpoints ===

def rate_limit(limit: int = 10, window: int = 60):
    """
    Decorator to apply rate limiting to a specific endpoint.
    
    Usage:
        @app.get("/expensive-operation")
        @rate_limit(limit=5, window=60)
        async def expensive_operation(request: Request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            key = get_rate_limit_key(request)
            allowed, info = rate_limiter.is_allowed(
                key=f"{key}:{func.__name__}",
                limit=limit,
                window_seconds=window
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": info.get("reset_at", 60) - int(time.time())
                    }
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
