"""Domain-to-database mapping for the Companies context.

Converts between domain dictionaries and SQLAlchemy ORM models in the
infrastructure layer, keeping the domain layer clean of persistence concerns.
"""

from typing import Any
from datetime import datetime

from companies.infrastructure.models.company_model import CompanyModel, CompanyIntelligenceModel


def _to_str(value: Any) -> Any:
    """Normalize datetime values to ISO strings (Text columns may hold datetimes on fresh inserts)."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def company_model_to_dict(model: CompanyModel) -> dict[str, Any]:
    """Convert a CompanyModel to a domain dictionary."""
    return {
        "id": model.id,
        "name": model.name,
        "website": model.website,
        "domain": model.domain,
        "industry": model.industry,
        "country": model.country,
        "city": model.city,
        "description": model.description,
        "raw_content": model.raw_content,
        "company_size": model.company_size,
        "company_type": model.company_type,
        "logo_url": model.logo_url,
        "founded_year": model.founded_year,
        "headquarters_full": model.headquarters_full,
        "countries_of_operation": model.countries_of_operation,
        "funding_stage": model.funding_stage,
        "funding_amount": model.funding_amount,
        "products": model.products,
        "tech_stack": model.tech_stack,
        "work_environment": model.work_environment,
        "extra": model.extra,
        "status": model.status,
        "created_at": _to_str(model.created_at),
        "updated_at": model.updated_at,
        "queue_order": model.queue_order,
        "current_node": model.current_node,
        "progress_pct": model.progress_pct,
        "error": model.error,
        "retry_count": model.retry_count,
        "failure_reason": model.failure_reason,
        "failure_step": model.failure_step,
        "failure_timestamp": model.failure_timestamp,
        "session_id": model.session_id,
        "parent_company_id": model.parent_company_id,
    }


def dict_to_company_model(data: dict[str, Any]) -> CompanyModel:
    """Convert a domain dictionary to a CompanyModel."""
    return CompanyModel(**{k: v for k, v in data.items() if hasattr(CompanyModel, k)})


def company_intelligence_model_to_dict(model: CompanyIntelligenceModel) -> dict[str, Any]:
    """Convert a CompanyIntelligenceModel to a domain dictionary."""
    return {
        "id": model.id,
        "company_id": model.company_id,
        "overview": model.overview,
        "culture_analysis": model.culture_analysis,
        "international_analysis": model.international_analysis,
        "career_analysis": model.career_analysis,
        "benefits_analysis": model.benefits_analysis,
        "visa_analysis": model.visa_analysis,
        "technology_analysis": model.technology_analysis,
        "recommendation": model.recommendation,
        "scores": model.scores,
        "raw_source_data": model.raw_source_data,
        "generated_at": model.generated_at,
    }
