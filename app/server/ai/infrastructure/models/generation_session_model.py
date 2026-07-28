"""SQLAlchemy ORM model for generation sessions."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class GenerationSessionModel(Base):
    """SQLAlchemy model for the ai_generation_sessions table."""

    __tablename__ = "ai_generation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    current_stage: Mapped[str] = mapped_column(String(50), default="")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    errors: Mapped[str] = mapped_column(Text, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
