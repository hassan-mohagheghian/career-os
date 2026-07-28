"""SQLAlchemy ORM models for summaries, resumes, and other tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database.sqlalchemy_config import Base


class SummaryModel(Base):
    """SQLAlchemy model for the summaries table."""

    __tablename__ = "summaries"

    num: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    match: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    score: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stack: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    resumeFit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class ResumeModel(Base):
    """SQLAlchemy model for the resumes table."""

    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    job_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class SkillRoadmapModel(Base):
    """SQLAlchemy model for the skill_roadmaps table."""

    __tablename__ = "skill_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("skill_roadmaps.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    numbering: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    # Self-referential relationship
    children: Mapped[list["SkillRoadmapModel"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan"
    )
    parent: Mapped[Optional["SkillRoadmapModel"]] = relationship(
        back_populates="children", remote_side="SkillRoadmapModel.id"
    )


class SkillRoadmapProgressModel(Base):
    """SQLAlchemy model for the skill_roadmap_progress table."""

    __tablename__ = "skill_roadmap_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skill_roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    completed: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("roadmap_id"),)


class SkillRoadmapJobModel(Base):
    """SQLAlchemy model for the skill_roadmap_jobs table."""

    __tablename__ = "skill_roadmap_jobs"

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


class PreferenceModel(Base):
    """SQLAlchemy model for the preferences table."""

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    rule_type: Mapped[str] = mapped_column(String, default="job")
    scope: Mapped[str] = mapped_column(String, default="JOB")
    key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    score_weight: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("category", "key"),)


class DashboardInsightModel(Base):
    """SQLAlchemy model for the dashboard_insights table."""

    __tablename__ = "dashboard_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)


class AnalysisRunModel(Base):
    """SQLAlchemy model for the analysis_runs table."""

    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    analysis_json: Mapped[str] = mapped_column(Text, nullable=False)


class TechLearningModel(Base):
    """SQLAlchemy model for the tech_learning table."""

    __tablename__ = "tech_learning"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pl: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    jobs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jd: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class CityModel(Base):
    """SQLAlchemy model for the cities table."""

    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jobs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
