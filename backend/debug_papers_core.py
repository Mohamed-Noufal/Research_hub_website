import asyncio
from app.api.v1.papers_core import health_check, get_cache_service

async def test():
    print("Testing health_check...")
    try:
        cache_service = get_cache_service()
        result = await health_check(cache_service)
        print("Success:", result)
    except Exception as e:
        print("Failed:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
