import pytest
from app.tools import rag_tools

@pytest.mark.asyncio
async def test_semantic_search_mock(mock_rag_engine):
    results = await rag_tools.semantic_search("test query", rag_engine=mock_rag_engine)
    assert len(results) == 1
    assert results[0]['text'] == "Mock chunk"
    mock_rag_engine.query.assert_called_once()

@pytest.mark.asyncio
async def test_compare_papers_mock(mock_rag_engine, mock_llm_client):
    mock_llm_client.complete.return_value = '{"similarities": "sim", "differences": "diff"}'
    
    result = await rag_tools.compare_papers(
        paper_ids=[1, 2],
        rag_engine=mock_rag_engine,
        llm_client=mock_llm_client
    )
    
    assert result['similarities'] == "sim"
    assert result['differences'] == "diff"

@pytest.mark.asyncio
async def test_extract_methodology_mock(mock_rag_engine, mock_llm_client):
    mock_llm_client.complete.return_value = '{"methodology_summary": "Summary", "data_collection": "Data", "analysis_methods": "Analysis", "sample_size": "100"}'
    
    result = await rag_tools.extract_methodology(
        paper_id=1,
        rag_engine=mock_rag_engine,
        llm_client=mock_llm_client
    )
    
    assert result['methodology_summary'] == "Summary"
    assert result['sample_size'] == "100"
