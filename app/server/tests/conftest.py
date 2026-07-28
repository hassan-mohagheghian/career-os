"""Shared test fixtures and configuration."""

import sys
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
    with patch('jobs.infrastructure.workers.worker.get_session_sync', return_value=sa_session):
        yield sa_session


@pytest.fixture
def mock_get_session_company_worker(sa_session):
    """Patch services.company_worker.get_session_sync to return our test SA session."""
    with patch('companies.infrastructure.workers.company_worker.get_session_sync', return_value=sa_session):
        yield sa_session


@pytest.fixture
def client(sa_session):
    """Create a FastAPI test client with all routes wired to the test DB."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from fastapi.responses import JSONResponse
    from dependencies import (
        get_session, get_session_sync, get_job_repo, get_skill_repo,
        get_company_repo, get_pending_repo, get_insight_repo, get_preference_repo,
        get_summary_repo, get_resume_repo, get_company_link_repo, get_company_intelligence_repo,
        get_pending_generation_repo, get_career_insight_run_repo,
        get_skill_roadmap_repo, get_skill_roadmap_progress_repo, get_skill_roadmap_job_repo,
    )
    from exceptions import AppError
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
    from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
    from processing.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
    from career.infrastructure.repositories.sa_insight_repository import SQLAlchemyInsightRepository
    from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
    from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
    from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
    from processing.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
    from career.infrastructure.repositories.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
    from shared.presentation.api.root_router import api_router

    app = FastAPI(title="Test API")

    @app.exception_handler(AppError)
    async def app_error_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.detail, "details": getattr(exc, "details", None)}},
        )

    def override_get_session():
        yield sa_session

    def override_get_session_sync():
        return sa_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_session_sync] = override_get_session_sync
    app.dependency_overrides[get_job_repo] = lambda: SQLAlchemyJobRepository(sa_session)
    app.dependency_overrides[get_skill_repo] = lambda: SQLAlchemySkillRepository(sa_session)
    app.dependency_overrides[get_company_repo] = lambda: SQLAlchemyCompanyRepository(sa_session)
    app.dependency_overrides[get_pending_repo] = lambda: SQLAlchemyPendingRepository(sa_session)
    app.dependency_overrides[get_insight_repo] = lambda: SQLAlchemyInsightRepository(sa_session)
    app.dependency_overrides[get_preference_repo] = lambda: SQLAlchemyPreferenceRepository(sa_session)
    app.dependency_overrides[get_summary_repo] = lambda: SQLAlchemySummaryRepository(sa_session)
    app.dependency_overrides[get_resume_repo] = lambda: SQLAlchemyResumeRepository(sa_session)
    app.dependency_overrides[get_company_link_repo] = lambda: SQLAlchemyCompanyLinkRepository(sa_session)
    app.dependency_overrides[get_company_intelligence_repo] = lambda: SQLAlchemyCompanyIntelligenceRepository(sa_session)
    app.dependency_overrides[get_pending_generation_repo] = lambda: SQLAlchemyPendingGenerationRepository(sa_session)
    app.dependency_overrides[get_career_insight_run_repo] = lambda: SQLAlchemyCareerInsightRunRepository(sa_session)
    app.dependency_overrides[get_skill_roadmap_repo] = lambda: SQLAlchemySkillRoadmapRepository(sa_session)
    app.dependency_overrides[get_skill_roadmap_progress_repo] = lambda: SQLAlchemySkillRoadmapProgressRepository(sa_session)
    app.dependency_overrides[get_skill_roadmap_job_repo] = lambda: SQLAlchemySkillRoadmapJobRepository(sa_session)
    app.include_router(api_router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
