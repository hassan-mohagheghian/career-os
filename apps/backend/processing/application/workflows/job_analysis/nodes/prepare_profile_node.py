"""PrepareProfileNode — gathers the user's profile for the analysis prompt.

Loads the user's skills, the latest resume and LinkedIn profile raw text, and
the enabled scoring rules, and stores formatted text in the state's
analysis_context. When a structured Candidate Profile exists it is the primary
source for skills and the profile document section; the raw resume/LinkedIn
text is the fallback when no profile has been built yet.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.job_analysis_inputs import (
    build_candidate_profile_text,
    build_profile_documents_text,
    build_profile_text,
    build_resume_text,
    build_scoring_rules_text,
)
from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "prepare_profile"


class PrepareProfileNode:
    def __init__(
        self,
        skill_repo: Any,
        source_repo: Any,
        rule_repo: Any,
        event_publisher: Any | None = None,
        candidate_profile_repo: Any | None = None,
    ):
        self._skills = skill_repo
        self._sources = source_repo
        self._rules = rule_repo
        self._events = event_publisher
        self._profiles = candidate_profile_repo

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        profile = self._load_candidate_profile(state)
        profile_id = (profile or {}).get("id")
        if not profile_id and self._profiles is not None:
            try:
                profile_id = self._profiles.get_or_create_current().get("id")
            except Exception:
                profile_id = None
        try:
            skills = self._skills.list_visible()
            rule_rows = self._rules.get_enabled_by_scopes(["SHARED", "JOB"])
            resume_raw = self._latest_raw_text(profile_id, "resume")
            linkedin_raw = self._latest_raw_text(profile_id, "linkedin")
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load user profile: {e}")
            skills, rule_rows, resume_raw, linkedin_raw = [], [], None, None

        state.analysis_context["job_text"] = (
            state.processing_context.combined_text if state.processing_context else ""
        )
        if profile:
            profile_skills = profile.get("skills") or []
            state.analysis_context["profile_text"] = build_profile_text(profile_skills)
            state.analysis_context["profile_documents"] = build_candidate_profile_text(profile)
        else:
            state.analysis_context["profile_text"] = build_profile_text(skills)
            state.analysis_context["profile_documents"] = build_profile_documents_text(resume_raw, linkedin_raw)
        state.analysis_context["scoring_rules"] = build_scoring_rules_text(rule_rows)
        state.analysis_context["resume_text"] = build_resume_text(resume_raw)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _latest_raw_text(self, profile_id: str, source_type: str) -> str | None:
        if not profile_id:
            return None
        try:
            latest = self._sources.get_latest_by_type(profile_id, source_type)
        except Exception:
            return None
        if latest is None:
            return None
        raw_text = latest.get("raw_text")
        if not raw_text or not str(raw_text).strip():
            return None
        return str(raw_text)

    def _load_candidate_profile(self, state: JobProcessingState) -> dict[str, Any] | None:
        if self._profiles is None:
            return None
        try:
            return self._profiles.get_current_profile()
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load candidate profile: {e}")
            return None
