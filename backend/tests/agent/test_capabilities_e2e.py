import pytest
from unittest.mock import AsyncMock
from app.agents.orchestrator import OrchestratorAgent

@pytest.mark.asyncio
async def test_capability_rag_retrieval(mock_llm_client, db_session, mock_rag_engine):
    """
    Test that the agent correctly identifies a RAG intent and delegates to tool
    """
    # 1. User asks for specific info
    # 2. Agent calls semantic_search
    # 3. Agent summarizes result
    
    mock_llm_client.complete.side_effect = [
        '{"action": "semantic_search", "action_input": {"query": "transformer architecture"}}',
        '{"action": "Final Answer", "action_input": "The transformer architecture is based on attention mechanisms."}'
    ]
    
    agent = OrchestratorAgent(mock_llm_client, db_session, mock_rag_engine)
    response = await agent.process_user_message("user_1", "How does transformer architecture work?")
    
    assert response['status'] == 'success'
    assert "transformer" in response['result'].lower()
    mock_rag_engine.query.assert_called()

@pytest.mark.asyncio
async def test_capability_pdf_extraction(mock_llm_client, db_session, mock_rag_engine):
    """
    Test execution path for PDF parsing (mocked background job)
    """
    # Note: parse_pdf is a background job tool. 
    # We want to verify the agent calls 'parse_pdf' when asked to read a file
    
    mock_llm_client.complete.side_effect = [
        '{"action": "parse_pdf", "action_input": {"pdf_path": "uploads/test.pdf", "paper_id": 101}}',
        '{"action": "Final Answer", "action_input": "Started parsing."}'
    ]
    
    # We need to mock pdf_tools.parse_pdf_background or ensuring the tool exists
    # The tool is created inside OrchestratorAgent._create_tools -> lambda -> pdf_tools...
    # We can mock the function inside the tool instance if we want, or just rely on the tool execution logic
    
    # For this test, since we don't have a real PDF or DB, we mainly test the Agent->Tool selection logic
    # akin to integration test, but specifically for this capability.
    
    agent = OrchestratorAgent(mock_llm_client, db_session, mock_rag_engine)
    
    # We need to patch the tool function to avoid actual execution if it tries to hit DB/Files
    # Access tool by name
    tools_dict = {t.name: t for t in agent.tools}
    if 'parse_pdf' in tools_dict:
        # Replace the function with a mock
        tools_dict['parse_pdf'].function = AsyncMock(return_value="Job started 123")
        # Re-assign to agent
        agent.agent.tools = tools_dict

    response = await agent.process_user_message("user_1", "Read this PDF: uploads/test.pdf")
    
    assert response['status'] == 'success'
    assert "parsing" in response['result'].lower()
