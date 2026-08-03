"""Domain-to-database mapping layer.

This module provides functions to convert between domain entities (dicts)
and SQLAlchemy ORM models. The mapping happens in the infrastructure layer,
keeping the domain layer clean of persistence concerns.
"""

from typing import Any
from datetime import datetime

from jobs.infrastructure.models.job_model import JobModel
from skills.infrastructure.models.skill_model import SkillModel, SkillAliasModel, SkillRelationshipModel
from companies.infrastructure.models.company_model import CompanyModel, CompanyIntelligenceModel

from shared.infrastructure.database.models.misc_models import ResumeModel


# ── Job Mappers ──────────────────────────────────────────────────

def _to_str(value: Any) -> Any:
    """Normalize datetime values to ISO strings (Text columns may hold datetimes on fresh inserts)."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def job_model_to_dict(model: JobModel) -> dict[str, Any]:
    """Convert a JobModel to a domain dictionary."""
    return {
        "id": model.id,
        "company": model.company,
        "role": model.role,
        "location": model.location,
        "match": model.match,
        "score": model.score,
        "success": model.success,
        "salary": model.salary,
        "stack": model.stack,
        "visa": model.visa,
        "applicants": model.applicants,
        "posted": model.posted,
        "industry": model.industry,
        "domain": model.domain,
        "notes": model.notes,
        "links": model.links,
        "action": model.action,
        "url": model.url,
        "work_type": model.work_type,
        "workflow_log": model.workflow_log,
        "locations": model.locations,
        "deleted": model.deleted,
        "employment_type": model.employment_type,
        "work_types": model.work_types,
        "raw_description": model.raw_description,
        "structured_description": model.structured_description,
        "adv_at": model.adv_at,
        "see_at": model.see_at,
        "apply_reason": model.apply_reason,
        "fit_score": model.fit_score,
        "success_score": model.success_score,
        "overall_score": model.overall_score,
        "company_id": model.company_id,
        "created_at": _to_str(model.created_at),
        "updated_at": _to_str(model.updated_at),
        "title": model.title,
        "description": model.description,
        "apply_time": model.apply_time,
        "response_time": model.response_time,
        "response_status": model.response_status,
        "rescoring": model.rescoring,
        "status": model.status,
        "queue_order": model.queue_order,
        "current_node": model.current_node,
        "progress_pct": model.progress_pct,
        "error": model.error,
        "retry_count": model.retry_count,
        "failure_reason": model.failure_reason,
        "failure_step": model.failure_step,
        "failure_timestamp": model.failure_timestamp,
        "session_id": model.session_id,
    }


def dict_to_job_model(data: dict[str, Any]) -> JobModel:
    """Convert a domain dictionary to a JobModel."""
    return JobModel(**{k: v for k, v in data.items() if hasattr(JobModel, k)})


# ── Skill Mappers ────────────────────────────────────────────────

def skill_model_to_dict(model: SkillModel, aliases: list[str] | None = None) -> dict[str, Any]:
    """Convert a SkillModel to a domain dictionary."""
    import json
    result = {
        "id": model.id,
        "name": model.name,
        "level": model.level,
        "roles": model.roles,
        "path": model.path,
        "source": model.source,
        "hidden": model.hidden,
        "merged_into": model.merged_into,
        "category": model.category,
        "confidence": model.confidence,
        "market_relevance": model.market_relevance,
        "evidence": model.evidence,
        "source_type": model.source_type,
        "tags": json.loads(model.tags) if model.tags else [],
        "created_at": _to_str(model.created_at),
    }
    if aliases is not None:
        result["aliases"] = aliases
    return result


def dict_to_skill_model(data: dict[str, Any]) -> SkillModel:
    """Convert a domain dictionary to a SkillModel."""
    import json
    skill_data = {}
    for k, v in data.items():
        if hasattr(SkillModel, k):
            if k == "tags" and isinstance(v, list):
                skill_data[k] = json.dumps(v)
            else:
                skill_data[k] = v
    return SkillModel(**skill_data)


# ── Company Mappers ──────────────────────────────────────────────

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
    }


def dict_to_company_model(data: dict[str, Any]) -> CompanyModel:
    """Convert a domain dictionary to a CompanyModel."""
    return CompanyModel(**{k: v for k, v in data.items() if hasattr(CompanyModel, k)})


# ── Company Intelligence Mappers ─────────────────────────────────

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


# ── Resume Mappers ───────────────────────────────────────────────

def resume_model_to_dict(model: ResumeModel) -> dict[str, Any]:
    """Convert a ResumeModel to a domain dictionary."""
    return {
        "id": model.id,
        "title": model.title,
        "company": model.company,
        "role": model.role,
        "content": model.content,
        "version": model.version,
        "raw_text": model.raw_text,
        "created_at": _to_str(model.created_at),
        "job_id": model.job_id,
    }
