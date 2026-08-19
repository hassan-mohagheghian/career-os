"""SQLAlchemy ORM model for the placeholders schema.

The Placeholders context owns its own PostgreSQL schema. It stores simple
key/value personal details used to fill ``{{token}}`` placeholders in generated
documents. There are no cross-context references (no FKs to other schemas).
"""

from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class PlaceholderModel(Base):
    __tablename__ = "placeholders"
    __table_args__ = {"schema": "placeholders"}

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


__all__ = ["PlaceholderModel"]