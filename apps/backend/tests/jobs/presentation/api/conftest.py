"""Conftest for integration API tests."""
import sys
import os
import re
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv()

from shared.infrastructure.database.sqlalchemy_config import Base, ensure_schemas
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model
import jobs.infrastructure.models.misc_models
import processing.infrastructure.models.processing_execution_model


def _get_test_db_url() -> str:
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError("DATABASE_URL is required. Set it to a PostgreSQL connection string.")
    m = re.match(r'^(postgresql(?:\+psycopg)?://[^/]+)/(.+)$', url)
    if not m:
        raise RuntimeError(f"Could not parse DATABASE_URL: {url}")
    return f"{m.group(1)}/{m.group(2)}_test"


TEST_DB_URL = os.environ.get('TEST_DATABASE_URL') or _get_test_db_url()


def _ensure_test_database():
    url = os.environ.get('DATABASE_URL')
    m = re.match(r'^(postgresql(?:\+psycopg)?://[^/]+)/.+$', url)
    admin_url = m.group(1) + '/postgres'
    db_name = TEST_DB_URL.split('/')[-1]
    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE {db_name}"))
        admin_engine.dispose()
    except Exception:
        pass


_ensure_test_database()


@pytest.fixture
def test_db(_engine):
    connection = _engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@asynccontextmanager
async def no_lifespan(app):
    yield


def _build_app(sa_session):
    from apps.backend.entrypoints.api import create_app
    from dependencies import (
        get_session, get_session_sync, get_job_repo, get_skill_repo,
        get_company_repo, get_pending_repo, get_rule_repo,
        get_summary_repo, get_company_link_repo, get_company_intelligence_repo,
        get_processing_execution_repo,
    )
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
    from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
    from rules.infrastructure.repositories.sa_rule_repository import SQLAlchemyRuleRepository
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
    from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
    from processing.infrastructure.repositories.sa_processing_execution_repository import SQLAlchemyProcessingExecutionRepository

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
    app.dependency_overrides[get_pending_repo] = lambda: SQLAlchemyJobRepository(sa_session)
    app.dependency_overrides[get_rule_repo] = lambda: SQLAlchemyRuleRepository(sa_session)
    app.dependency_overrides[get_summary_repo] = lambda: SQLAlchemySummaryRepository(sa_session)
    app.dependency_overrides[get_company_link_repo] = lambda: SQLAlchemyCompanyLinkRepository(sa_session)
    app.dependency_overrides[get_company_intelligence_repo] = lambda: SQLAlchemyCompanyIntelligenceRepository(sa_session)
    app.dependency_overrides[get_processing_execution_repo] = lambda: SQLAlchemyProcessingExecutionRepository(sa_session)

    return app


@pytest.fixture
def client(test_db):
    app = _build_app(test_db)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
