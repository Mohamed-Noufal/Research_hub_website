
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.core.rag_engine import RAGEngine

async def test_fetch_nodes_for_bm25():
    """Test if we can fetch nodes for a project or paper"""
    # This requires DB connectivity.
    # We will try to fetch nodes for an arbitrary project_id (e.g., 1)
    # If DB is empty, it returns [], which is valid but doesn't prove schema.
    # But if SQL fails, it throws error.
    
    engine = RAGEngine()
    
    print("\nAttempting to fetch nodes for project_id=1...")
    nodes = engine._fetch_nodes_for_scope(project_id=1)
    print(f"Fetched {len(nodes)} nodes.")
    
    # Check if we got TextNodes
    if nodes:
        print(f"Sample Node: {nodes[0].get_content()[:50]}...")
        assert hasattr(nodes[0], 'id_')
        assert hasattr(nodes[0], 'metadata')


async def test_hybrid_retriever_construction():
    """Test if hybrid retriever is built correctly"""
    engine = RAGEngine()
    
    # Mocking _fetch_nodes to avoid empty DB issue during test logic check
    # But wait, we want to test the REAL fetch.
    
    # Let's try to get the retriever.
    # It should fallback to Vector if no nodes found.
    retriever = await engine._get_hybrid_retriever(
        similarity_top_k=5, 
        filters=None,
        project_id=99999 # Unlikely to exist
    )
    
    # Should be VectorRetriever or QueryFusionRetriever?
    # If no nodes, it returns VectorRetriever.
    print(f"\nRetriever for empty project: {type(retriever)}")
    assert "VectorIndexRetriever" in str(type(retriever)) 

if __name__ == "__main__":
    # Manually run async
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_fetch_nodes_for_bm25())
    try:
        loop.run_until_complete(test_hybrid_retriever_construction())
    except Exception as e:
        print(e)
