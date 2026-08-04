"""Builders that turn user data (skills, resume, rules) into prompt text."""

from __future__ import annotations

from typing import Any


def build_profile_text(skills: list[dict[str, Any]]) -> str:
    """Format the user's skill profile for the analysis prompt."""
    if not skills:
        return "(no skills registered)"
    header = f"Total skills: {len(skills)}"
    body = []
    for s in skills:
        meta = []
        if s.get("level") is not None:
            meta.append(f"level {s.get('level')}")
        if s.get("category"):
            meta.append(str(s.get("category")))
        suffix = f" ({', '.join(meta)})" if meta else ""
        body.append(f"- {s.get('name')}{suffix}")
    return header + "\n" + "\n".join(body)


def build_resume_text(resume_raw: str | None) -> str:
    """Format the latest resume raw text, truncating to a sane prompt size."""
    if not resume_raw:
        return "(no resume available)"
    return resume_raw[:6000]


MAX_PROFILE_DOC_CHARS = 6000


def build_profile_documents_text(resume_raw: str | None, linkedin_raw: str | None) -> str:
    """Format the latest resume and LinkedIn profile as labeled prompt sections.

    Each source is truncated independently so a very long document cannot crowd
    out the other. The resume section is listed first because it is the
    authoritative source for skills and seniority.
    """
    sections = []
    if resume_raw:
        sections.append(f"RESUME TEXT (latest):\n{resume_raw[:MAX_PROFILE_DOC_CHARS]}")
    if linkedin_raw:
        sections.append(f"LINKEDIN PROFILE TEXT (latest):\n{linkedin_raw[:MAX_PROFILE_DOC_CHARS]}")
    if not sections:
        return "(no resume or LinkedIn profile available)"
    return "\n\n".join(sections)


def build_scoring_rules_text(rules: list[dict[str, Any]]) -> str:
    """Format enabled scoring rules (SHARED + JOB scopes) for the prompt."""
    if not rules:
        return "(no scoring rules set)"
    lines = []
    for r in rules:
        weight = r.get("score_weight") or r.get("priority") or 0
        lines.append(f"  #{r.get('priority')}  {r.get('key')} (weight:{weight}): {r.get('value')}")
    return "\n".join(lines)
