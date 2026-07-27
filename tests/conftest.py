"""Shared test fixtures."""

import sqlite3
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _create_tables(conn: sqlite3.Connection):
    """Create all database tables for testing."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            num INTEGER PRIMARY KEY,
            company TEXT, role TEXT, location TEXT, match TEXT,
            score TEXT, success TEXT, salary TEXT, stack TEXT, visa TEXT,
            applicants TEXT, posted TEXT, industry TEXT,
            domain TEXT, notes TEXT, action TEXT, url TEXT,
            work_type TEXT DEFAULT 'On-site',
            workflow_log TEXT DEFAULT '[]',
            locations TEXT DEFAULT '[]',
            deleted INTEGER DEFAULT 0,
            employment_type TEXT DEFAULT 'Full-time',
            work_types TEXT DEFAULT '[]',
            raw_description TEXT,
            structured_description TEXT,
            adv_at TEXT,
            see_at TEXT,
            apply_reason TEXT,
            fit_score INTEGER,
            success_score INTEGER,
            overall_score INTEGER,
            company_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            title TEXT,
            description TEXT,
            apply_time TEXT,
            response_time TEXT,
            response_status TEXT,
            rescoring INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS summaries (
            num INTEGER PRIMARY KEY,
            company TEXT, match TEXT, score TEXT,
            summary TEXT, stack TEXT, resumeFit TEXT, note TEXT, url TEXT
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT, role TEXT, content TEXT,
            version INTEGER DEFAULT 1,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            job_num INTEGER
        );

        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            level INTEGER DEFAULT 1,
            roles TEXT DEFAULT '',
            path TEXT DEFAULT '',
            source TEXT DEFAULT 'user',
            source_type TEXT DEFAULT 'user_input',
            category TEXT DEFAULT '',
            confidence REAL,
            market_relevance REAL,
            evidence TEXT,
            tags TEXT DEFAULT '[]',
            hidden INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS skill_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER,
            alias_name TEXT,
            normalized_name TEXT,
            FOREIGN KEY (skill_id) REFERENCES skills(id)
        );

        CREATE TABLE IF NOT EXISTS skill_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT,
            related_name TEXT,
            relation_type TEXT,
            confidence REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS skill_roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT,
            tree TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS skill_roadmap_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT,
            completed_nodes TEXT DEFAULT '[]',
            total_nodes INTEGER DEFAULT 0,
            percentage REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS skill_roadmap_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT,
            job_type TEXT,
            status TEXT DEFAULT 'queued',
            session_id TEXT
        );

        CREATE TABLE IF NOT EXISTS pending_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            source TEXT DEFAULT 'api',
            company TEXT,
            status TEXT DEFAULT 'pending',
            error TEXT,
            job_num INTEGER,
            version INTEGER DEFAULT 1,
            step_fetch INTEGER DEFAULT 0,
            step_validate INTEGER DEFAULT 0,
            step_extract_raw INTEGER DEFAULT 0,
            step_extract_struct INTEGER DEFAULT 0,
            step_analyze INTEGER DEFAULT 0,
            step_summary INTEGER DEFAULT 0,
            step_db INTEGER DEFAULT 0,
            step_done INTEGER DEFAULT 0,
            workflow_log TEXT DEFAULT '[]',
            notes TEXT,
            queue_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pending_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            input_text TEXT,
            notes TEXT DEFAULT '[]',
            input_type TEXT DEFAULT 'url',
            source TEXT DEFAULT 'web',
            status TEXT DEFAULT 'pending',
            error TEXT,
            step_fetch INTEGER DEFAULT 0,
            step_extract INTEGER DEFAULT 0,
            step_analyze INTEGER DEFAULT 0,
            step_save INTEGER DEFAULT 0,
            step_done INTEGER DEFAULT 0,
            company_id INTEGER,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            industry TEXT,
            city TEXT,
            country TEXT,
            logo_url TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS company_intelligence (
            company_id INTEGER PRIMARY KEY,
            overview TEXT,
            culture TEXT,
            tech_stack TEXT DEFAULT '[]',
            visa_policy TEXT,
            last_updated TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );

        CREATE TABLE IF NOT EXISTS company_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            url TEXT,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );

        CREATE TABLE IF NOT EXISTS career_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT,
            data TEXT DEFAULT '{}',
            status TEXT DEFAULT 'idle',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS career_insight_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT,
            status TEXT DEFAULT 'processing',
            session_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            name TEXT,
            value TEXT,
            weight REAL DEFAULT 1.0,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS generation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            status TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS dashboard_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tech_learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            priority INTEGER,
            pl TEXT, pc TEXT, sc TEXT, dc TEXT,
            usage INTEGER, uc TEXT,
            jobs TEXT, jd TEXT, reason TEXT, action TEXT
        );

        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            country TEXT
        );

        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            status TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
    """)


def _create_test_app(test_db: sqlite3.Connection) -> FastAPI:
    """Create a FastAPI app for testing (no lifespan, no startup tasks)."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

    from dependencies import get_db
    from exceptions import AppError
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Test API")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    @app.exception_handler(AppError)
    async def app_error_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.detail,
                    "details": getattr(exc, "details", None),
                }
            },
        )

    # Override database dependency
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    # Register routers
    from api.router import api_router
    app.include_router(api_router)

    # Health check
    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


@pytest.fixture
def test_db():
    """Create an in-memory test database with schema."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    _create_tables(conn)

    yield conn
    conn.close()


@pytest.fixture
def client(test_db):
    """Create a sync test client with test database."""
    app = _create_test_app(test_db)

    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(test_db):
    """Create an async test client with test database."""
    app = _create_test_app(test_db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── SQLAlchemy Session Fixtures ──────────────────────────────────

@pytest.fixture
def sa_session():
    """Create a SQLAlchemy session for testing with in-memory SQLite."""
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from infrastructure.database.sqlalchemy_config import Base

    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    yield session
    session.close()
    engine.dispose()
