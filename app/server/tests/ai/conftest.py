"""Shared test fixtures for the AI agent layer."""

import sys
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

# Add server directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


@pytest.fixture
def provider_config():
    """Return a default ProviderConfig for testing."""
    from ai.infrastructure.providers.base import ProviderConfig
    return ProviderConfig(name="test", timeout=30)


@pytest.fixture
def mock_llm_provider():
    """Return a mock LLMProvider with pre-configured responses."""
    from ai.infrastructure.providers.base import LLMProvider, ProviderResponse

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
    """Create a temporary DB with schema via ORM, return path. Auto-cleanup."""
    from sqlalchemy import create_engine
    from shared.infrastructure.database.sqlalchemy_config import Base
    from jobs.infrastructure.models.job_model import JobModel
    from skills.infrastructure.models.skill_model import SkillModel
    from processing.infrastructure.models.pending_model import PendingJobModel

    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    yield path
    os.remove(path)
