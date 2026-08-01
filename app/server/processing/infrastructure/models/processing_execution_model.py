from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class ProcessingExecutionModel(Base):
    __tablename__ = "processing_executions"
    __table_args__ = {"schema": "processing"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    workflow_progress: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
