"""
Debug script to test DOI fetching for specific DOI
Tests: 10.3390/s25175264
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.doi_fetcher_service import DOIFetcherService


async def debug_doi_fetch(doi: str):
    """Debug DOI fetching for a specific DOI"""
    print("=" * 80)
    print(f"Debugging DOI: {doi}")
    print("=" * 80)
    
    fetcher = DOIFetcherService()
    
    # Test each source individually
    sources = {
        "Crossref": fetcher._fetch_from_crossref,
        "Unpaywall": fetcher._fetch_from_unpaywall,
        "Semantic Scholar": fetcher._fetch_from_semantic_scholar,
    }
    
    for source_name, fetch_func in sources.items():
        print(f"\n{'='*80}")
        print(f"Testing: {source_name}")
        print(f"{'='*80}")
        
        try:
            result = await fetch_func(doi)
            
            if result:
                print(f"✅ SUCCESS from {source_name}")
                print(f"\nTitle: {result.get('title', 'N/A')}")
                print(f"Abstract: {result.get('abstract', 'N/A')[:200]}...")
                print(f"Authors: {result.get('authors', [])}")
                print(f"Journal: {result.get('journal', 'N/A')}")
                print(f"Publisher: {result.get('publisher', 'N/A')}")
                print(f"PDF URL: {result.get('pdf_url', 'N/A')}")
                print(f"Citation Count: {result.get('citation_count', 0)}")
                print(f"Publication Date: {result.get('publication_date', 'N/A')}")
                print(f"\nFull metadata keys: {list(result.keys())}")
            else:
                print(f"❌ No result from {source_name}")
                
        except Exception as e:
            print(f"❌ Error from {source_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Test the combined fetch
    print(f"\n{'='*80}")
    print("Testing Combined Fetch (fetch_paper_by_doi)")
    print(f"{'='*80}")
    
    try:
        result = await fetcher.fetch_paper_by_doi(doi)
        if result:
            print(f"✅ Combined fetch successful")
            print(f"\nSource used: {result.get('source', 'N/A')}")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Abstract: {result.get('abstract', 'N/A')[:200]}...")
            print(f"Authors: {result.get('authors', [])}")
            print(f"\nFull result:")
            import json
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"❌ Combined fetch returned None")
    except Exception as e:
        print(f"❌ Combined fetch error: {e}")
        import traceback
        traceback.print_exc()
    
    await fetcher.close()
    
    print("\n" + "=" * 80)
    print("Debug Complete!")
    print("=" * 80)


if __name__ == "__main__":
    doi = "10.3390/s25175264"
    print(f"\n🔍 Debugging DOI Fetch for: {doi}\n")
    asyncio.run(debug_doi_fetch(doi))
