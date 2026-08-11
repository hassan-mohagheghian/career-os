"""Application Intelligence prompt builders — preparation plan, tailored resume
and cover letter generation.

Each builder produces a versioned prompt plus its strict output JSON schema.
The LLM call always goes through LLMService (AGENTS.md rule #1) and the result
is validated against the mirrored Pydantic models in
``application_intelligence_validation``.

These generators are *consumers* of existing Career Intelligence: the prompt is
grounded in the persisted job analysis, company intelligence and candidate
profile. They never re-analyze the job, company or user.
"""

from __future__ import annotations

import json
from typing import Any

APPLICATION_INTELLIGENCE_PROMPT_VERSION = "1.0.0"
APPLICATION_INTELLIGENCE_SCHEMA_VERSION = "1.0.0"


def build_preparation_output_schema() -> dict[str, Any]:
    """JSON schema for the preparation plan (hard/soft skill gap plan)."""
    gap_item = {
        "type": "object",
        "properties": {
            "skill": {"type": "string"},
            "gap_level": {"type": "string", "enum": ["missing", "low", "matching"]},
            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
            "why": {"type": "string"},
            "what_to_learn": {"type": "array", "items": {"type": "string"}},
            "how_to_practice": {"type": "array", "items": {"type": "string"}},
            "resources": {"type": "array", "items": {"type": "string"}},
            "estimated_effort": {"type": "string"},
        },
        "required": ["skill"],
    }
    soft_item = {
        "type": "object",
        "properties": {
            "skill": {"type": "string"},
            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
            "why": {"type": "string"},
            "what_to_improve": {"type": "array", "items": {"type": "string"}},
            "how_to_practice": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["skill"],
    }
    return {
        "type": "object",
        "properties": {
            "hard_skills": {"type": "array", "items": gap_item},
            "soft_skills": {"type": "array", "items": soft_item},
        },
        "required": ["hard_skills", "soft_skills"],
    }


def build_document_output_schema() -> dict[str, Any]:
    """JSON schema for generated documents (tailored resume / cover letter).

    Documents are plain markdown content inside an envelope so the response is
    parseable and the content is directly editable in the workspace.
    """
    return {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
        },
        "required": ["content"],
    }


def _sections(context: dict[str, str], keys: list[str]) -> str:
    return "\n\n".join(context.get(k) or f"{k.upper()}:\n  (no data available)" for k in keys)


def build_preparation_prompt(context: dict[str, str]) -> str:
    """Build the preparation plan prompt (grounded in job + job skills)."""
    schema = json.dumps(build_preparation_output_schema(), indent=2)
    return f"""You are a senior career advisor for a software engineer preparing to apply for a visa-sponsored role in Europe.

Build a practical, prioritized preparation plan based ONLY on the structured job analysis below. Never re-analyze the job — use the tagged skills and scores as the source of truth.

{_sections(context, ["job", "job_skills"])}

PLAN RULES:
1. hard_skills: for EVERY job-required skill tagged "missing" or "low" by the analysis, create one entry.
   - gap_level: "missing" (user lacks it) or "low" (has it below the required level). Never "matching".
   - priority: "high" (blocks the application / core to the role), "medium", or "low".
   - why: one sentence tying the skill to this specific job.
   - what_to_learn: 2-3 concrete, actionable learning objectives.
   - how_to_practice: 2-3 concrete practice exercises (projects, katas, contributions).
   - resources: 1-2 realistic learning resources (documentation, courses, repos) — do not invent obscure URLs.
   - estimated_effort: short duration estimate (e.g. "3-4 weeks").
2. soft_skills: at most 3 high-value soft skills the user should emphasize or improve for THIS role (e.g. from the job's collaboration/culture signals in the analysis), with priority, why, what_to_improve (1-2), how_to_practice (1-2).
3. Keep the whole plan actionable: at most 10 hard_skills and 3 soft_skills.

Respond ONLY with valid JSON matching exactly this schema:

{schema}
"""


def build_resume_prompt(context: dict[str, str]) -> str:
    """Build the tailored resume prompt (grounded in job + company + candidate)."""
    schema = json.dumps(build_document_output_schema(), indent=2)
    return f"""You are a senior career advisor writing a tailored resume for a software engineer applying for a visa-sponsored role in Europe.

Write a complete, professional resume as MARKDOWN (not JSON) that:
1. Is tailored to THIS job posting and THIS company — mirror the job's required skills and the company's technology/culture signals.
2. Uses ONLY facts from the candidate profile below. Never invent experience, skills, employers or dates.
3. Emphasizes the candidate's matched skills and achievements that map to the job's required skills (from the job analysis).
4. Ordering: contact/header → professional summary (2-3 lines) → core competencies (skills relevant to the job) → experience (reverse chronological) → projects → education → certificates → languages.
5. Uses markdown headings (##), bullet lists, and bold for job titles / company names.

{_sections(context, ["job", "company", "candidate"])}

CONSTRAINTS:
- Output ONLY the resume markdown content inside the JSON envelope "content". No preamble, no code fences.
- Keep the resume to at most one page of focused content — every bullet must be high-signal for this specific application.
- Do not add placeholder sections the candidate has no data for.

Respond ONLY with valid JSON matching exactly this schema:

{schema}
"""


def build_cover_letter_prompt(context: dict[str, str]) -> str:
    """Build the cover letter prompt (grounded in job + company + candidate)."""
    schema = json.dumps(build_document_output_schema(), indent=2)
    return f"""You are a senior career advisor writing a cover letter for a software engineer applying for a visa-sponsored role in Europe.

Write a complete, professional cover letter as MARKDOWN (not JSON) that:
1. Opens with a clear subject line (## Subject) and a formal greeting addressed to the hiring team.
2. States the role, company and how the candidate found it.
3. In 3-5 body paragraphs, connects the candidate's real experience (from the profile ONLY) to the job's required skills and the company's technology/culture (from the intelligence below). Show, don't tell — use concrete achievements from the profile.
4. Explicitly addresses the visa/relocation angle briefly and confidently (the candidate is seeking a visa-sponsored role).
5. Closes with a call to action and a professional signature (## Signature).

{_sections(context, ["job", "company", "candidate"])}

CONSTRAINTS:
- Output ONLY the cover letter markdown content inside the JSON envelope "content". No preamble, no code fences.
- Keep the letter to at most 350 words.
- Never invent experience, numbers, or facts not present in the candidate profile.

Respond ONLY with valid JSON matching exactly this schema:

{schema}
"""
