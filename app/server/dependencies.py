"""FastAPI dependency injection functions.

These functions provide dependencies for route handlers via FastAPI's Depends() system.
"""

import sqlite3
from typing import Generator

from config import DB_PATH


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


# ── Repository Dependencies ──────────────────────────────────────

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


# ── FastAPI Depends() wrappers ──────────────────────────────────

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
