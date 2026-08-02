"""SQLAlchemy ORM models for the jobs table."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class JobModel(Base):
    """SQLAlchemy model for the jobs table."""

    __tablename__ = "jobs"
    __table_args__ = {"schema": "job"}

    num: Mapped[int] = mapped_column(Integer, primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid7()))
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    match: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    score: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    success: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    salary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stack: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    visa: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    applicants: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    posted: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    action: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_type: Mapped[str] = mapped_column(String, default="On-site")
    workflow_log: Mapped[str] = mapped_column(Text, default="[]")
    locations: Mapped[str] = mapped_column(Text, default="[]")
    deleted: Mapped[int] = mapped_column(Integer, default=0)
    employment_type: Mapped[str] = mapped_column(String, default="Full-time")
    work_types: Mapped[str] = mapped_column(Text, default="[]")
    raw_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adv_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    see_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    apply_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    apply_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    response_time: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    response_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rescoring: Mapped[int] = mapped_column(Integer, default=0)
    links: Mapped[str] = mapped_column(Text, default="[]")
    source: Mapped[Optional[str]] = mapped_column(String, default="web")
    status: Mapped[str] = mapped_column(String, default="imported")
    queue_order: Mapped[int] = mapped_column(Integer, default=0)
    current_node: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    progress_pct: Mapped[float] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_step: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    failure_timestamp: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
