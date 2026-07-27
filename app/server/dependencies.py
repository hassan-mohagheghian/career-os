"""FastAPI dependency injection functions.

These functions provide dependencies for route handlers via FastAPI's Depends() system.
Supports both legacy sqlite3 connections and new SQLAlchemy sessions.
"""

import sqlite3
from typing import Generator

from config import DB_PATH


# ── Legacy sqlite3 dependencies (kept for backward compatibility) ──

def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection for the request lifetime."""
    conn = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
    finally:
        conn.close()


def get_db_sync() -> sqlite3.Connection:
    """Get a synchronous database connection (for non-async contexts)."""
    conn = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ── SQLAlchemy Session Dependencies ──────────────────────────────

def get_sqlalchemy_session() -> Generator:
    """Get a SQLAlchemy session for the request lifetime.

    Yields a Session and auto-commits on success, rolls back on error.
    """
    from infrastructure.database.sqlalchemy_config import SessionLocal
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_sqlalchemy_session_sync():
    """Get a synchronous SQLAlchemy session (for non-async contexts)."""
    from infrastructure.database.sqlalchemy_config import SessionLocal
    return SessionLocal()


# ── Legacy Repository Dependencies ──────────────────────────────

def get_job_repository(db: sqlite3.Connection = None) -> "JobRepository":
    """Get job repository instance."""
    from infrastructure.database.job_repository import JobRepository
    if db is None:
        db = get_db_sync()
    return JobRepository(db)


def get_skill_repository(db: sqlite3.Connection = None) -> "SkillRepository":
    """Get skill repository instance."""
    from infrastructure.database.skill_repository import SkillRepository
    if db is None:
        db = get_db_sync()
    return SkillRepository(db)


def get_company_repository(db: sqlite3.Connection = None) -> "CompanyRepository":
    """Get company repository instance."""
    from infrastructure.database.company_repository import CompanyRepository
    if db is None:
        db = get_db_sync()
    return CompanyRepository(db)


def get_pending_repository(db: sqlite3.Connection = None) -> "PendingRepository":
    """Get pending repository instance."""
    from infrastructure.database.pending_repository import PendingRepository
    if db is None:
        db = get_db_sync()
    return PendingRepository(db)


def get_insight_repository(db: sqlite3.Connection = None) -> "InsightRepository":
    """Get insight repository instance."""
    from infrastructure.database.insight_repository import InsightRepository
    if db is None:
        db = get_db_sync()
    return InsightRepository(db)


# ── SQLAlchemy Repository Dependencies ───────────────────────────

def get_sa_job_repository():
    """FastAPI dependency for SQLAlchemy job repository."""
    from infrastructure.database.sa_job_repository import SQLAlchemyJobRepository
    from fastapi import Depends
    session = Depends(get_sqlalchemy_session)
    return SQLAlchemyJobRepository(session)


def get_sa_skill_repository():
    """FastAPI dependency for SQLAlchemy skill repository."""
    from infrastructure.database.sa_skill_repository import SQLAlchemySkillRepository
    from fastapi import Depends
    session = Depends(get_sqlalchemy_session)
    return SQLAlchemySkillRepository(session)


def get_sa_company_repository():
    """FastAPI dependency for SQLAlchemy company repository."""
    from infrastructure.database.sa_company_repository import SQLAlchemyCompanyRepository
    from fastapi import Depends
    session = Depends(get_sqlalchemy_session)
    return SQLAlchemyCompanyRepository(session)


def get_sa_pending_repository():
    """FastAPI dependency for SQLAlchemy pending repository."""
    from infrastructure.database.sa_pending_repository import SQLAlchemyPendingRepository
    from fastapi import Depends
    session = Depends(get_sqlalchemy_session)
    return SQLAlchemyPendingRepository(session)


def get_sa_insight_repository():
    """FastAPI dependency for SQLAlchemy insight repository."""
    from infrastructure.database.sa_insight_repository import SQLAlchemyInsightRepository
    from fastapi import Depends
    session = Depends(get_sqlalchemy_session)
    return SQLAlchemyInsightRepository(session)


# ── FastAPI Depends() wrappers (legacy) ─────────────────────────

def DependsJobRepository():
    """FastAPI dependency for job repository."""
    from infrastructure.database.job_repository import JobRepository
    from fastapi import Depends
    db = Depends(get_db)
    return JobRepository(db)


def DependsSkillRepository():
    """FastAPI dependency for skill repository."""
    from infrastructure.database.skill_repository import SkillRepository
    from fastapi import Depends
    db = Depends(get_db)
    return SkillRepository(db)


def DependsCompanyRepository():
    """FastAPI dependency for company repository."""
    from infrastructure.database.company_repository import CompanyRepository
    from fastapi import Depends
    db = Depends(get_db)
    return CompanyRepository(db)
