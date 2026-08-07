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


def build_candidate_profile_text(profile: dict[str, Any]) -> str:
    """Format the structured Candidate Profile as a labeled prompt section.

    Used as the primary profile document for job analysis when a candidate
    profile exists (Phase 102). Falls back to raw resume/LinkedIn text only
    when no profile is available. Truncated to ``MAX_PROFILE_DOC_CHARS`` so a
    large profile cannot crowd out the rest of the prompt.
    """
    if not profile:
        return "(no candidate profile available)"

    header = []
    if profile.get("name"):
        header.append(profile["name"])
    if profile.get("title"):
        header.append(profile["title"])
    if profile.get("headline"):
        header.append(profile["headline"])
    if profile.get("location"):
        header.append(profile["location"])
    if profile.get("version") is not None:
        header.append(f"profile version {profile['version']}")
    if profile.get("summary"):
        header.append(f"Summary: {profile['summary']}")

    lines = ["CANDIDATE PROFILE (canonical, from merged sources):"]
    if header:
        lines.append(" | ".join(header))

    skills = profile.get("skills") or []
    if skills:
        lines.append("SKILLS:")
        for s in skills:
            meta = []
            if s.get("level") is not None:
                meta.append(f"level {s['level']}")
            if s.get("confidence") is not None:
                meta.append(f"confidence {s['confidence']}")
            if s.get("years_of_experience") is not None:
                meta.append(f"years {s['years_of_experience']}")
            evidence = s.get("evidence")
            if isinstance(evidence, dict) and evidence.get("sources"):
                meta.append("evidence: " + ", ".join(str(x) for x in evidence["sources"]))
            suffix = f" ({', '.join(meta)})" if meta else ""
            lines.append(f"- {s.get('name')}{suffix}")

    for label, items in (
        ("EXPERIENCE:", profile.get("experiences") or []),
        ("PROJECTS:", profile.get("projects") or []),
        ("EDUCATION:", profile.get("educations") or []),
        ("CERTIFICATES:", profile.get("certificates") or []),
        ("INTERESTS:", profile.get("interests") or []),
        ("LANGUAGES:", profile.get("languages") or []),
    ):
        if not items:
            continue
        lines.append(label)
        for item in items:
            if label == "EXPERIENCE:":
                dates = ""
                if item.get("start_date") or item.get("end_date"):
                    dates = f" ({item.get('start_date')} -> {item.get('end_date')})"
                detail = f"  {item.get('company')} - {item.get('role')}{dates}"
                if item.get("summary"):
                    detail += f"\n    {item['summary']}"
                lines.append(detail)
            elif label == "PROJECTS:":
                detail = f"  {item.get('name')}"
                if item.get("url"):
                    detail += f" ({item.get('url')})"
                if item.get("description"):
                    detail += f"\n    {item['description']}"
                lines.append(detail)
            elif label == "EDUCATION:":
                lines.append(
                    f"  {item.get('institution')} - {item.get('degree')}"
                    + (f", {item.get('field')}" if item.get("field") else "")
                )
            elif label == "CERTIFICATES:":
                detail = f"  {item.get('name')}"
                if item.get("issuer"):
                    detail += f" ({item.get('issuer')})"
                lines.append(detail)
            elif label == "LANGUAGES:":
                detail = f"  {item.get('name')}"
                if item.get("proficiency"):
                    detail += f" ({item.get('proficiency')})"
                lines.append(detail)
            else:
                lines.append(f"  {item.get('name')}")

    text = "\n".join(lines)
    return text[:MAX_PROFILE_DOC_CHARS]


def build_scoring_rules_text(rules: list[dict[str, Any]]) -> str:
    """Format enabled scoring rules (SHARED + JOB scopes) for the prompt."""
    if not rules:
        return "(no scoring rules set)"
    lines = []
    for r in rules:
        weight = r["priority"]
        lines.append(f"  #{r.get('priority')}  {r.get('key')} (weight:{weight}): {r.get('value')}")
    return "\n".join(lines)
