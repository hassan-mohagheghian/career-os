"""LinkCompanyNode — connects a processed job to a company record.

Best-effort step that runs after the analysis result is persisted:

  - reads the extracted ``company`` name and optional ``company_url``,
  - resolves it through ``CompanyMatchingService`` (existing company → link,
    no match → minimal company auto-created),
  - writes ``job.company_id`` on the job row.

This step must never fail the execution: company extraction is a convenience
and a failure here is only surfaced as a workflow warning.
"""

from __future__ import annotations

from typing import Any

from companies.application.services.company_matching_service import CompanyMatchingService
from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "link_company"


class LinkCompanyNode:
    def __init__(
        self,
        matching_service: CompanyMatchingService,
        job_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._matching = matching_service
        self._jobs = job_repo
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        if self._matching is None:
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        result = state.analysis_result or {}
        fields = result.get("fields") or {}
        company_name = (fields.get("company") or "").strip()

        if not company_name:
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        try:
            company_id, _created = self._matching.find_or_create(company_name, fields.get("company_url"))
            if company_id:
                self._jobs.update_fields(state.job_id, company_id=company_id)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to link company: {e}")

        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
