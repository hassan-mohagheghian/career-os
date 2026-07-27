"""SQLAlchemy engine, session, and Base configuration.

This module provides:
- SQLAlchemy 2.x declarative Base
- Engine creation with SQLite-specific settings
- Session factory for request-scoped sessions
- FastAPI dependency injection for database sessions
"""

from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DB_PATH


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy ORM models."""
    pass


# SQLite-specific engine configuration
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 15,
    },
    pool_pre_ping=True,
)


# SQLite PRAGMA settings applied to every new connection
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    The session is automatically closed after the request completes.
    """
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
    """Get a synchronous database session (for non-async contexts)."""
    return SessionLocal()
