"""Pure scoring and normalization helpers for the Company Analysis workflow.

Deterministic business rules (parity with the legacy company worker) so tests
can verify behavior without an LLM:
  - scores are clamped to 0-100
  - overall = round(fit * 0.5 + success * 0.5)
  - grades derived from the legacy A++..D buckets
"""

from __future__ import annotations

import json
from typing import Any

# Legacy letter-grade buckets (parity with the legacy company worker).
_GRADE_BUCKETS = (
    (90, "A++"), (80, "A+"), (70, "A"), (50, "B"), (30, "C"), (0, "D"),
)


def grade_for_overall(overall: Any) -> str:
    """Map an overall score to a legacy letter grade (A++ .. D)."""
    score = normalize_score_100(overall)
    if score is None:
        return "P"
    for threshold, grade in _GRADE_BUCKETS:
        if score >= threshold:
            return grade
    return "P"


def normalize_score_100(value: Any) -> int | None:
    """Coerce a value to an int in [0, 100], or None when it cannot be parsed."""
    if value is None or value == "":
        return None
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return None
    return max(0, min(100, n))


def calculate_overall_score(fit: Any, success: Any) -> int | None:
    """Weighted overall score (fit 50% + success 50%), rounded."""
    fit_n = normalize_score_100(fit)
    success_n = normalize_score_100(success)
    if fit_n is None or success_n is None:
        return None
    return round(fit_n * 0.5 + success_n * 0.5)


def coerce_company_type(value: Any) -> str:
    valid = (
        "PRODUCT_COMPANY",
        "RECRUITING_AGENCY",
        "STAFFING_COMPANY",
        "CONSULTING_COMPANY",
        "UNKNOWN",
    )
    if isinstance(value, str) and value.strip().upper() in valid:
        return value.strip().upper()
    return "UNKNOWN"


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [x.strip() for x in value.split(",") if x.strip()]
        return items if items else ([value.strip()] if value.strip() else [])
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def _coerce_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_payload(raw: Any) -> dict[str, Any]:
    """Coerce the LLM payload (dict or JSON string) into a canonical dict."""
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return dict(raw) if isinstance(raw, dict) else {}


def build_company_analysis_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical company analysis result from a normalized LLM payload.

    Deterministic parts (scores, grades) are computed here and take precedence
    over the LLM's own values; the LLM provides the explanation text.
    """
    extraction_raw = _coerce_dict(payload.get("extraction"))
    intelligence_raw = _coerce_dict(payload.get("intelligence"))
    recommendation_raw = _coerce_dict(payload.get("recommendation"))
    scores_raw = _coerce_dict(payload.get("scores"))

    fit = normalize_score_100(scores_raw.get("company_fit_score"))
    success = normalize_score_100(scores_raw.get("company_success_score"))
    overall = calculate_overall_score(fit, success)

    return {
        "extraction": {
            "name": _coerce_str(extraction_raw.get("name")),
            "website": _coerce_str(extraction_raw.get("website")),
            "domain": _coerce_str(extraction_raw.get("domain")),
            "industry": _coerce_str(extraction_raw.get("industry")),
            "country": _coerce_str(extraction_raw.get("country")),
            "city": _coerce_str(extraction_raw.get("city")),
            "description": _coerce_str(extraction_raw.get("description")),
            "company_size": _coerce_str(extraction_raw.get("company_size")),
            "company_type": coerce_company_type(extraction_raw.get("company_type")),
            "logo_url": _coerce_str(extraction_raw.get("logo_url")),
            "founded_year": _coerce_str(extraction_raw.get("founded_year")),
            "headquarters_full": _coerce_str(extraction_raw.get("headquarters_full")),
            "countries_of_operation": _coerce_string_list(extraction_raw.get("countries_of_operation")),
            "products": _coerce_string_list(extraction_raw.get("products")),
            "tech_stack": _coerce_dict(extraction_raw.get("tech_stack")),
            "work_environment": _coerce_dict(extraction_raw.get("work_environment")),
            "funding_stage": _coerce_str(extraction_raw.get("funding_stage")),
            "funding_amount": _coerce_str(extraction_raw.get("funding_amount")),
        },
        "intelligence": {
            "overview": _coerce_dict(intelligence_raw.get("overview")),
            "culture_analysis": _coerce_dict(intelligence_raw.get("culture_analysis")),
            "international_analysis": _coerce_dict(intelligence_raw.get("international_analysis")),
            "career_analysis": _coerce_dict(intelligence_raw.get("career_analysis")),
            "benefits_analysis": _coerce_dict(intelligence_raw.get("benefits_analysis")),
            "visa_analysis": _coerce_dict(intelligence_raw.get("visa_analysis")),
            "technology_analysis": _coerce_dict(intelligence_raw.get("technology_analysis")),
        },
        "recommendation": {
            "priority": _coerce_str(recommendation_raw.get("priority")) or "B",
            "observation": _coerce_str(recommendation_raw.get("observation")),
            "evidence": _coerce_str(recommendation_raw.get("evidence")),
            "impact": _coerce_str(recommendation_raw.get("impact")),
            "action": _coerce_str(recommendation_raw.get("action")),
            "ideal_role": _coerce_str(recommendation_raw.get("ideal_role")),
            "timing": _coerce_str(recommendation_raw.get("timing")),
        },
        "scores": {
            "fit": fit,
            "success": success,
            "overall": overall,
            "fit_grade": grade_for_overall(scores_raw.get("company_fit_score")),
            "overall_grade": grade_for_overall(overall),
            "fit_explanation": _coerce_str(scores_raw.get("fit_explanation")),
            "fit_positive_factors": _coerce_string_list(scores_raw.get("fit_positive_factors")),
            "fit_negative_factors": _coerce_string_list(scores_raw.get("fit_negative_factors")),
            "success_explanation": _coerce_str(scores_raw.get("success_explanation")),
            "success_positive_factors": _coerce_string_list(scores_raw.get("success_positive_factors")),
            "success_negative_factors": _coerce_string_list(scores_raw.get("success_negative_factors")),
            # Legacy aliases consumed by the v2 list/detail APIs and the UI.
            "company_fit_score": fit,
            "company_success_score": success,
            "company_overall_score": overall,
        },
    }
