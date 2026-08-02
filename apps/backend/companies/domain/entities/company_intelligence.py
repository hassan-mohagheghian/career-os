"""CompanyIntelligence entity — intelligence analysis data for a company."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.domain.entity import BaseEntity


class CompanyIntelligence(BaseEntity):
    """Company intelligence analysis."""

    def __init__(
        self,
        id: int | None = None,
        company_id: int | None = None,
        overview: str | None = None,
        culture_analysis: str | None = None,
        international_analysis: str | None = None,
        career_analysis: str | None = None,
        benefits_analysis: str | None = None,
        visa_analysis: str | None = None,
        technology_analysis: str | None = None,
        recommendation: str | None = None,
        scores: str | None = None,
        raw_source_data: str | None = None,
        generated_at: datetime | None = None,
    ):
        super().__init__(id=id, created_at=generated_at)
        self.company_id = company_id
        self.overview = overview
        self.culture_analysis = culture_analysis
        self.international_analysis = international_analysis
        self.career_analysis = career_analysis
        self.benefits_analysis = benefits_analysis
        self.visa_analysis = visa_analysis
        self.technology_analysis = technology_analysis
        self.recommendation = recommendation
        self.scores = scores
        self.raw_source_data = raw_source_data

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "overview": self.overview,
            "culture_analysis": self.culture_analysis,
            "international_analysis": self.international_analysis,
            "career_analysis": self.career_analysis,
            "benefits_analysis": self.benefits_analysis,
            "visa_analysis": self.visa_analysis,
            "technology_analysis": self.technology_analysis,
            "recommendation": self.recommendation,
            "scores": self.scores,
            "raw_source_data": self.raw_source_data,
            "generated_at": self.created_at.isoformat() if self.created_at else None,
        }
