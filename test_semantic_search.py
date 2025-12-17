#!/usr/bin/env python3
"""
Test script for semantic search functionality
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.embedding_service import EmbeddingService

async def test_semantic_search():
    """Test the semantic search functionality"""
    print("🚀 Testing Semantic Search Implementation")
    print("=" * 50)

    # Initialize embedding service
    print("Loading embedding model... (this may take a moment)")
    embedding_service = EmbeddingService()

    # Sample papers for testing
    papers = [
        {
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism.",
            "citation_count": 50000,
            "source": "arxiv"
        },
        {
            "title": "Transformer Architecture Overview",
            "abstract": "This paper provides an overview of transformer architectures, focusing on the attention mechanisms that allow parallel processing of sequences.",
            "citation_count": 1000,
            "source": "semantic_scholar"
        },
        {
            "title": "Query-Key-Value Attention Processing",
            "abstract": "We explore the query-key-value mechanism in neural attention, showing how it enables efficient information retrieval from sequences.",
            "citation_count": 500,
            "source": "openalex"
        },
        {
            "title": "Deep Learning for Natural Language Processing",
            "abstract": "This survey covers modern approaches to natural language processing using deep neural networks, including RNNs, CNNs, and transformers.",
            "citation_count": 2000,
            "source": "arxiv"
        },
        {
            "title": "Multi-Head Attention Mechanisms",
            "abstract": "This work introduces multi-head attention, allowing models to jointly attend to information from different representation subspaces.",
            "citation_count": 3000,
            "source": "semantic_scholar"
        }
    ]

    print(f"\n📚 Testing with {len(papers)} sample papers:")
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title']} (citations: {paper['citation_count']})")

    # Test queries - including synonyms and different phrasings
    test_queries = [
        "attention mechanisms",
        "transformer networks",
        "neural attention models",
        "sequence processing with attention",
        "deep learning transformers"
    ]

    print(f"\n🔍 Testing semantic reranking with {len(test_queries)} queries...\n")

    for query in test_queries:
        print(f"Query: \"{query}\"")
        print("-" * 40)

        # Get semantic reranking
        reranked = embedding_service.rerank_by_semantic_similarity(query, papers.copy(), top_k=3)

        print("🎯 Top 3 semantic matches:")
        for i, paper in enumerate(reranked, 1):
            # Show semantic score if available
            score_info = ""
            if 'semantic_score' in paper:
                score_info = f" (score: {paper['semantic_score']:.3f})"
            print(f"   {i}. {paper['title']}{score_info}")

        print()

    # Compare with keyword-based ranking
    print("📊 Comparison: Keyword vs Semantic Ranking")
    print("=" * 50)

    keyword_query = "attention"
    print(f"Query: \"{keyword_query}\"")
    print()

    # Keyword ranking (simple title/abstract contains)
    keyword_ranked = sorted(papers, key=lambda p:
        (keyword_query.lower() in p['title'].lower()) * 10 +
        (keyword_query.lower() in p['abstract'].lower()) * 5,
        reverse=True)[:3]

    # Semantic ranking
    semantic_ranked = embedding_service.rerank_by_semantic_similarity(keyword_query, papers.copy(), top_k=3)

    print("📋 Keyword-based ranking:")
    for i, paper in enumerate(keyword_ranked, 1):
        has_keyword = "✓" if keyword_query.lower() in paper['title'].lower() or keyword_query.lower() in paper['abstract'].lower() else "✗"
        print(f"   {i}. {paper['title']} [{has_keyword}]")

    print("\n🎯 Semantic-based ranking:")
    for i, paper in enumerate(semantic_ranked, 1):
        if 'semantic_score' in paper:
            score = paper['semantic_score']
            print(f"   {i}. {paper['title']} (score: {score:.3f})")
        else:
            print(f"   {i}. {paper['title']}")

    print("\n✅ Semantic search test completed!")
    print("\n💡 Key observations:")
    print("   - Semantic search finds papers even without exact keyword matches")
    print("   - It understands meaning and synonyms")
    print("   - Results are often more relevant than simple keyword matching")

if __name__ == "__main__":
    asyncio.run(test_semantic_search())
