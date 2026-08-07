"""SQLAlchemy ORM models for the candidate schema.

Cross-context links are logical references only (AGENTS.md rule 15): the only
one here is ``candidate_skills.skill_id`` -> ``skill.skills``, stored as a
plain Integer column with NO ForeignKey. FKs exist only within the ``candidate``
schema (aggregate + children).
"""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.database.sqlalchemy_config import Base


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CandidateModel(Base):
    __tablename__ = "candidates"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="")
    headline: Mapped[str] = mapped_column(String, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateProfileModel(Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidates.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String, default="")
    title: Mapped[str] = mapped_column(String, default="")
    headline: Mapped[str] = mapped_column(String, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateSourceModel(Base):
    __tablename__ = "candidate_sources"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, default="pending")
    error: Mapped[str] = mapped_column(Text, default="")
    processed_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateSkillModel(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    skill_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String, default="")
    level: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[str] = mapped_column(String, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0)
    origin: Mapped[str] = mapped_column(String, default="explicit")
    years_of_experience: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_used: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateExperienceModel(Base):
    __tablename__ = "candidate_experiences"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    company: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="")
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    duration_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    highlights: Mapped[str] = mapped_column(Text, default="[]")
    skills: Mapped[str] = mapped_column(Text, default="[]")
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateProjectModel(Base):
    __tablename__ = "candidate_projects"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="")
    skills: Mapped[str] = mapped_column(Text, default="[]")
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateEducationModel(Base):
    __tablename__ = "candidate_educations"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    institution: Mapped[str] = mapped_column(String, default="")
    degree: Mapped[str] = mapped_column(String, default="")
    field: Mapped[str] = mapped_column(String, default="")
    start_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateCertificateModel(Base):
    __tablename__ = "candidate_certificates"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, default="")
    issuer: Mapped[str] = mapped_column(String, default="")
    issue_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    credential_url: Mapped[str] = mapped_column(String, default="")
    evidence: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateInterestModel(Base):
    __tablename__ = "candidate_interests"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateLanguageModel(Base):
    __tablename__ = "candidate_languages"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, default="")
    proficiency: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)


class CandidateProfileVersionModel(Base):
    __tablename__ = "candidate_profile_versions"
    __table_args__ = {"schema": "candidate"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile_id: Mapped[str] = mapped_column(
        String, ForeignKey("candidate.candidate_profiles.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    snapshot: Mapped[str] = mapped_column(Text, default="{}")
    source_versions: Mapped[str] = mapped_column(Text, default="{}")
    change_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)
