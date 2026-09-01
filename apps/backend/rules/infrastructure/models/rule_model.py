"""SQLAlchemy ORM model for scoring rules (shared schema)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


class RuleModel(Base):
    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("category", "key", "user_id"), {"schema": "shared"})

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    rule_type: Mapped[str] = mapped_column(String, default="job")
    scope: Mapped[str] = mapped_column(String, default="JOB")
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, default="")
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
