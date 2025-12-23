import pytest
import os
import sys
from unittest.mock import MagicMock
import unittest.mock

# Ensure backend path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock Environment Variables needed for Settings
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost/test_db"
os.environ["GROQ_API_KEY"] = "mock_key" # Optional but good to have


# from app.core.database import SessionLocal, engine # Mocked below

import app.core.monitoring
@pytest.fixture(scope="session", autouse=True)
def mock_telemetry():
    """Mock the entire telemetry system to avoid OTLP connection attempts"""
    print("DEBUG: mock_telemetry fixture started (setup)")
    
    # Store original
    original_get_instance = app.core.monitoring.MonitoringManager.get_instance
    
    # Create mock
    mock_instance = MagicMock()
    mock_tracer = MagicMock()
    # Ensure nested mocks work for context manager
    mock_span = MagicMock()
    mock_span.__enter__.return_value = mock_span
    mock_span.__exit__.return_value = None
    mock_tracer.start_as_current_span.return_value = mock_span
    mock_instance.get_tracer.return_value = mock_tracer
    
    # Patch
    app.core.monitoring.MonitoringManager.get_instance = MagicMock(return_value=mock_instance)
    
    yield
    
    # Restore
    print("DEBUG: mock_telemetry fixture teardown")
    app.core.monitoring.MonitoringManager.get_instance = original_get_instance

@pytest.fixture(scope="session")
def db_engine():
    # Return a mock engine
    return MagicMock()

@pytest.fixture(scope="function")
def db_session(db_engine):
    # Return a mock session
    session = MagicMock()
    # Ensure commit/rollback don't fail
    session.commit.return_value = None
    session.rollback.return_value = None
    yield session

import asyncio
from unittest.mock import AsyncMock

@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.complete.return_value = '{"action": "Final Answer", "action_input": "Mocked response"}'
    return client

@pytest.fixture
def mock_rag_engine():
    engine = AsyncMock()
    engine.query.return_value = {"source_nodes": [{"text": "Mock chunk", "metadata": {"paper_id": 1}}]}
    engine.retrieve_only.return_value = [{"text": "Mock chunk", "metadata": {"paper_id": 1}}]
    return engine
