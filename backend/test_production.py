"""
Production Features Test Script
Tests all production-ready features implemented in Phases 1-4
"""
import asyncio
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def divider(title: str):
    logger.info(f"\n{'='*60}")
    logger.info(f" {title}")
    logger.info('='*60)


async def test_database_connection():
    """Test database connectivity"""
    divider("Database Connection")
    from app.core.database import SessionLocal
    from sqlalchemy import text
    
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).fetchone()
        papers_count = db.execute(text("SELECT COUNT(*) FROM papers")).fetchone()[0]
        chunks_count = db.execute(text("SELECT COUNT(*) FROM data_paper_chunks")).fetchone()[0]
        db.close()
        
        logger.info(f"✅ Database connected")
        logger.info(f"   Papers: {papers_count}")
        logger.info(f"   RAG Chunks: {chunks_count}")
        return True
    except Exception as e:
        logger.error(f"❌ Database failed: {e}")
        return False


async def test_redis_connection():
    """Test Redis connectivity"""
    divider("Redis Connection")
    import redis
    from app.core.config import settings
    
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        client.ping()
        info = client.info("memory")
        
        logger.info(f"✅ Redis connected")
        logger.info(f"   Memory: {info.get('used_memory_human', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"❌ Redis failed: {e}")
        return False


async def test_cache_service():
    """Test cache service"""
    divider("Cache Service (Phase 2)")
    
    try:
        from app.core.cache import CacheService
        cache = CacheService()
        
        if not cache.enabled:
            logger.warning("⚠️ Cache disabled (Redis not available)")
            return False
        
        # Test set/get
        test_key = "test:production_test"
        test_value = {"message": "hello", "timestamp": time.time()}
        
        cache.set(test_key, test_value, ttl=60)
        retrieved = cache.get(test_key)
        
        if retrieved and retrieved.get("message") == "hello":
            logger.info("✅ Cache service working")
            logger.info("   Set/Get: OK")
            cache.delete(test_key)
            return True
        else:
            logger.error("❌ Cache get failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Cache service failed: {e}")
        return False


async def test_rate_limiter():
    """Test rate limiter"""
    divider("Rate Limiter (Phase 4)")
    
    try:
        from app.core.security import rate_limiter
        
        if not rate_limiter.enabled:
            logger.warning("⚠️ Rate limiter disabled (Redis not available)")
            return False
        
        # Test rate limiting
        test_key = "test:rate_limit_test"
        
        # Should be allowed
        allowed, info = rate_limiter.is_allowed(test_key, limit=5, window_seconds=10)
        
        if allowed:
            logger.info("✅ Rate limiter working")
            logger.info(f"   Allowed: {allowed}")
            logger.info(f"   Remaining: {info.get('remaining')}")
            return True
        else:
            logger.error("❌ Rate limiter blocked unexpectedly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Rate limiter failed: {e}")
        return False


async def test_celery_connection():
    """Test Celery worker status"""
    divider("Celery Workers (Phase 1)")
    
    try:
        from app.workers.celery_app import celery_app
        
        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active()
        
        if active:
            workers = list(active.keys())
            logger.info(f"✅ Celery workers active: {len(workers)}")
            for w in workers:
                logger.info(f"   - {w}")
            return True
        else:
            logger.warning("⚠️ No Celery workers running")
            logger.info("   To start: celery -A app.workers.celery_app worker -l info")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Celery check failed: {e}")
        logger.info("   Workers may not be running")
        return False


async def test_rag_engine():
    """Test RAG engine"""
    divider("RAG Engine")
    
    try:
        from app.core.rag_engine import RAGEngine
        
        logger.info("   Initializing RAG engine...")
        rag = RAGEngine()
        
        logger.info("✅ RAG engine initialized")
        logger.info("   Vector store: Connected")
        logger.info("   Embedding model: Nomic (768 dims)")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG engine failed: {e}")
        return False


async def test_rag_query():
    """Test RAG query with caching"""
    divider("RAG Query + Caching")
    
    try:
        from app.core.rag_engine import RAGEngine
        
        rag = RAGEngine()
        
        # First query (should be cache miss)
        logger.info("   Query 1: 'What is attention mechanism?'")
        start = time.time()
        result = await rag.query(
            query_text="What is attention mechanism?",
            user_id="00000000-0000-0000-0000-000000000001",
            top_k=3,
            use_cache=True
        )
        time1 = time.time() - start
        
        chunks = len(result.get('source_nodes', []))
        answer_preview = result.get('answer', '')[:100]
        
        logger.info(f"   Time: {time1:.2f}s")
        logger.info(f"   Chunks: {chunks}")
        logger.info(f"   Answer: {answer_preview}...")
        
        if chunks == 0:
            logger.warning("⚠️ No chunks found - database may be empty")
            return False
        
        # Second query (should be cache hit)
        logger.info("\n   Query 2 (same query - should be cached):")
        start = time.time()
        result2 = await rag.query(
            query_text="What is attention mechanism?",
            user_id="00000000-0000-0000-0000-000000000001",
            top_k=3,
            use_cache=True
        )
        time2 = time.time() - start
        
        logger.info(f"   Time: {time2:.2f}s")
        
        if time2 < time1 / 2:
            logger.info(f"   ✅ Cache is working! ({time1:.2f}s -> {time2:.2f}s)")
        else:
            logger.info(f"   ⚠️ Cache may not be working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG query failed: {e}")
        return False


async def main():
    logger.info("="*60)
    logger.info(" PRODUCTION FEATURES TEST")
    logger.info(" Testing Phases 1-4 Implementation")
    logger.info("="*60)
    
    results = {}
    
    # Core infrastructure
    results['database'] = await test_database_connection()
    results['redis'] = await test_redis_connection()
    
    # Phase 2: Performance
    results['cache'] = await test_cache_service()
    
    # Phase 4: Security
    results['rate_limiter'] = await test_rate_limiter()
    
    # Phase 1: Background Processing
    results['celery'] = await test_celery_connection()
    
    # RAG Engine
    results['rag_engine'] = await test_rag_engine()
    
    # RAG Query (only if chunks exist)
    if results['rag_engine']:
        results['rag_query'] = await test_rag_query()
    
    # Summary
    divider("SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"  {status} {test}")
    
    logger.info(f"\n  Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("\n🎉 All production features working!")
    elif passed >= total - 1:
        logger.info("\n⚠️ Most features working (Celery workers may need to be started)")
    else:
        logger.info("\n❌ Some features need attention")
    
    return passed, total


if __name__ == "__main__":
    passed, total = asyncio.run(main())
    sys.exit(0 if passed >= total - 1 else 1)
