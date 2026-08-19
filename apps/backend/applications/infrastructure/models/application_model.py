"""SQLAlchemy ORM models for the application schema.

The Applications context owns its own PostgreSQL schema. Cross-context
references are logical only (AGENTS.md rule 15): ``applications.job_id`` is a
plain column with NO ForeignKey into the ``job`` schema. FKs exist only within
the ``application`` schema (aggregate + children).
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _new_id() -> str:
    return str(uuid.uuid7())


class ApplicationModel(Base):
    __tablename__ = "applications"
    __table_args__ = {"schema": "application"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    job_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="seen")
    applied_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class ApplicationStatusEventModel(Base):
    __tablename__ = "application_status_timeline"
    __table_args__ = {"schema": "application"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("application.applications.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    changed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class ApplicationFollowUpModel(Base):
    __tablename__ = "application_follow_ups"
    __table_args__ = {"schema": "application"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("application.applications.id"), nullable=False, index=True
    )
    scheduled_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    completed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class ApplicationDocumentModel(Base):
    __tablename__ = "application_documents"
    __table_args__ = {"schema": "application"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("application.applications.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)
