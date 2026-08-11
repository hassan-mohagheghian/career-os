"""LoadContextNode — assembles the grounded intelligence context for one
application artifact generation.

Consumes the persisted Career Intelligence (job + canonical analysis, company +
company intelligence, candidate profile) exactly as the workspace frontend
sees it. Never re-analyzes anything.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.application_intelligence_inputs import (
    build_application_context,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.application_intelligence_state import (
    ApplicationIntelligenceState,
)

NODE_ID = "load_context"


class LoadContextNode:
    def __init__(
        self,
        application_repo: Any,
        job_service: Any,
        analysis_repo: Any,
        company_service: Any,
        intelligence_repo: Any,
        profile_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._applications = application_repo
        self._jobs = job_service
        self._analysis = analysis_repo
        self._companies = company_service
        self._intelligence = intelligence_repo
        self._profiles = profile_repo
        self._events = event_publisher

    def __call__(self, state: ApplicationIntelligenceState) -> ApplicationIntelligenceState:
        progress_ops.start_step(self._events, state, NODE_ID)

        application = self._applications.get_by_id(state.application_id)
        if not application:
            state.errors.append(
                f"[{NODE_ID}] Application {state.application_id} not found"
            )
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        job_id = application.get("job_id") or ""
        state.job_id = job_id
        if not job_id:
            state.errors.append(f"[{NODE_ID}] Application {state.application_id} has no job")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        job = self._jobs.get_job(job_id)
        if not job:
            state.errors.append(f"[{NODE_ID}] Job {job_id} not found")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        analysis = self._analysis.get_by_job_id(job_id)

        company = None
        intelligence = None
        company_id = job.get("company_id")
        if company_id:
            company = self._companies.get_company(company_id)
            if company:
                intelligence = self._intelligence.get_by_company_id(company_id)

        profile = self._profiles.get_current_profile()

        state.context = build_application_context(
            job, analysis, company, intelligence, profile
        )
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
