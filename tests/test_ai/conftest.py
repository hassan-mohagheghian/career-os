"""Shared test fixtures for the AI agent layer."""

import sys
import os
import tempfile
import sqlite3
import pytest
from unittest.mock import MagicMock, patch

# Add server directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.fixture
def provider_config():
    """Return a default ProviderConfig for testing."""
    from app.ai.providers.base import ProviderConfig
    return ProviderConfig(name="test", timeout=30)


@pytest.fixture
def mock_llm_provider():
    """Return a mock LLMProvider with pre-configured responses."""
    from app.ai.providers.base import LLMProvider, ProviderResponse

    provider = MagicMock(spec=LLMProvider)
    provider.name = "mock"
    provider.generate.return_value = ProviderResponse(
        content="mock response",
        metadata={"mock": True},
        provider="mock",
        model="mock-model",
    )
    provider.generate_structured.return_value = ProviderResponse(
        content='{"result": "mock"}',
        metadata={"mock": True},
        provider="mock",
        model="mock-model",
    )
    return provider


@pytest.fixture
def test_db():
    """Create a temporary DB with schema, return path. Auto-cleanup."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            num INTEGER PRIMARY KEY,
            company TEXT, role TEXT, location TEXT, match TEXT,
            score TEXT, salary TEXT, stack TEXT, visa TEXT,
            url TEXT, deleted INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS tech_stack (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, level INTEGER, category TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS pending_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT, status TEXT DEFAULT 'pending'
        );
    """)
    conn.commit()
    conn.close()
    yield path
    os.remove(path)
