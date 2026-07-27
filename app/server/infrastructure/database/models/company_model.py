"""SQLAlchemy ORM models for the company tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.sqlalchemy_config import Base


class CompanyModel(Base):
    """SQLAlchemy model for the companies table."""

    __tablename__ = "companies"

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
    processing_status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extracted_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(Text, default=datetime.utcnow)

    # Relationships
    company: Mapped["CompanyModel"] = relationship(back_populates="links")
