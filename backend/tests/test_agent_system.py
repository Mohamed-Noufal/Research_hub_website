"""
Unit Tests for AI Agent System
Tests Pydantic schemas, tool execution, and mode switching.
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import json


# ==================== PYDANTIC SCHEMA TESTS ====================

class TestSchemaValidation:
    """Test Pydantic schema validation for agent outputs."""
    
    def test_methodology_output_valid(self):
        """Test valid methodology output passes validation."""
        from app.schemas.agent_outputs import MethodologyOutput
        
        data = {
            "methodology_summary": "This study uses a mixed-methods approach combining surveys and interviews.",
            "data_collection": "Surveys distributed to 500 participants, followed by 20 interviews.",
            "analysis_methods": "Thematic analysis for qualitative data, regression for quantitative.",
            "sample_size": "N=500 (survey), N=20 (interviews)"
        }
        
        output = MethodologyOutput(**data)
        assert output.methodology_summary is not None
        assert len(output.methodology_summary) >= 10
    
    def test_methodology_output_missing_required_field(self):
        """Test that missing required field raises error."""
        from app.schemas.agent_outputs import MethodologyOutput
        from pydantic import ValidationError
        
        data = {
            # Missing methodology_summary (required)
            "data_collection": "Some data collection method"
        }
        
        with pytest.raises(ValidationError):
            MethodologyOutput(**data)
    
    def test_methodology_output_too_short(self):
        """Test that summary too short raises error."""
        from app.schemas.agent_outputs import MethodologyOutput
        from pydantic import ValidationError
        
        data = {
            "methodology_summary": "Short"  # Less than min_length
        }
        
        with pytest.raises(ValidationError):
            MethodologyOutput(**data)
    
    def test_findings_output_valid(self):
        """Test valid findings output passes validation."""
        from app.schemas.agent_outputs import FindingsOutput
        
        data = {
            "key_finding": "The study found a significant correlation between X and Y.",
            "limitations": "Small sample size limits generalizability.",
            "evidence_level": "moderate"
        }
        
        output = FindingsOutput(**data)
        assert output.key_finding is not None
        assert output.evidence_level == "moderate"
    
    def test_findings_output_invalid_evidence_level(self):
        """Test that invalid evidence level raises error."""
        from app.schemas.agent_outputs import FindingsOutput
        from pydantic import ValidationError
        
        data = {
            "key_finding": "Some finding here that is long enough",
            "evidence_level": "invalid_level"  # Not in allowed values
        }
        
        with pytest.raises(ValidationError):
            FindingsOutput(**data)


# ==================== TOOL EXECUTION TESTS ====================

class TestToolExecution:
    """Test individual tool functions."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute.return_value.fetchall.return_value = []
        db.execute.return_value.fetchone.return_value = None
        return db
    
    @pytest.fixture
    def mock_rag_engine(self):
        """Create mock RAG engine."""
        rag = MagicMock()
        rag.retrieve_only = AsyncMock(return_value=[
            {"text": "Sample methodology text", "metadata": {"paper_id": 1}}
        ])
        return rag
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        llm = MagicMock()
        llm.complete = Mock(return_value=json.dumps({
            "methodology_summary": "This study uses surveys.",
            "data_collection": "Online surveys",
            "analysis_methods": "Statistical analysis",
            "sample_size": "N=100"
        }))
        return llm
    
    def test_get_project_papers(self, mock_db):
        """Test get_project_papers returns correct format."""
        from app.tools import database_tools
        
        # Mock return data
        mock_db.execute.return_value.fetchall.return_value = [
            MagicMock(id=1, title="Paper 1", source="arXiv"),
            MagicMock(id=2, title="Paper 2", source="Semantic Scholar")
        ]
        
        result = database_tools.get_project_papers(project_id=1, db=mock_db)
        
        assert "papers" in result
        assert len(result["papers"]) == 2
    
    def test_list_projects(self, mock_db):
        """Test list_projects returns user's projects."""
        from app.tools import literature_tools
        from collections import namedtuple
        
        # Create proper named tuple for row
        ProjectRow = namedtuple('ProjectRow', ['id', 'name', 'paper_count'])
        mock_db.execute.return_value.fetchall.return_value = [
            ProjectRow(id=1, name="Project 1", paper_count=5),
            ProjectRow(id=2, name="Project 2", paper_count=3)
        ]
        
        result = literature_tools.list_projects(user_id="test-user", db=mock_db)
        
        assert result is not None
    
    def test_semantic_search(self, mock_rag_engine):
        """Test semantic search returns results."""
        from app.tools import rag_tools
        
        # Mock the retrieve_only to return synchronously
        mock_rag_engine.retrieve_only = Mock(return_value=[
            {"text": "Sample text", "metadata": {"paper_id": 1}}
        ])
        
        # semantic_search is sync and uses retrieve_only
        result = rag_tools.semantic_search(
            query="machine learning methodology",
            project_id=1,
            top_k=5,
            scope="project",
            rag_engine=mock_rag_engine
        )
        
        # Should return a result dict
        assert result is not None


