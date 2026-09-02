"""SQLAlchemy ORM models for the skills tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database.sqlalchemy_config import Base
from skills.domain.slug_utils import slugify


class SkillModel(Base):
    __tablename__ = "skills"
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_skill_name_user"),
        UniqueConstraint("slug", "user_id", name="uq_skill_slug_user"),
        {"schema": "skill"},
    )

    def __init__(self, **kwargs):
        name = kwargs.get("name")
        if "slug" not in kwargs and name:
            kwargs["slug"] = slugify(name)
        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, nullable=False, index=True)
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
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, default="")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    aliases: Mapped[list["SkillAliasModel"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    mentions: Mapped[list["SkillMentionModel"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    notes: Mapped[list["SkillNoteModel"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )

    links: Mapped[list["SkillLinkModel"]] = relationship(
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


class SkillCategoryModel(Base):
    """Category catalog for the skill taxonomy.

    Seeded with the canonical categories; users can add new ones. Each skill may
    belong to many categories via SkillCategoryLinkModel.
    """

    __tablename__ = "skill_categories"
    __table_args__ = {"schema": "skill"}

    def __init__(self, **kwargs):
        name = kwargs.get("name")
        if "slug" not in kwargs and name:
            kwargs["slug"] = slugify(name)
        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)


class SkillCategoryLinkModel(Base):
    """Many-to-many association between skills and categories.

    Both FKs stay inside the skill schema (same bounded context), so real
    foreign keys are allowed (AGENTS.md rule 15).
    """

    __tablename__ = "skill_category_links"
    __table_args__ = (
        UniqueConstraint("skill_id", "category_id"),
        {"schema": "skill"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skill_categories.id"), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)


class SkillBreakdownModel(Base):
    """A composite skill broken into atomic child skills.

    Records that ``origin_skill_id`` decomposes into ``child_skill_id``. The
    map feeds skill extraction so jobs mentioning the composite also surface
    its children. The origin is soft-hidden after a breakdown; this table
    keeps the lineage. Both FKs stay inside the skill schema (rule 15).
    """

    __tablename__ = "skill_breakdowns"
    __table_args__ = (
        UniqueConstraint("origin_skill_id", "child_skill_id"),
        {"schema": "skill"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin_skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    child_skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    origin_skill: Mapped["SkillModel"] = relationship(foreign_keys=[origin_skill_id])
    child_skill: Mapped["SkillModel"] = relationship(foreign_keys=[child_skill_id])


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


class SkillNoteModel(Base):
    """Free-text activity note on a skill."""
    __tablename__ = "skill_notes"
    __table_args__ = {"schema": "skill"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    skill: Mapped["SkillModel"] = relationship(back_populates="notes")


class SkillLinkModel(Base):
    """A titled resource link on a skill (documentation, tutorial, etc.)."""
    __tablename__ = "skill_links"
    __table_args__ = {"schema": "skill"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skill.skills.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    skill: Mapped["SkillModel"] = relationship(back_populates="links")