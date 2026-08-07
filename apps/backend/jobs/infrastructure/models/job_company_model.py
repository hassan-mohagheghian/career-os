"""SQLAlchemy ORM model for the job_companies table.

Associates a job with every company mentioned in its posting — the hiring
company (role="hiring") and any recruiting / staffing / agency companies
(role="recruiter"). Rows are replaced on re-processing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class JobCompanyModel(Base):
    """SQLAlchemy model for the job_companies table."""

    __tablename__ = "job_companies"
    __table_args__ = {"schema": "job"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("job.jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String, nullable=False, default="hiring")
    company_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
