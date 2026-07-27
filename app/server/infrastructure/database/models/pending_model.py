"""SQLAlchemy ORM models for the pending tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.sqlalchemy_config import Base


class PendingJobModel(Base):
    """SQLAlchemy model for the pending_jobs table."""

    __tablename__ = "pending_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    source: Mapped[str] = mapped_column(String, default="cli")
    status: Mapped[str] = mapped_column(String, default="queued")
    version: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, default="[]")
    links: Mapped[str] = mapped_column(Text, default="[]")
    step_fetch: Mapped[int] = mapped_column(Integer, default=0)
    step_analyze: Mapped[int] = mapped_column(Integer, default=0)
    step_resume: Mapped[int] = mapped_column(Integer, default=0)
    step_cover: Mapped[int] = mapped_column(Integer, default=0)
    step_db: Mapped[int] = mapped_column(Integer, default=0)
    step_done: Mapped[int] = mapped_column(Integer, default=0)
    job_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workflow_log: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    queue_order: Mapped[int] = mapped_column(Integer, default=0)
    step_extract_raw: Mapped[int] = mapped_column(Integer, default=0)
    step_extract_struct: Mapped[int] = mapped_column(Integer, default=0)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class PendingCompanyModel(Base):
    """SQLAlchemy model for the pending_companies table."""

    __tablename__ = "pending_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_text: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="[]")
    input_type: Mapped[str] = mapped_column(String, default="url")
    source: Mapped[str] = mapped_column(String, default="web")
    status: Mapped[str] = mapped_column(String, default="pending")
    version: Mapped[int] = mapped_column(Integer, default=1)
    step_fetch: Mapped[int] = mapped_column(Integer, default=0)
    step_extract: Mapped[int] = mapped_column(Integer, default=0)
    step_analyze: Mapped[int] = mapped_column(Integer, default=0)
    step_save: Mapped[int] = mapped_column(Integer, default=0)
    step_done: Mapped[int] = mapped_column(Integer, default=0)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workflow_log: Mapped[str] = mapped_column(Text, default="[]")
    links: Mapped[str] = mapped_column(Text, default="[]")
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)


class PendingGenerationModel(Base):
    """SQLAlchemy model for the pending_generations table."""

    __tablename__ = "pending_generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_num: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="queued")
    step_prepare: Mapped[int] = mapped_column(Integer, default=0)
    step_context: Mapped[int] = mapped_column(Integer, default=0)
    step_generate: Mapped[int] = mapped_column(Integer, default=0)
    step_save: Mapped[int] = mapped_column(Integer, default=0)
    step_done: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
