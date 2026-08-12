"""Grounded context assembly for the Application Intelligence workflow.

The application workspace is a *consumer* of existing Career Intelligence — it
never re-analyzes a job, company or the user. These builders turn the persisted
structured intelligence (job + job analysis, company + company intelligence,
candidate profile) into labeled prompt sections. They reuse the profile
formatters from ``job_analysis_inputs`` so the application context stays
consistent with the analysis prompts.
"""

from __future__ import annotations

import json
from typing import Any

from processing.application.services.job_analysis_inputs import (
    build_candidate_profile_text,
)


def build_job_context(job: dict[str, Any], analysis: dict[str, Any] | None) -> str:
    """Format the job row + canonical analysis as a prompt section.

    ``analysis`` carries the job_analysis payload (scores, recommendation,
    apply_reason, summary, skills with matched/missing/low status, insights).
    """
    lines = ["JOB:", ]
    for key in ("title", "company", "role", "location", "salary", "visa", "industry", "domain"):
        value = job.get(key)
        if value:
            lines.append(f"  {key}: {value}")

    if not analysis or not analysis.get("payload"):
        lines.append("  (no structured analysis available)")
        return "\n".join(lines)

    payload = analysis.get("payload") or {}
    scores = payload.get("scores") or {}
    summary = payload.get("summary") or {}

    lines.append("JOB ANALYSIS (canonical, persisted):")
    if scores.get("fit") is not None:
        lines.append(f"  fit score: {scores.get('fit')}")
    if scores.get("success") is not None:
        lines.append(f"  success score: {scores.get('success')}")
    if payload.get("recommendation"):
        lines.append(f"  recommendation: {payload['recommendation']}")
    if payload.get("apply_reason"):
        lines.append(f"  apply reason: {payload['apply_reason']}")
    if summary.get("summary"):
        lines.append(f"  summary: {summary['summary']}")
    if summary.get("resume_fit"):
        lines.append(f"  resume fit: {summary['resume_fit']}")

    scores_explanation = payload.get("scores_explanation") or {}
    for label, key in (
        ("  fit factors:", "fit_factors"),
        ("  success factors:", "success_factors"),
        ("  concerns:", "concerns"),
    ):
        items = scores_explanation.get(key) or []
        if items:
            lines.append(label)
            for item in items:
                lines.append(f"    - {item}")

    return "\n".join(lines)


def build_job_skills_context(analysis: dict[str, Any] | None) -> str:
    """Format the job-required skills tagged by the analysis (matched/missing/low).

    This is the primary source for skill-gap grounding in the generation prompts.
    """
    payload = (analysis or {}).get("payload") or {}
    skills = payload.get("skills") or []
    if not skills:
        return "JOB SKILLS:\n  (no skill extraction available)"
    lines = ["JOB SKILLS (tagged by analysis):"]
    for s in skills:
        meta = []
        if s.get("status"):
            meta.append(s["status"])
        if s.get("level") is not None:
            meta.append(f"level {s['level']}")
        if s.get("category"):
            meta.append(str(s["category"]))
        suffix = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"  - {s.get('name')}{suffix}")
        if s.get("evidence"):
            lines.append(f"      evidence: {s['evidence']}")
    return "\n".join(lines)


def build_company_context(company: dict[str, Any], intelligence: dict[str, Any] | None) -> str:
    """Format the company row + intelligence sections as a prompt section."""
    lines = ["COMPANY:", ]
    for key in ("name", "website", "domain", "country", "location"):
        value = company.get(key)
        if value:
            lines.append(f"  {key}: {value}")

    if not intelligence:
        lines.append("  (no company intelligence available)")
        return "\n".join(lines)

    lines.append("COMPANY INTELLIGENCE (canonical, persisted):")
    for label, key in (
        ("overview", "overview"),
        ("technology", "technology_analysis"),
        ("culture", "culture_analysis"),
        ("benefits", "benefits_analysis"),
        ("internationalization", "international_analysis"),
        ("career", "career_analysis"),
        ("visa", "visa_analysis"),
    ):
        value = intelligence.get(key)
        if value:
            lines.append(f"  {label}: {value}")

    recommendation = intelligence.get("recommendation")
    if recommendation:
        lines.append(f"  recommendation: {recommendation}")
    scores = intelligence.get("scores")
    if isinstance(scores, dict):
        lines.append(f"  scores: {json.dumps(scores, ensure_ascii=False)}")

    return "\n".join(lines)


def build_candidate_context(profile: dict[str, Any] | None) -> str:
    """Format the candidate profile (reuses the analysis profile builder)."""
    return build_candidate_profile_text(profile)


def build_application_context(
    job: dict[str, Any],
    analysis: dict[str, Any] | None,
    company: dict[str, Any] | None,
    intelligence: dict[str, Any] | None,
    profile: dict[str, Any] | None,
) -> dict[str, str]:
    """Assemble the labeled sections consumed by the generation prompts.

    Returns a map of section name → text so each prompt builder can embed the
    sections it needs (job + skills + company + candidate).
    """
    return {
        "job": build_job_context(job, analysis),
        "job_skills": build_job_skills_context(analysis),
        "company": build_company_context(company or {}, intelligence),
        "candidate": build_candidate_context(profile),
    }
