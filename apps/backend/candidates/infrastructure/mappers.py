"""Domain-to-database mapping for the Candidates context.

Converts between domain dictionaries and SQLAlchemy ORM models, serializing
evidence and list payloads to JSON text columns.
"""

import json
import uuid
from typing import Any

from candidates.infrastructure.models.candidate_model import (
    CandidateModel,
    CandidateProfileModel,
    CandidateSourceModel,
    CandidateSkillModel,
    CandidateExperienceModel,
    CandidateProjectModel,
    CandidateEducationModel,
    CandidateCertificateModel,
    CandidateInterestModel,
    CandidateLanguageModel,
    CandidateProfileVersionModel,
)


def _json_load(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return fallback


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


# ── Model → dict ──────────────────────────────────────────────────


def candidate_model_to_dict(model: CandidateModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "name": model.name,
        "headline": model.headline,
        "summary": model.summary,
        "location": model.location,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def profile_model_to_dict(model: CandidateProfileModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "candidate_id": model.candidate_id,
        "version": model.version,
        "name": model.name,
        "title": model.title,
        "headline": model.headline,
        "summary": model.summary,
        "location": model.location,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def source_model_to_dict(model: CandidateSourceModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "source_type": model.source_type,
        "version": model.version,
        "raw_text": model.raw_text,
        "status": model.status,
        "error": model.error,
        "processed_at": model.processed_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def candidate_skill_model_to_dict(model: CandidateSkillModel) -> dict[str, Any]:
    evidence = _json_load(model.evidence, {})
    if not isinstance(evidence, dict):
        evidence = {}
    if "confidence" not in evidence and model.confidence is not None:
        evidence = {**evidence, "confidence": model.confidence}
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "skill_id": model.skill_id,
        "name": model.name,
        "level": model.level,
        "category": model.category,
        "confidence": model.confidence,
        "origin": model.origin,
        "years_of_experience": model.years_of_experience,
        "last_used": model.last_used,
        "evidence": evidence,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def experience_model_to_dict(model: CandidateExperienceModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "company": model.company,
        "role": model.role,
        "start_date": model.start_date,
        "end_date": model.end_date,
        "duration_months": model.duration_months,
        "summary": model.summary,
        "highlights": _json_load(model.highlights, []),
        "skills": _json_load(model.skills, []),
        "evidence": _json_load(model.evidence, {}),
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def project_model_to_dict(model: CandidateProjectModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "name": model.name,
        "description": model.description,
        "url": model.url,
        "role": model.role,
        "skills": _json_load(model.skills, []),
        "evidence": _json_load(model.evidence, {}),
        "start_date": model.start_date,
        "end_date": model.end_date,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def education_model_to_dict(model: CandidateEducationModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "institution": model.institution,
        "degree": model.degree,
        "field": model.field,
        "start_date": model.start_date,
        "end_date": model.end_date,
        "evidence": _json_load(model.evidence, {}),
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def certificate_model_to_dict(model: CandidateCertificateModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "name": model.name,
        "issuer": model.issuer,
        "issue_date": model.issue_date,
        "credential_url": model.credential_url,
        "evidence": _json_load(model.evidence, {}),
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def interest_model_to_dict(model: CandidateInterestModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "name": model.name,
        "created_at": model.created_at,
    }


def language_model_to_dict(model: CandidateLanguageModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "name": model.name,
        "proficiency": model.proficiency,
        "created_at": model.created_at,
    }


def version_model_to_dict(model: CandidateProfileVersionModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "profile_id": model.profile_id,
        "version": model.version,
        "snapshot": _json_load(model.snapshot, {}),
        "source_versions": _json_load(model.source_versions, {}),
        "change_summary": model.change_summary,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


# ── Dict → model ──────────────────────────────────────────────────


def dict_to_candidate_model(data: dict[str, Any]) -> CandidateModel:
    return CandidateModel(
        id=data.get("id") or str(uuid.uuid4()),
        name=data.get("name", ""),
        headline=data.get("headline", ""),
        summary=data.get("summary", ""),
        location=data.get("location", ""),
    )


def dict_to_profile_model(data: dict[str, Any]) -> CandidateProfileModel:
    return CandidateProfileModel(
        id=data.get("id") or str(uuid.uuid4()),
        candidate_id=data.get("candidate_id"),
        version=data.get("version", 1),
        name=data.get("name", ""),
        title=data.get("title", ""),
        headline=data.get("headline", ""),
        summary=data.get("summary", ""),
        location=data.get("location", ""),
    )


def dict_to_source_model(data: dict[str, Any]) -> CandidateSourceModel:
    return CandidateSourceModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        source_type=data.get("source_type", ""),
        version=data.get("version", 1),
        raw_text=data.get("raw_text", ""),
        status=data.get("status", "pending"),
        error=data.get("error", ""),
        processed_at=data.get("processed_at"),
    )


def _normalize_evidence(data: dict[str, Any]) -> dict[str, Any]:
    evidence = data.get("evidence") or {}
    if not isinstance(evidence, dict):
        evidence = {}
    if "confidence" not in evidence and data.get("confidence") is not None:
        evidence = {**evidence, "confidence": data.get("confidence")}
    return evidence


def dict_to_candidate_skill_model(data: dict[str, Any]) -> CandidateSkillModel:
    evidence = _normalize_evidence(data)
    return CandidateSkillModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        skill_id=data.get("skill_id"),
        name=data.get("name", ""),
        level=data.get("level", 1),
        category=data.get("category", ""),
        confidence=evidence.get("confidence", 0.0),
        origin=data.get("origin", "explicit"),
        years_of_experience=data.get("years_of_experience"),
        last_used=data.get("last_used"),
        evidence=_json_dump(evidence),
    )


def dict_to_experience_model(data: dict[str, Any]) -> CandidateExperienceModel:
    return CandidateExperienceModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        company=data.get("company", ""),
        role=data.get("role", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        duration_months=data.get("duration_months"),
        summary=data.get("summary", ""),
        highlights=_json_dump(data.get("highlights") or []),
        skills=_json_dump(data.get("skills") or []),
        evidence=_json_dump(data.get("evidence") or {}),
    )


def dict_to_project_model(data: dict[str, Any]) -> CandidateProjectModel:
    return CandidateProjectModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        name=data.get("name", ""),
        description=data.get("description", ""),
        url=data.get("url", ""),
        role=data.get("role", ""),
        skills=_json_dump(data.get("skills") or []),
        evidence=_json_dump(data.get("evidence") or {}),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
    )


def dict_to_education_model(data: dict[str, Any]) -> CandidateEducationModel:
    return CandidateEducationModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        institution=data.get("institution", ""),
        degree=data.get("degree", ""),
        field=data.get("field", ""),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        evidence=_json_dump(data.get("evidence") or {}),
    )


def dict_to_certificate_model(data: dict[str, Any]) -> CandidateCertificateModel:
    return CandidateCertificateModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        name=data.get("name", ""),
        issuer=data.get("issuer", ""),
        issue_date=data.get("issue_date"),
        credential_url=data.get("credential_url", ""),
        evidence=_json_dump(data.get("evidence") or {}),
    )


def dict_to_interest_model(data: dict[str, Any]) -> CandidateInterestModel:
    return CandidateInterestModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        name=data.get("name", ""),
    )


def dict_to_language_model(data: dict[str, Any]) -> CandidateLanguageModel:
    return CandidateLanguageModel(
        id=data.get("id") or str(uuid.uuid4()),
        profile_id=data.get("profile_id"),
        name=data.get("name", ""),
        proficiency=data.get("proficiency", ""),
    )
