import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.orchestrator import OrchestratorAgent

@pytest.mark.asyncio
async def test_agent_chooses_tool(mock_llm_client, db_session, mock_rag_engine):
    # Setup
    mock_llm_client.complete.return_value = '{"action": "semantic_search", "action_input": {"query": "test"}}'
    
    agent = OrchestratorAgent(mock_llm_client, db_session, mock_rag_engine)
    
    # Run
    response = await agent.process_user_message("user_123", "Search for test papers")
    
    # Verify
    # Since the mock always returns the same action, the agent's loop detection should trigger
    assert response['status'] == 'loop_detected'
    # Wait, if we return "semantic_search" once, the next loop it sees the result and should "Final Answer"
    # But our mock ALWAYS returns "semantic_search". So it will loop.
    # We need to mock side effects for LLM response
    
    mock_llm_client.complete.side_effect = [
        '{"action": "semantic_search", "action_input": {"query": "test"}}',
        '{"action": "Final Answer", "action_input": "Found them."}'
    ]
    
    response = await agent.process_user_message("user_123", "Search for test papers")
    assert response['status'] == 'success'
    assert response['result'] == "Found them."
    
    # Verify tool was called
    mock_rag_engine.query.assert_called()

@pytest.mark.asyncio
async def test_agent_direct_answer(mock_llm_client, db_session, mock_rag_engine):
    mock_llm_client.complete.return_value = '{"action": "Final Answer", "action_input": "Hello"}'
    agent = OrchestratorAgent(mock_llm_client, db_session, mock_rag_engine)
    
    response = await agent.process_user_message("user_123", "Hi")
    assert response['status'] == 'success'
    assert response['result'] == "Hello"
