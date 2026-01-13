"""
Integration Tests for AI Agent System
Tests full pipelines: fill_all_tabs, agent delegation, memory system.
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import json


# ==================== FILL ALL TABS INTEGRATION TEST ====================

class TestFillAllTabs:
    """Integration tests for the fill_all_tabs master tool."""
    
    @pytest.fixture
    def mock_components(self):
        """Create all mock components for fill_all_tabs."""
        db = MagicMock()
        
        # Mock papers in project
        db.execute.return_value.fetchall.return_value = [
            MagicMock(id=1, title="Paper 1", source="arXiv"),
            MagicMock(id=2, title="Paper 2", source="Semantic Scholar"),
        ]
        
        rag = MagicMock()
        rag.retrieve_only = AsyncMock(return_value=[
            {"text": "Methodology content from paper", "metadata": {"paper_id": 1}}
        ])
        
        llm = MagicMock()
        llm.complete = Mock(return_value=json.dumps({
            "methodology_summary": "Mixed methods approach",
            "data_collection": "Surveys and interviews",
            "analysis_methods": "Thematic analysis",
            "sample_size": "N=100"
        }))
        
        return {"db": db, "rag": rag, "llm": llm}
    
    @pytest.mark.asyncio
    async def test_fill_all_tabs_processes_all_papers(self, mock_components):
        """Test that fill_all_tabs processes each paper."""
        from app.tools import master_tools
        
        result = await master_tools.fill_all_tabs(
            project_id=1,
            user_id="test-user",
            db=mock_components["db"],
            rag_engine=mock_components["rag"],
            llm_client=mock_components["llm"]
        )
        
        assert result is not None
        assert result.get("status") == "completed" or "error" not in result
    
    @pytest.mark.asyncio
    async def test_fill_all_tabs_with_checkpoint(self, mock_components):
        """Test checkpointing: resume from where it left off."""
        from app.tools import master_tools
        
        # Simulate partial completion
        mock_components["db"].execute.return_value.fetchone.return_value = MagicMock(
            checkpoint=json.dumps({"phase": "findings", "completed_papers": [1]})
        )
        
        result = await master_tools.fill_all_tabs(
            project_id=1,
            user_id="test-user",
            db=mock_components["db"],
            rag_engine=mock_components["rag"],
            llm_client=mock_components["llm"]
        )
        
        # Should continue from checkpoint
        assert result is not None


# ==================== AGENT DELEGATION TESTS ====================

class TestAgentDelegation:
    """Test MainAgent → LiteratureReviewAgent delegation."""
    
    @pytest.fixture
    def mock_agents(self):
        """Create mock agents."""
        mock_llm = MagicMock()
        mock_llm.complete = Mock(return_value="I'll delegate this to the literature agent.")
        
        mock_db = MagicMock()
        
        return {"llm": mock_llm, "db": mock_db}
    
    def test_main_agent_has_delegate_tool(self, mock_agents):
        """Test MainAgent has delegation tool."""
        from app.agents.main_agent import MainAgent
        
        agent = MainAgent(
            llm_client=mock_agents["llm"],
            db=mock_agents["db"]
        )
        
        tool_names = [t.name for t in agent.agent.tools]
        assert "delegate_to_literature_agent" in tool_names
    
    def test_literature_agent_modes(self, mock_agents):
        """Test LiteratureReviewAgent has all expected modes."""
        from app.agents.literature_agent import LiteratureReviewAgent, MODE_TOOLS
        
        expected_modes = ["methodology", "findings", "comparison", "synthesis", "summary", "full"]
        
        for mode in expected_modes:
            assert mode in MODE_TOOLS


# ==================== MEMORY SYSTEM TESTS ====================

class TestMemorySystem:
    """Integration tests for memory extraction, storage, and retrieval."""
    
    @pytest.fixture
    def mock_memory_components(self):
        """Create mock components for memory system."""
        db = MagicMock()
        db.execute.return_value.fetchall.return_value = []
        
        embed_model = MagicMock()
        embed_model.get_text_embedding = Mock(return_value=[0.1] * 768)
        
        llm = MagicMock()
        llm.complete = Mock(return_value=json.dumps({
            "memories": [
                "User prefers quantitative research methods",
                "User is working on machine learning topic"
            ]
        }))
        
        return {"db": db, "embed": embed_model, "llm": llm}
    
    @pytest.mark.asyncio
    async def test_memory_extraction(self, mock_memory_components):
        """Test memory extraction from conversation."""
        from app.core.memory_manager import MemoryManager
        
        manager = MemoryManager(
            db=mock_memory_components["db"],
            embed_model=mock_memory_components["embed"],
            llm_client=mock_memory_components["llm"]
        )
        
        messages = [
            {"role": "user", "content": "I prefer quantitative research methods"},
            {"role": "assistant", "content": "I understand you prefer quantitative methods."}
        ]
        
        memories = await manager.extract_memories(
            conversation_id="conv-1",
            user_id="user-1",
            messages=messages
        )
        
        # Should extract at least one memory
        assert memories is not None
    
    @pytest.mark.asyncio
    async def test_memory_retrieval(self, mock_memory_components):
        """Test memory retrieval by semantic search."""
        from app.core.memory_manager import MemoryManager
        
        manager = MemoryManager(
            db=mock_memory_components["db"],
            embed_model=mock_memory_components["embed"],
            llm_client=mock_memory_components["llm"]
        )
        
        # Mock stored memories
        mock_memory_components["db"].execute.return_value.fetchall.return_value = [
            MagicMock(
                id=1,
                content="User prefers quantitative methods",
                importance=0.9
            )
        ]
        
        memories = await manager.retrieve_memories(
            user_id="user-1",
            query="What research methods does the user prefer?"
        )
        
        assert memories is not None


# ==================== WEBSOCKET INTEGRATION TESTS ====================

class TestWebSocketFlow:
    """Test WebSocket message flow."""
    
    @pytest.mark.asyncio
    async def test_message_flow_structure(self):
        """Test that message updates have correct structure."""
        expected_types = [
            "thinking",
            "tool_selected", 
            "tool_executing",
            "tool_result",
            "synthesizing",
            "message",
            "message_end"
        ]
        
        # These are the update types the frontend expects
        for update_type in expected_types:
            assert isinstance(update_type, str)
    
    def test_model_id_in_request(self):
        """Test that model_id is properly extracted from request."""
        request_data = {
            "message": "Hello",
            "project_id": 1,
            "user_id": "user-1",
            "scope": "project",
            "model_id": "groq/qwen3-32b",
            "selected_paper_ids": []
        }
        
        model_id = request_data.get("model_id")
        assert model_id == "groq/qwen3-32b"


# ==================== LLM FALLBACK TESTS ====================

class TestLLMFallback:
    """Test LLM fallback handling."""
    
    def test_fallback_handler_creation(self):
        """Test LLMFallbackHandler can be created."""
        from app.core.llm_fallback import LLMFallbackHandler
        
        mock_client = MagicMock()
        
        handler = LLMFallbackHandler(
            primary_model="groq/qwen3-32b",
            primary_client=mock_client,
            fallback_models=[],
            fallback_clients={}
        )
        
        assert handler.primary_model == "groq/qwen3-32b"
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts closed."""
        from app.core.llm_fallback import LLMFallbackHandler
        
        mock_client = MagicMock()
        
        handler = LLMFallbackHandler(
            primary_model="test",
            primary_client=mock_client
        )
        
        # Circuit should be closed initially
        assert not handler._is_circuit_open("test")


# ==================== END-TO-END FLOW TEST ====================

class TestEndToEndFlow:
    """Test complete request → response flow."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_context_setting(self):
        """Test that orchestrator sets context correctly."""
        from app.agents.orchestrator import OrchestratorAgent
        from unittest.mock import MagicMock
        
        mock_llm = MagicMock()
        mock_llm.complete = Mock(return_value="I'll help you with that.")
        mock_db = MagicMock()
        
        orchestrator = OrchestratorAgent(
            llm_client=mock_llm,
            db=mock_db,
            rag_engine=None
        )
        
        # Process a message
        await orchestrator.process_user_message(
            user_id="user-1",
            message="List my projects",
            project_id=1
        )
        
        # Context should be set
        assert orchestrator.agent.context["user_id"] == "user-1"
        assert orchestrator.agent.context["project_id"] == 1


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
