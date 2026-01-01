
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.orchestrator import OrchestratorAgent
from app.tools import rag_tools

# Mocks
@pytest.fixture
def mock_llm_client():
    return AsyncMock()

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_rag_engine():
    rag = AsyncMock()
    # Mock query to return a standard structure
    rag.query.return_value = {
        "answer": "Mock Answer",
        "source_nodes": [
            {"text": "Ref 1", "metadata": {"paper_id": 1}},
            {"text": "Ref 2", "metadata": {"paper_id": 2}}
        ]
    }
    return rag

@pytest.mark.asyncio
async def test_semantic_search_scope_project(mock_rag_engine):
    """Test that scope='project' passes project_id to rag_engine"""
    
    # Call the tool directly
    await rag_tools.semantic_search(
        query="test query",
        project_id=123,
        scope="project",
        selected_paper_ids=None,
        rag_engine=mock_rag_engine
    )
    
    # Verify rag_engine.query called with project_id=123 and paper_ids=None
    mock_rag_engine.query.assert_called_once()
    call_kwargs = mock_rag_engine.query.call_args.kwargs
    
    assert call_kwargs['query_text'] == "test query"
    assert call_kwargs['project_id'] == 123
    assert call_kwargs['paper_ids'] is None


@pytest.mark.asyncio
async def test_semantic_search_scope_library(mock_rag_engine):
    """Test that scope='library' ignores project_id (sets to None)"""
    
    await rag_tools.semantic_search(
        query="test query",
        project_id=123, # Should be ignored
        scope="library",
        selected_paper_ids=None,
        rag_engine=mock_rag_engine
    )
    
    mock_rag_engine.query.assert_called_once()
    call_kwargs = mock_rag_engine.query.call_args.kwargs
    
    # project_id should be None for Global Search
    assert call_kwargs['project_id'] is None
    assert call_kwargs['paper_ids'] is None

@pytest.mark.asyncio
async def test_semantic_search_scope_selection(mock_rag_engine):
    """Test that scope='selection' passes specific paper_ids"""
    
    selected_ids = [10, 20, 30]
    
    await rag_tools.semantic_search(
        query="test query",
        project_id=123,
        scope="selection",
        selected_paper_ids=selected_ids,
        rag_engine=mock_rag_engine
    )
    
    mock_rag_engine.query.assert_called_once()
    call_kwargs = mock_rag_engine.query.call_args.kwargs
    
    # Should ignore project_id strict filter if we want to search *specific papers* irrespective of project
    # OR we might want to enforce project_id AND paper_ids. 
    # Current impl sets project_id=None to allow cross-project selection if needed, 
    # or just to focus on the list.
    assert call_kwargs['project_id'] is None
    assert call_kwargs['paper_ids'] == selected_ids

@pytest.mark.asyncio
async def test_orchestrator_integration(mock_llm_client, mock_db, mock_rag_engine):
    """Test that Orchestrator properly injects context into tools"""
    
    orchestrator = OrchestratorAgent(mock_llm_client, mock_db, mock_rag_engine)
    
    # Manually set context (usually set in 'process_user_message')
    orchestrator.agent.context = {
        'user_id': "u1",
        'project_id': 999,
        'scope': 'selection',
        'selected_paper_ids': [1, 2]
    }
    
    # Find the 'semantic_search' tool
    search_tool = next(t for t in orchestrator.tools if t.name == "semantic_search")
    
    # Execute the tool's function wrapper
    # The wrapper should pull 'scope' and 'selected_paper_ids' from self.agent.context
    await search_tool.function(query="test context injection")
    
    # Check if rag_engine received the context values
    mock_rag_engine.query.assert_called_once()
    call_kwargs = mock_rag_engine.query.call_args.kwargs
    
    # In 'selection' mode, project_id is cleared
    assert call_kwargs['project_id'] is None

@pytest.mark.asyncio
async def test_get_paper_sections_integration(mock_llm_client, mock_db, mock_rag_engine):
    """Test that get_paper_sections passes section_filter correctly"""
    orchestrator = OrchestratorAgent(mock_llm_client, mock_db, mock_rag_engine)
    
    # Find the tool
    sections_tool = next(t for t in orchestrator.tools if t.name == "get_paper_sections")
    
    # Execute with multiple sections
    await sections_tool.function(
        section_types=["Methodology", "Results"],
        paper_ids=[5]
    )
    
    # Verify rag_engine.retrieve_only called with explicit section_filter
    mock_rag_engine.retrieve_only.assert_called_once()
    call_kwargs = mock_rag_engine.retrieve_only.call_args.kwargs
    
    # Query text should be joined
    assert call_kwargs['query_text'] == "Methodology Results"
    # Filter should be list
    assert call_kwargs['section_filter'] == ["Methodology", "Results"]
    assert call_kwargs['paper_ids'] == [5]
    assert call_kwargs['top_k'] == 50
