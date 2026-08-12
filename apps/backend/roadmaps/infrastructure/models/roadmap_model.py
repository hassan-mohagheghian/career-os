"""SQLAlchemy ORM models for the roadmap schema.

The Roadmaps context owns its own PostgreSQL schema. Cross-context references
are logical only (AGENTS.md rule 15): ``roadmaps.application_id`` and
``roadmap_skill_links.skill_id`` are plain columns with NO ForeignKey into the
``application`` / ``skill`` schemas. FKs exist only within the ``roadmap``
schema (aggregate + children).
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


class RoadmapModel(Base):
    __tablename__ = "roadmaps"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    goal_type: Mapped[str] = mapped_column(String, nullable=False, default="CUSTOM")
    source: Mapped[str] = mapped_column(String, nullable=False, default="MANUAL")
    application_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)


class RoadmapGoalModel(Base):
    __tablename__ = "roadmap_goals"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    roadmap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap.roadmaps.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String, nullable=False, default="CUSTOM")
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    target_company_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    target_skill_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)


class RoadmapMilestoneModel(Base):
    __tablename__ = "roadmap_milestones"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    roadmap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap.roadmaps.id"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="NOT_STARTED")
    priority: Mapped[str] = mapped_column(String, nullable=False, default="MEDIUM")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)


class RoadmapTaskModel(Base):
    __tablename__ = "roadmap_tasks"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    milestone_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_milestones.id"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String, nullable=False, default="NOT_STARTED")
    priority: Mapped[str] = mapped_column(String, nullable=False, default="MEDIUM")
    estimated_effort: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    success_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)


class RoadmapSkillLinkModel(Base):
    __tablename__ = "roadmap_skill_links"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    roadmap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap.roadmaps.id"), nullable=False, index=True
    )
    milestone_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_milestones.id"), nullable=True
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_tasks.id"), nullable=True
    )
    skill_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)


class RoadmapNoteModel(Base):
    __tablename__ = "roadmap_notes"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    roadmap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap.roadmaps.id"), nullable=False, index=True
    )
    milestone_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_milestones.id"), nullable=True
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_tasks.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)


class RoadmapResourceModel(Base):
    __tablename__ = "roadmap_resources"
    __table_args__ = {"schema": "roadmap"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    roadmap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap.roadmaps.id"), nullable=False, index=True
    )
    milestone_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_milestones.id"), nullable=True
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap.roadmap_tasks.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    type: Mapped[str] = mapped_column(String, nullable=False, default="OTHER")
    status: Mapped[str] = mapped_column(String, nullable=False, default="PLANNED")
    source: Mapped[str] = mapped_column(String, nullable=False, default="USER")
    created_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False, default=_now_iso)