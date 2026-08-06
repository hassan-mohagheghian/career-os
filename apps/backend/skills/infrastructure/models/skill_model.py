"""SQLAlchemy ORM models for the skills tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database.sqlalchemy_config import Base


class SkillModel(Base):
    __tablename__ = "skills"
    __table_args__ = {"schema": "skill"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    ml: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    roles: Mapped[str] = mapped_column(String, default="")
    path: Mapped[str] = mapped_column(String, default="")
    source: Mapped[str] = mapped_column(String, default="service")
    hidden: Mapped[int] = mapped_column(Integer, default=0)
    pinned: Mapped[int] = mapped_column(Integer, default=0)
    merged_into: Mapped[str] = mapped_column(String, default="")
    category: Mapped[str] = mapped_column(String, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    market_relevance: Mapped[float] = mapped_column(Float, default=0)
    evidence: Mapped[str] = mapped_column(Text, default="[]")
    source_type: Mapped[str] = mapped_column(String, default="service")
    tags: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    aliases: Mapped[list["SkillAliasModel"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    mentions: Mapped[list["SkillMentionModel"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class SkillAliasModel(Base):
    __tablename__ = "skill_aliases"
    __table_args__ = {"schema": "skill"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    alias_name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    skill: Mapped["SkillModel"] = relationship(back_populates="aliases")


class SkillRelationshipModel(Base):
    __tablename__ = "skill_relationships"
    __table_args__ = (
        UniqueConstraint("skill_name", "related_name", "relation_type"),
        {"schema": "skill"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_name: Mapped[str] = mapped_column(String, nullable=False)
    related_name: Mapped[str] = mapped_column(String, nullable=False)
    relation_type: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0)


class SkillMentionModel(Base):
    """A link between a skill and the source (job/company) that requested it.

    Lets us count demand for a skill without duplicating skill rows: each row
    records that a processed job or company mentioned the skill.
    """

    __tablename__ = "skill_mentions"
    __table_args__ = (
        UniqueConstraint("skill_id", "source_type", "source_id"),
        {"schema": "skill"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="")
    evidence: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    skill: Mapped["SkillModel"] = relationship(back_populates="mentions")