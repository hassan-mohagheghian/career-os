"""Shared test fixtures and configuration."""

import sys
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add server directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import SA Base and all models to register them
from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model
import processing.infrastructure.models.pending_model
import career.infrastructure.models.insight_model
import shared.infrastructure.database.models.misc_models


@pytest.fixture
def test_db():
    """Create a temp DB using SA Base.metadata.create_all. Auto-cleanup."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    yield path
    os.remove(path)


@pytest.fixture
def sa_session(test_db):
    """Create a SQLAlchemy session connected to the test DB with all tables."""
    engine = create_engine(f"sqlite:///{test_db}")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def mock_get_session(sa_session):
    """Patch dependencies.get_session_sync to return our test SA session."""
    with patch('dependencies.get_session_sync', return_value=sa_session):
        yield sa_session


@pytest.fixture
def mock_get_session_worker(sa_session):
    """Patch services.worker.get_session_sync to return our test SA session."""
    with patch('services.worker.get_session_sync', return_value=sa_session):
        yield sa_session


@pytest.fixture
def mock_get_session_company_worker(sa_session):
    """Patch services.company_worker.get_session_sync to return our test SA session."""
    with patch('services.company_worker.get_session_sync', return_value=sa_session):
        yield sa_session
