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
    """Return a MockProvider with pre-configured responses."""
    from ai.infrastructure.providers.mock import MockProvider
    return MockProvider()


@pytest.fixture
def test_db():
    """Create a temporary DB with schema via ORM, return path. Auto-cleanup."""
    from sqlalchemy import create_engine
    from shared.infrastructure.database.sqlalchemy_config import Base
    from jobs.infrastructure.models.job_model import JobModel
    from skills.infrastructure.models.skill_model import SkillModel

    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    yield path
    os.remove(path)
