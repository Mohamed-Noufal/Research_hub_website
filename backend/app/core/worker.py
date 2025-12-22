"""
Redis-backed worker Configuration using ARQ
"""
from arq.connections import RedisSettings
import os

# Default Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def get_redis_settings():
    """
    Get Redis settings for ARQ
    """
    return RedisSettings.from_dsn(REDIS_URL)
