"""SQLAlchemy ORM models for the company tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database.sqlalchemy_config import Base


class CompanyModel(Base):
    """SQLAlchemy model for the companies table."""

    __tablename__ = "companies"
    __table_args__ = {"schema": "company"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    founded_year: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    headquarters_full: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    countries_of_operation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    funding_stage: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    funding_amount: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    products: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_environment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="[]")
    links: Mapped[str] = mapped_column(Text, default="[]")
    source: Mapped[Optional[str]] = mapped_column(String, default="web")
    workflow_log: Mapped[str] = mapped_column(Text, default="[]")
    input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_type: Mapped[Optional[str]] = mapped_column(String, default="url")
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    queue_order: Mapped[int] = mapped_column(Integer, default=0)
    current_node: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    progress_pct: Mapped[float] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_step: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    failure_timestamp: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    intelligence: Mapped[Optional["CompanyIntelligenceModel"]] = relationship(
        back_populates="company", uselist=False
    )
    links: Mapped[list["CompanyLinkModel"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class CompanyIntelligenceModel(Base):
    """SQLAlchemy model for the company_intelligence table."""

    __tablename__ = "company_intelligence"
    __table_args__ = {"schema": "company"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("company.companies.id"), nullable=False)
    overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    culture_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    international_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    career_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visa_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technology_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_source_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    # Relationships
    company: Mapped["CompanyModel"] = relationship(back_populates="intelligence")


class CompanyLinkModel(Base):
    """SQLAlchemy model for the company_links table."""

    __tablename__ = "company_links"
    __table_args__ = {"schema": "company"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("company.companies.id"), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extracted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    # Relationships
    company: Mapped["CompanyModel"] = relationship(back_populates="links")
