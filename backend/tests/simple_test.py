#!/usr/bin/env python3
"""
Simple test to check basic functionality
"""

import httpx
import asyncio

async def test_basic():
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=10.0) as client:
            # Test health
            print("Testing health endpoint...")
            response = await client.get("/health")
            print(f"Health: {response.status_code}")

            if response.status_code == 200:
                # Test categories
                print("Testing categories endpoint...")
                response = await client.get("/api/v1/papers/categories")
                print(f"Categories: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"Found {data.get('total', 0)} categories")

                    # Test one category search
                    print("Testing category search...")
                    response = await client.get("/api/v1/papers/search/category/ai_cs?query=machine+learning&limit=3")
                    print(f"Category search: {response.status_code}")

                    if response.status_code == 200:
                        data = response.json()
                        papers = data.get("papers", [])
                        print(f"Found {len(papers)} papers")
                        if papers:
                            print(f"Sample: {papers[0]['title'][:50]}...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic())
