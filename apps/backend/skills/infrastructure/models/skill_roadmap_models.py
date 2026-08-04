"""SQLAlchemy ORM models for skill roadmaps (skill schema)."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database.sqlalchemy_config import Base


class SkillRoadmapModel(Base):
    __tablename__ = "skill_roadmaps"
    __table_args__ = {"schema": "skill"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("skill.skill_roadmaps.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    numbering: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    children: Mapped[list["SkillRoadmapModel"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped[Optional["SkillRoadmapModel"]] = relationship(
        back_populates="children", remote_side="SkillRoadmapModel.id"
    )


class SkillRoadmapProgressModel(Base):
    __tablename__ = "skill_roadmap_progress"
    __table_args__ = (UniqueConstraint("roadmap_id"), {"schema": "skill"})

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skill.skill_roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)


class SkillRoadmapJobModel(Base):
    __tablename__ = "skill_roadmap_jobs"
    __table_args__ = {"schema": "skill"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    job_type: Mapped[str] = mapped_column(String, default="generate")
    status: Mapped[str] = mapped_column(String, default="queued")
    step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=4)
    message: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
