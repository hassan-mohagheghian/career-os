"""Pure scoring and normalization helpers for the Job Analysis workflow.

Deterministic business rules (parity with the legacy worker) so tests can
verify behavior without an LLM:
  - scores are clamped to 0-100
  - overall = round(fit * 0.6 + success * 0.4)
  - recommendation derived from overall: apply >= 80, consider >= 60, else skip
"""

from __future__ import annotations

import json
from typing import Any

VALID_RECOMMENDATIONS = ("apply", "consider", "skip")

# Legacy letter-grade buckets (parity with the legacy worker).
_GRADE_BUCKETS = (
    (90, "A++"), (80, "A+"), (70, "A"), (50, "B"), (30, "C"), (0, "D"),
)


def grade_for_overall(overall: int | None) -> str:
    """Map an overall score to a legacy letter grade (A++ .. D)."""
    if overall is None:
        return "P"
    for threshold, grade in _GRADE_BUCKETS:
        if overall >= threshold:
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
    """Weighted overall score, rounded to the nearest integer."""
    fit_n = normalize_score_100(fit)
    success_n = normalize_score_100(success)
    if fit_n is None or success_n is None:
        return None
    return round(fit_n * 0.6 + success_n * 0.4)


def recommendation_for_overall(overall: int | None) -> str:
    """Map an overall score to an apply/consider/skip recommendation."""
    if overall is None:
        return "skip"
    if overall >= 80:
        return "apply"
    if overall >= 60:
        return "consider"
    return "skip"


def coerce_recommendation(value: Any) -> str:
    """Ensure a recommendation is one of apply/consider/skip."""
    if isinstance(value, str) and value.strip().lower() in VALID_RECOMMENDATIONS:
        return value.strip().lower()
    return "skip"


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [x.strip() for x in value.split(",") if x.strip()]
        return items if items else ([value.strip()] if value.strip() else [])
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def normalize_payload(raw: Any) -> dict[str, Any]:
    """Coerce the LLM payload (dict or JSON string) into a canonical dict."""
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return dict(raw) if isinstance(raw, dict) else {}


def build_analysis_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical analysis result from a normalized LLM payload.

    Deterministic parts (scores, recommendation) are computed here and take
    precedence over the LLM's own values; the LLM provides explanation text.
    """
    scores = payload.get("scores") or {}
    fit = normalize_score_100(scores.get("fit"))
    success = normalize_score_100(scores.get("success"))
    overall = calculate_overall_score(fit, success)

    explanation = payload.get("scores_explanation") or {}
    summary = payload.get("summary") or {}

    return {
        "fields": {
            "title": payload.get("title"),
            "company": payload.get("company"),
            "role": payload.get("role"),
            "location": payload.get("location"),
            "salary": payload.get("salary"),
            "stack": payload.get("stack"),
            "visa": payload.get("visa"),
            "work_types": _coerce_string_list(payload.get("work_types")),
            "employment_types": _coerce_string_list(payload.get("employment_types")),
            "industry": payload.get("industry"),
            "domain": payload.get("domain"),
            "description": payload.get("description"),
        },
        "scores": {
            "fit": fit,
            "success": success,
            "overall": overall,
        },
        "scores_explanation": {
            "fit_factors": _coerce_string_list(explanation.get("fit_factors")),
            "success_factors": _coerce_string_list(explanation.get("success_factors")),
            "concerns": _coerce_string_list(explanation.get("concerns")),
        },
        "recommendation": recommendation_for_overall(overall),
        "apply_reason": str(payload.get("apply_reason") or "").strip(),
        "summary": {
            "summary": str(summary.get("summary") or "").strip(),
            "resume_fit": str(summary.get("resume_fit") or "").strip(),
            "note": str(summary.get("note") or "").strip(),
        },
        "skills": [],
        "insights": _coerce_string_list(payload.get("insights")),
    }


def normalize_skills(raw_skills: Any) -> list[dict[str, Any]]:
    """Normalize the LLM skills list: drop empties, default missing fields."""
    if not isinstance(raw_skills, list):
        return []
    result: list[dict[str, Any]] = []
    for item in raw_skills:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        result.append({
            "name": name,
            "category": str(item.get("category") or "").strip(),
            "level": normalize_score_100(item.get("level")),
            "status": coerce_status(item.get("status")),
            "evidence": str(item.get("evidence") or "").strip(),
        })
    return result


def coerce_status(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in ("matched", "missing", "low"):
        return value.strip().lower()
    return "missing"
