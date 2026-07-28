"""SQLAlchemy ORM models for the career insight tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class CareerInsightModel(Base):
    """SQLAlchemy model for the career_insights table."""

    __tablename__ = "career_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)


class CareerInsightRunModel(Base):
    """SQLAlchemy model for the career_insight_runs table."""

    __tablename__ = "career_insight_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    insight_type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column("metadata", Text, default="{}")
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
