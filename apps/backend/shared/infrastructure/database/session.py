"""Shared SQLAlchemy session management.

Provides get_session and get_session_sync for dependency injection
across all bounded contexts.
"""

from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session


def get_session() -> Generator[Session, None, None]:
    """Get a SQLAlchemy session for the request lifetime.

    Yields a Session and auto-commits on success, rolls back on error.
    Used as a FastAPI dependency.
    """
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_sync() -> Session:
    """Get a synchronous SQLAlchemy session (for non-async contexts).

    Caller is responsible for closing the session.
    """
    from shared.infrastructure.database.sqlalchemy_config import SessionLocal
    return SessionLocal()
