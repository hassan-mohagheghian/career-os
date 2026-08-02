"""Database infrastructure for the background worker.

Reuses the server's SQLAlchemy engine, session factory, and models.
No duplication of ORM mappings or domain models.
"""

import os
import sys

_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from shared.infrastructure.database.sqlalchemy_config import (
    Base,
    engine,
    SessionLocal,
)
from shared.infrastructure.database.session import get_session_sync, get_session


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_session",
    "get_session_sync",
]