# ==================== MODE SWITCHING TESTS ====================

class TestModeSwitching:
    """Test LiteratureReviewAgent mode switching."""
    
    def test_mode_creates_correct_tools(self):
        """Test that each mode loads correct tool subset."""
        from app.agents.literature_agent import MODE_TOOLS
        
        # Each mode should have specific tools
        assert "extract_methodology" in MODE_TOOLS["methodology"]
        assert "extract_findings" in MODE_TOOLS["findings"]
        assert "compare_papers" in MODE_TOOLS["comparison"]
        assert "find_research_gaps" in MODE_TOOLS["synthesis"]
        
        # Full mode should have all tools
        assert len(MODE_TOOLS["full"]) > len(MODE_TOOLS["methodology"])
    
    def test_mode_switch_rebuilds_agent(self):
        """Test that switching mode rebuilds the agent."""
        from app.agents.literature_agent import LiteratureReviewAgent
        from unittest.mock import MagicMock
        
        mock_llm = MagicMock()
        mock_db = MagicMock()
        
        agent = LiteratureReviewAgent(
            llm_client=mock_llm,
            db=mock_db,
            rag_engine=None
        )
        
        initial_mode = agent.current_mode
        agent.set_mode("findings")
        
        # Mode should have changed
        assert agent.current_mode == "findings"
        assert agent.current_mode != initial_mode


# ==================== EMBEDDING CACHE TESTS ====================

class TestEmbeddingCache:
    """Test embedding cache functionality."""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get."""
        from app.core.embedding_cache import EmbeddingCache
        
        cache = EmbeddingCache(redis_url=None)  # Memory only
        
        text = "Sample text for embedding"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        cache.set(text, embedding)
        result = cache.get(text)
        
        assert result == embedding
    
    def test_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        from app.core.embedding_cache import EmbeddingCache
        
        cache = EmbeddingCache(redis_url=None)
        result = cache.get("text not in cache")
        
        assert result is None
    
    def test_cache_batch_operations(self):
        """Test batch get and set."""
        from app.core.embedding_cache import EmbeddingCache
        
        cache = EmbeddingCache(redis_url=None)
        
        texts = {
            "text1": [0.1, 0.2],
            "text2": [0.3, 0.4],
            "text3": [0.5, 0.6]
        }
        
        cache.set_many(texts)
        results = cache.get_many(list(texts.keys()))
        
        assert results["text1"] == [0.1, 0.2]
        assert results["text2"] == [0.3, 0.4]


# ==================== RATE LIMITER TESTS ====================

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=10,
            burst_size=5,
            redis_url=None
        )
        
        # First 5 requests should be allowed (burst)
        for _ in range(5):
            assert limiter.allow("user1") == True
    
    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=10,
            burst_size=2,  # Low burst for testing
            redis_url=None
        )
        
        # Use up burst
        limiter.allow("user2")
        limiter.allow("user2")
        
        # Third request should fail
        assert limiter.allow("user2") == False
    
    def test_per_user_limits(self):
        """Test that limits are per-user."""
        from app.core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=10,
            burst_size=2,
            redis_url=None
        )
        
        # Use up user1's burst
        limiter.allow("user1")
        limiter.allow("user1")
        assert limiter.allow("user1") == False
        
        # user2 should still have their burst
        assert limiter.allow("user2") == True


# ==================== MODEL CONFIG TESTS ====================

class TestModelConfig:
    """Test model configuration."""
    
    def test_available_models_exist(self):
        """Test that expected models are configured."""
        from app.core.model_config import AVAILABLE_MODELS
        
        assert "groq/qwen3-32b" in AVAILABLE_MODELS
        assert "together/qwen3-235b" in AVAILABLE_MODELS
        assert "google/gemini-3-flash" in AVAILABLE_MODELS
    
    def test_get_default_model(self):
        """Test default model selection."""
        from app.core.model_config import get_default_model
        
        default = get_default_model()
        
        assert default is not None
        assert default.id is not None
    
    def test_estimate_cost(self):
        """Test cost estimation."""
        from app.core.model_config import estimate_cost
        
        # 1M tokens should match the per-million rate
        cost = estimate_cost("groq/qwen3-32b", 1_000_000, 1_000_000)
        
        # Groq is free
        assert cost == 0.0


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
