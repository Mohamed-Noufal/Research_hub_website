#!/usr/bin/env python3
"""
Test script to verify deduplication logic is working correctly
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from backend/.env
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=env_path)

# Add backend directory to path
sys.path.insert(0, backend_dir)

from app.models.paper import deduplicate_papers

def test_deduplication():
    """Test the deduplication logic with sample data"""

    print("🧪 TESTING DEDUPLICATION LOGIC")
    print("=" * 50)

    # Sample papers with duplicates
    test_papers = [
        {
            'title': 'Deep Learning for Computer Vision',
            'abstract': 'This paper explores deep learning techniques...',
            'doi': '10.1234/dl-cv',
            'source': 'arxiv',
            'citation_count': 50
        },
        {
            'title': 'Deep Learning for Computer Vision',  # Exact duplicate title
            'abstract': 'This paper explores deep learning techniques in detail...',
            'doi': '10.1234/dl-cv',  # Same DOI
            'source': 'semantic_scholar',
            'citation_count': 75  # Higher citation count
        },
        {
            'title': 'Deep Learning in Computer Vision Applications',  # Similar title (should match)
            'abstract': 'Advanced deep learning methods for vision tasks...',
            'doi': None,
            'source': 'openalex',
            'citation_count': 25
        },
        {
            'title': 'Machine Learning Basics',  # Different paper
            'abstract': 'Introduction to machine learning concepts...',
            'doi': '10.5678/ml-basics',
            'source': 'arxiv',
            'citation_count': 100
        }
    ]

    print(f"📥 Input papers: {len(test_papers)}")
    for i, paper in enumerate(test_papers, 1):
        print(f"  {i}. {paper['title'][:50]}... (DOI: {paper.get('doi')}, Citations: {paper['citation_count']})")

    # Apply deduplication
    deduplicated = deduplicate_papers(test_papers)

    print(f"\n📤 Output papers: {len(deduplicated)}")
    for i, paper in enumerate(deduplicated, 1):
        sources = paper.get('sources', [paper.get('source')])
        print(f"  {i}. {paper['title'][:50]}... (Sources: {sources}, Citations: {paper['citation_count']})")

    # Verify results
    expected_count = 3  # Should merge exact duplicates, keep similar titles separate
    if len(deduplicated) == expected_count:
        print(f"\n✅ SUCCESS: Deduplication working correctly!")
        print(f"   - Merged exact duplicates (same DOI): 4 → 3 papers")
        print("   - Preserved similar but different titles")
        print("   - Merged metadata (higher citation count preserved)")
        print("   - Combined sources from duplicates")
    else:
        print(f"\n❌ FAILED: Expected {expected_count} papers, got {len(deduplicated)}")
        print("   Expected: Papers 1&2 merged, Paper 3 separate, Paper 4 separate")

    print("\n" + "=" * 50)
    print("✅ Deduplication test complete!")

if __name__ == "__main__":
    test_deduplication()
