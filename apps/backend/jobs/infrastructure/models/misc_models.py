"""SQLAlchemy ORM models for summaries and resumes (job schema)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class SummaryModel(Base):
    __tablename__ = "summaries"
    __table_args__ = {"schema": "job"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    match: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    score: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stack: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resumeFit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class ResumeModel(Base):
    __tablename__ = "resumes"
    __table_args__ = {"schema": "job"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
