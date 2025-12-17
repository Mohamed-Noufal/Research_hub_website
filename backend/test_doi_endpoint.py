"""
Test script for DOI-based paper fetching endpoint

This script tests the new /papers/fetch-by-doi endpoint without requiring
the full backend server to be running.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.doi_fetcher_service import DOIFetcherService


async def test_doi_fetcher():
    """Test the DOI fetcher service"""
    print("=" * 60)
    print("Testing DOI Fetcher Service")
    print("=" * 60)
    
    fetcher = DOIFetcherService()
    
    # Test cases
    test_dois = [
        "10.1038/nature12373",  # Nature paper
        "10.1109/CVPR.2016.90",  # IEEE paper
        "10.1371/journal.pone.0123456",  # PLOS ONE paper (might not exist)
    ]
    
    for doi in test_dois:
        print(f"\n📥 Testing DOI: {doi}")
        print("-" * 60)
        
        try:
            paper = await fetcher.fetch_paper_by_doi(doi)
            
            if paper:
                print(f"✅ SUCCESS!")
                print(f"   Title: {paper.get('title', 'N/A')[:80]}...")
                print(f"   Source: {paper.get('source', 'N/A')}")
                print(f"   Authors: {len(paper.get('authors', []))} authors")
                print(f"   PDF URL: {'Yes' if paper.get('pdf_url') else 'No'}")
                print(f"   Citation Count: {paper.get('citation_count', 0)}")
                print(f"   Journal: {paper.get('journal', 'N/A')}")
            else:
                print(f"❌ Paper not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await fetcher.close()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


async def test_category_inference():
    """Test category inference logic"""
    print("\n" + "=" * 60)
    print("Testing Category Inference")
    print("=" * 60)
    
    # Import the inference function
    from app.api.v1.papers import _infer_category_from_metadata
    
    test_cases = [
        {
            "journal": "Nature",
            "expected": "medicine_biology"
        },
        {
            "journal": "IEEE Transactions on Neural Networks",
            "expected": "ai_cs"
        },
        {
            "journal": "Journal of Agricultural Science",
            "expected": "agriculture_animal"
        },
        {
            "journal": "Physical Review Letters",
            "expected": "engineering_physics"
        },
        {
            "journal": "Journal of Economics",
            "expected": "economics_business"
        },
        {
            "journal": "Unknown Journal",
            "expected": "ai_cs"  # default
        }
    ]
    
    for test in test_cases:
        paper_data = {"journal": test["journal"]}
        result = _infer_category_from_metadata(paper_data)
        status = "✅" if result == test["expected"] else "❌"
        print(f"{status} {test['journal']}: {result} (expected: {test['expected']})")
    
    print("=" * 60)


if __name__ == "__main__":
    print("\n🧪 DOI Backend Endpoint Tests\n")
    
    # Run tests
    asyncio.run(test_doi_fetcher())
    asyncio.run(test_category_inference())
    
    print("\n✅ All tests completed!")
