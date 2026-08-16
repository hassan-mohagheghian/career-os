"""PrepareCompanyNode — gathers the inputs for the combined company analysis.

Loads the enabled scoring rules for the company scope (derived from the
company type), the candidate's latest resume/LinkedIn and candidate profile, and
stores the formatted prompt inputs on the analysis context.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.company_analysis_inputs import (
    build_company_type_line,
    build_scoring_rules_text,
    scope_for_company_type,
)
from processing.application.services.job_analysis_inputs import (
    build_candidate_profile_text,
    build_profile_documents_text,
    build_resume_text,
)
from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "prepare_company"


class PrepareCompanyNode:
    def __init__(
        self,
        rule_repo: Any,
        source_repo: Any | None = None,
        candidate_profile_repo: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._rules = rule_repo
        self._sources = source_repo
        self._profiles = candidate_profile_repo
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        company = state.company
        company_type = (company.company_type if company else None) or "UNKNOWN"
        scope = scope_for_company_type(company_type)

        try:
            rule_rows = self._rules.get_enabled_by_scopes(["SHARED", scope])
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load scoring rules: {e}")
            rule_rows = []

        state.analysis_context["company_text"] = (
            state.processing_context.combined_text if state.processing_context else ""
        )
        state.analysis_context["company_type"] = build_company_type_line(company_type)
        state.analysis_context["scoring_rules"] = build_scoring_rules_text(rule_rows)

        profile_id, resume_raw, linkedin_raw, profile = self._load_candidate_inputs(state)
        state.analysis_context["resume_text"] = build_resume_text(resume_raw)
        state.analysis_context["profile_documents"] = build_profile_documents_text(
            resume_raw, linkedin_raw
        )
        if profile:
            state.analysis_context["profile_documents"] = build_candidate_profile_text(profile)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _load_candidate_inputs(
        self, state: CompanyProcessingState
    ) -> tuple[str, str | None, str | None, dict[str, Any] | None]:
        if self._sources is None:
            return "", None, None, None
        profile = self._load_profile()
        profile_id = (profile or {}).get("id") or ""
        try:
            resume_raw = self._latest_raw_text(profile_id, "resume")
            linkedin_raw = self._latest_raw_text(profile_id, "linkedin")
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to load candidate sources: {e}")
            resume_raw, linkedin_raw = None, None
        return profile_id, resume_raw, linkedin_raw, profile

    def _load_profile(self) -> dict[str, Any] | None:
        if self._profiles is None:
            return None
        try:
            return self._profiles.get_current_profile()
        except Exception:
            return None

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
