#!/usr/bin/env python3
"""
Comprehensive test file for the Research Paper Search API
Tests all functionality and shows results to identify issues
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def log_success(self, test_name: str, details: str = ""):
        self.passed += 1
        print(f"✅ {test_name}: {details}")

    def log_failure(self, test_name: str, error: str, details: str = ""):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
        if details:
            print(f"   Details: {details}")

    def summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} passed ({success_rate:.1f}%)")
        if self.errors:
            print(f"ERRORS FOUND: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")
        print(f"{'='*60}")

class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.results = TestResults()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_health(self):
        """Test basic health endpoint"""
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                self.results.log_success("Health Check", "API is responding")
                return True
            else:
                self.results.log_failure("Health Check", f"Status {response.status_code}")
                return False
        except Exception as e:
            self.results.log_failure("Health Check", str(e))
            return False

    async def test_categories(self):
        """Test category loading"""
        try:
            response = await self.client.get(f"{API_PREFIX}/papers/categories")
            if response.status_code == 200:
                data = response.json()
                categories = data.get("categories", {})
                total = data.get("total", 0)

                if total == 5 and len(categories) == 5:
                    self.results.log_success("Categories API", f"Loaded {total} categories")
                    print(f"   Categories: {list(categories.keys())}")
                    return categories
                else:
                    self.results.log_failure("Categories API", f"Expected 5 categories, got {total}")
                    return None
            else:
                self.results.log_failure("Categories API", f"Status {response.status_code}")
                return None
        except Exception as e:
            self.results.log_failure("Categories API", str(e))
            return None

    async def test_individual_sources(self, categories: Dict):
        """Test each source individually"""
        test_queries = {
            "ai_cs": "machine learning",
            "medicine_biology": "cancer treatment",
            "agriculture_animal": "crop yield",
            "humanities_social": "education policy",
            "economics_business": "economic growth"
        }

        source_results = {}

        for category_id, category_data in categories.items():
            sources = category_data["sources"]
            query = test_queries.get(category_id, "test query")

            print(f"\n🔍 Testing {category_id} sources: {sources}")

            for source in sources:
                try:
                    # Test individual source
                    params = {
                        "query": query,
                        "limit": 3,
                        "sources": source
                    }

                    response = await self.client.get(
                        f"{API_PREFIX}/papers/search",
                        params=params
                    )

                    if response.status_code == 200:
                        data = response.json()
                        papers = data.get("papers", [])
                        sources_used = data.get("sources_used", [])

                        if papers and source in sources_used:
                            self.results.log_success(f"{category_id}:{source}",
                                                   f"{len(papers)} papers from {source}")
                            source_results[f"{category_id}:{source}"] = len(papers)
                        else:
                            self.results.log_failure(f"{category_id}:{source}",
                                                   f"No papers from {source}")
                            source_results[f"{category_id}:{source}"] = 0
                    else:
                        self.results.log_failure(f"{category_id}:{source}",
                                               f"Status {response.status_code}")
                        source_results[f"{category_id}:{source}"] = -1

                except Exception as e:
                    self.results.log_failure(f"{category_id}:{source}", str(e))
                    source_results[f"{category_id}:{source}"] = -1

                await asyncio.sleep(0.5)  # Rate limiting

        return source_results

    async def test_category_search(self, categories: Dict):
        """Test category-based search"""
        category_results = {}

        test_cases = [
            ("ai_cs", "neural networks"),
            ("medicine_biology", "drug discovery"),
            ("agriculture_animal", "sustainable farming"),
            ("humanities_social", "social inequality"),
            ("economics_business", "market analysis")
        ]

        for category_id, query in test_cases:
            try:
                print(f"\n🎯 Testing category search: {category_id} -> '{query}'")

                response = await self.client.get(
                    f"{API_PREFIX}/papers/search/category/{category_id}",
                    params={"query": query, "limit": 5}
                )

                if response.status_code == 200:
                    data = response.json()
                    papers = data.get("papers", [])
                    sources_used = data.get("sources_used", [])
                    category_returned = data.get("category")

                    if papers and category_returned == category_id:
                        self.results.log_success(f"Category Search {category_id}",
                                               f"{len(papers)} papers from {len(sources_used)} sources")
                        category_results[category_id] = {
                            "papers": len(papers),
                            "sources": sources_used,
                            "success": True
                        }
                        print(f"   Sources used: {sources_used}")
                        print(f"   Sample paper: {papers[0]['title'][:50]}..." if papers else "No papers")
                    else:
                        self.results.log_failure(f"Category Search {category_id}",
                                               "No papers or wrong category returned")
                        category_results[category_id] = {"success": False}
                else:
                    error_text = response.text[:200] if response.text else f"Status {response.status_code}"
                    self.results.log_failure(f"Category Search {category_id}", error_text)
                    category_results[category_id] = {"success": False}

            except Exception as e:
                self.results.log_failure(f"Category Search {category_id}", str(e))
                category_results[category_id] = {"success": False}

            await asyncio.sleep(1)  # Rate limiting

        return category_results

    async def test_ai_search(self):
        """Test AI-powered search"""
        try:
            print("\n🤖 Testing AI search expansion")
            response = await self.client.get(
                f"{API_PREFIX}/papers/search/ai",
                params={"query": "climate change impact", "limit": 3}
            )

            if response.status_code == 200:
                data = response.json()
                papers = data.get("papers", [])
                ai_analysis = data.get("ai_analysis")

                if papers and ai_analysis:
                    expanded_queries = ai_analysis.get("generated_queries", [])
                    self.results.log_success("AI Search",
                                           f"{len(papers)} papers, {len(expanded_queries)} query variations")
                    print(f"   AI generated queries: {expanded_queries}")
                    return True
                else:
                    self.results.log_failure("AI Search", "No papers or AI analysis")
                    return False
            else:
                self.results.log_failure("AI Search", f"Status {response.status_code}")
                return False

        except Exception as e:
            self.results.log_failure("AI Search", str(e))
            return False

    async def test_parallel_search_simulation(self):
        """Test parallel search with fallbacks"""
        try:
            print("\n🔄 Testing parallel search with fallbacks")
            # Use a category that has multiple sources
            response = await self.client.get(
                f"{API_PREFIX}/papers/search/category/medicine_biology",
                params={"query": "COVID vaccine", "limit": 10}
            )

            if response.status_code == 200:
                data = response.json()
                papers = data.get("papers", [])
                sources_used = data.get("sources_used", [])
                debug_info = data.get("debug_info", {})

                if papers and len(sources_used) >= 2:
                    self.results.log_success("Parallel Search",
                                           f"{len(papers)} papers from {len(sources_used)} sources")
                    print(f"   Sources: {sources_used}")
                    if debug_info:
                        print(f"   Timing: {debug_info.get('total_time_ms', 'N/A')}ms")
                    return True
                else:
                    self.results.log_failure("Parallel Search", "Insufficient parallel results")
                    return False
            else:
                self.results.log_failure("Parallel Search", f"Status {response.status_code}")
                return False

        except Exception as e:
            self.results.log_failure("Parallel Search", str(e))
            return False

    async def run_all_tests(self):
        """Run all tests and show comprehensive results"""
        print("🚀 STARTING COMPREHENSIVE API TESTS")
        print("=" * 60)

        # Test 1: Health check
        print("\n🏥 Testing basic health...")
        health_ok = await self.test_health()

        if not health_ok:
            print("❌ API is not responding. Check if backend is running on localhost:8000")
            return

        # Test 2: Categories
        print("\n📂 Testing categories...")
        categories = await self.test_categories()

        if not categories:
            print("❌ Categories not loading. Check category service.")
            return

        # Test 3: Individual sources
        print("\n🔍 Testing individual sources...")
        source_results = await self.test_individual_sources(categories)

        # Test 4: Category search
        print("\n🎯 Testing category-based search...")
        category_results = await self.test_category_search(categories)

        # Test 5: AI search
        print("\n🤖 Testing AI search...")
        ai_results = await self.test_ai_search()

        # Test 6: Parallel search
        print("\n🔄 Testing parallel search...")
        parallel_results = await self.test_parallel_search_simulation()

        # Final summary
        self.results.summary()

        # Detailed analysis
        print("\n📊 DETAILED ANALYSIS:")
        print(f"Categories loaded: {len(categories) if categories else 0}/5")
        print(f"Sources tested: {len(source_results)}")
        print(f"Category searches: {sum(1 for r in category_results.values() if r.get('success'))}/{len(category_results)}")
        print(f"AI search: {'✅' if ai_results else '❌'}")
        print(f"Parallel search: {'✅' if parallel_results else '❌'}")

        # Show working sources
        working_sources = [k for k, v in source_results.items() if v > 0]
        failing_sources = [k for k, v in source_results.items() if v == 0 or v == -1]

        if working_sources:
            print(f"\n✅ Working sources ({len(working_sources)}):")
            for source in working_sources:
                count = source_results[source]
                print(f"   {source}: {count} papers")

        if failing_sources:
            print(f"\n❌ Failing sources ({len(failing_sources)}):")
            for source in failing_sources:
                status = "No papers" if source_results[source] == 0 else "Error"
                print(f"   {source}: {status}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if self.results.failed > 0:
            print("1. Check API keys in .env file for failing sources")
            print("2. Verify internet connection for external APIs")
            print("3. Check database connection for vector search")
            print("4. Review error logs for specific failure reasons")

        if len(working_sources) < 5:
            print("5. Some sources may have rate limits - try again later")

        print("6. Test frontend at http://localhost:5173")
        print("7. Check browser console for frontend errors")

async def main():
    """Main test function"""
    print("🧪 RESEARCH PAPER SEARCH - COMPREHENSIVE TEST SUITE")
    print("Testing all functionality to identify issues and solutions\n")

    async with APITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
