#!/usr/bin/env python3
"""
Test script for AI Query Analyzer
Run this to test the AI-powered query expansion functionality
"""

import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.ai_query_analyzer import AIQueryAnalyzer

async def test_ai_analyzer():
    """Test the AI query analyzer with sample queries"""

    print("🤖 AI Query Analyzer Test")
    print("=" * 50)

    # Initialize analyzer
    try:
        analyzer = AIQueryAnalyzer()
        print("✅ AI Analyzer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Analyzer: {e}")
        return

    # Test queries
    test_queries = [
        "detection unhealthy goat using deep learning",
        "machine learning for medical diagnosis",
        "computer vision in agriculture",
        "natural language processing for healthcare"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: '{query}'")
        print("-" * 40)

        try:
            # Analyze query
            result = await analyzer.analyze_and_expand_query(query)

            # Display results
            print(f"📝 Original Query: {result['original_query']}")
            print(f"🎯 Analysis: {result.get('analysis', 'N/A')}")
            print(f"🔢 Generated Queries: {len(result['search_queries'])}")
            print(f"⚙️ Method: {result['method']}")

            print("\n📋 Generated Search Terms:")
            for j, search_term in enumerate(result['search_queries'], 1):
                print(f"  {j}. {search_term}")

            if 'explanation' in result:
                print(f"\n💡 Explanation: {result['explanation']}")

        except Exception as e:
            print(f"❌ Error analyzing query: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 50)

    # Health check
    print("\n🏥 Health Check:")
    try:
        health = await analyzer.health_check()
        print(f"🤖 AI Service Health: {'✅ Healthy' if health else '❌ Unhealthy'}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("Starting AI Query Analyzer test...")
    print("Make sure your backend environment is set up and PostgreSQL is running!")
    print()

    try:
        asyncio.run(test_ai_analyzer())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)

    print("\n🎉 AI Query Analyzer test completed!")
