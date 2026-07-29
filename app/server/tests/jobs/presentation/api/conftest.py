"""Conftest for integration API tests."""
import sys
import os
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model
import career.infrastructure.models.insight_model
import shared.infrastructure.database.models.misc_models


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


@asynccontextmanager
async def no_lifespan(app):
    yield


def _build_app(sa_session):
    from app.server.entrypoints.api import create_app
    from dependencies import (
        get_session, get_session_sync, get_job_repo, get_skill_repo,
        get_company_repo, get_pending_repo, get_insight_repo, get_preference_repo,
        get_summary_repo, get_resume_repo, get_company_link_repo, get_company_intelligence_repo,
        get_pending_generation_repo, get_career_insight_run_repo,
        get_skill_roadmap_repo, get_skill_roadmap_progress_repo, get_skill_roadmap_job_repo,
    )
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
    from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
    from shared.infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from career.infrastructure.repositories.sa_insight_repository import SQLAlchemyInsightRepository
    from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
    from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
    from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
    from shared.infrastructure.database.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
    from career.infrastructure.repositories.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository

    app = create_app()
    app.router.lifespan_context = no_lifespan

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

    return app


@pytest.fixture
def client(test_db):
    app = _build_app(test_db)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
