"""PrepareProfileNode — gathers the user's profile for the analysis prompt.

Loads the user's skills, the latest resume and LinkedIn profile raw text, and
the enabled scoring rules, and stores formatted text in the state's
analysis_context. The resume is authoritative, LinkedIn supplements it.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.job_analysis_inputs import (
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
        resume_repo: Any,
        rule_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._skills = skill_repo
        self._resumes = resume_repo
        self._rules = rule_repo
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        try:
            skills = self._skills.list_visible()
            rule_rows = self._rules.get_enabled_by_scopes(["SHARED", "JOB"])
            resume_raw = self._resumes.get_latest_original_raw_text()
            linkedin_raw = self._resumes.get_latest_linkedin_raw_text()
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load user profile: {e}")
            skills, rule_rows, resume_raw, linkedin_raw = [], [], None, None

        state.analysis_context["job_text"] = (
            state.processing_context.combined_text if state.processing_context else ""
        )
        state.analysis_context["profile_text"] = build_profile_text(skills)
        state.analysis_context["scoring_rules"] = build_scoring_rules_text(rule_rows)
        state.analysis_context["resume_text"] = build_resume_text(resume_raw)
        state.analysis_context["profile_documents"] = build_profile_documents_text(resume_raw, linkedin_raw)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
