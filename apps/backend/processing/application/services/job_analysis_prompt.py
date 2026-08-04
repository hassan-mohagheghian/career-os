"""Job analysis prompt builder — a single combined LLM call for a job.

The Job Analysis workflow performs exactly one LLM call per job. This module
owns that prompt (versioned) and its output JSON schema. The LLM call itself
always goes through LLMService (AGENTS.md rule #1).
"""

from __future__ import annotations

import json
from typing import Any

JOB_ANALYSIS_PROMPT_VERSION = "1.0.0"
JOB_ANALYSIS_SCHEMA_VERSION = "1.0.0"


def build_job_analysis_output_schema() -> dict[str, Any]:
    """JSON schema for the combined analysis output."""
    nullable_str = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {
            "title": nullable_str,
            "company": nullable_str,
            "role": nullable_str,
            "location": nullable_str,
            "salary": nullable_str,
            "stack": nullable_str,
            "visa": nullable_str,
            "work_types": {"type": ["array", "null"], "items": {"type": "string"}},
            "employment_types": {"type": ["array", "null"], "items": {"type": "string"}},
            "industry": nullable_str,
            "domain": nullable_str,
            "description": nullable_str,
            "scores": {
                "type": "object",
                "properties": {
                    "fit": {"type": "integer", "minimum": 0, "maximum": 100},
                    "success": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["fit", "success"],
            },
            "scores_explanation": {
                "type": "object",
                "properties": {
                    "fit_factors": {"type": "array", "items": {"type": "string"}},
                    "success_factors": {"type": "array", "items": {"type": "string"}},
                    "concerns": {"type": "array", "items": {"type": "string"}},
                },
            },
            "recommendation": {"type": "string", "enum": ["apply", "consider", "skip"]},
            "apply_reason": {"type": "string"},
            "summary": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "resume_fit": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
            "skills": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "level": {"type": "integer", "minimum": 0, "maximum": 5},
                        "status": {"type": "string", "enum": ["matched", "missing", "low"]},
                        "evidence": {"type": "string"},
                    },
                    "required": ["name"],
                },
            },
            "insights": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["scores", "recommendation", "apply_reason", "summary", "skills", "insights"],
    }


def build_job_analysis_prompt(
    job_text: str,
    user_profile_text: str,
    scoring_rules: str,
    resume_text: str,
) -> str:
    """Build the single combined analysis prompt for a job."""
    schema = json.dumps(build_job_analysis_output_schema(), indent=2)
    return f"""You are a senior career advisor for a software engineer seeking a visa-sponsored role in Europe (Germany, Netherlands).

Analyze the job posting below and the user's profile, then produce a complete structured analysis.

JOB POSTING TEXT:
{job_text}

USER PROFILE (skills and resume):
{user_profile_text}

RESUME TEXT (latest):
{resume_text}

SCORING RULES TO APPLY:
{scoring_rules}

Your analysis must:
1. Extract the job fields (title, company, role, location, salary, stack, visa, work_types, employment_types, industry, domain, description). Use null when a field is absent. work_types is an array of On-site / Remote / Hybrid; employment_types is an array of Full-time / Part-time / Contract / Internship / Temporary. Usually each array has exactly one value.
2. Score fit (0-100): how well the role matches the user's profile (skills, seniority, domain).
3. Score success (0-100): the user's probability of getting an offer (seniority match, level, salary, competition).
4. Explain fit and success with concrete factors and list concerns (gaps, mismatches, risks).
5. Recommend apply / consider / skip based on the scores, and write a short apply_reason justifying it.
6. Summarize the job, the user's fit, and add a practical note.
 7. List the skills the job requires and tag each as "matched" (user already has it), "missing" (user lacks it), or "low" (user has it but below the required level). Include the user's level (1-5), the category, and brief evidence from the posting.
 8. Add 2-4 short insights (what to highlight in the application, salary/visa notes, etc.).

OUTPUT SIZE LIMITS (critical — keep the response short so it is never truncated):
 1. description: a concise 1-2 sentence overview, at most 120 words. Do NOT copy the full posting.
 2. skills: list at most 12 skills.
 3. insights: 2-3 items only.
 4. scores_explanation: at most 3 items per list (fit_factors, success_factors, concerns).
 5. apply_reason and each summary field (summary, resume_fit, note): at most 40 words each.
 6. The JSON must be complete and valid — every string and bracket closed. Never truncate the output.

Respond ONLY with valid JSON matching exactly this schema:

{schema}
"""
