"""LinkCompanyNode — connects a processed job to every company mentioned in it.

Best-effort step that runs after the analysis result is persisted:

  - resolves the extracted hiring company (name + optional website) through
    ``CompanyMatchingService`` (existing company → link, no match → minimal
    company auto-created) and writes ``job.company_id`` / ``job.company``;
  - resolves every related (recruiting / staffing / agency) company the same
    way and records all associations in the ``job_companies`` table
    (``role="hiring"`` for the hiring company, ``role="recruiter"`` for the
    rest) via the job-company repository;
  - when no hiring company could be extracted, falls back the display company
    to the highest-confidence related company so the job card still shows a
    name.

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
        job_company_repo: Any | None = None,
        event_publisher: Any | None = None,
    ):
        self._matching = matching_service
        self._jobs = job_repo
        self._job_companies = job_company_repo
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        if self._matching is None:
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        result = state.analysis_result or {}
        fields = result.get("fields") or {}
        companies = result.get("companies") or {}
        hiring = companies.get("hiring_company") or {}
        related = companies.get("related_companies") or []

        try:
            rows: list[dict[str, Any]] = []

            # 1. Hiring company (best-effort; drives job.company_id + job.company).
            hiring_name = (hiring.get("name") or "").strip()
            if hiring_name:
                company_id, _created = self._matching.find_or_create(
                    hiring_name,
                    fields.get("company_url"),
                    hiring.get("company_type"),
                )
                if company_id:
                    self._jobs.update_fields(state.job_id, company_id=company_id)
                    rows.append({
                        "company_id": company_id,
                        "role": "hiring",
                        "company_type": hiring.get("company_type"),
                        "confidence": hiring.get("confidence"),
                        "reason": hiring.get("reason"),
                    })

            # 2. Related (recruiting / staffing / agency) companies.
            related_ids: list[dict[str, Any]] = []
            for ref in related:
                name = (ref.get("name") or "").strip()
                if not name:
                    continue
                company_id, _created = self._matching.find_or_create(
                    name, None, ref.get("company_type")
                )
                if company_id:
                    related_ids.append({
                        "company_id": company_id,
                        "role": "recruiter",
                        "company_type": ref.get("company_type"),
                        "confidence": ref.get("confidence"),
                        "reason": ref.get("reason"),
                    })
            rows.extend(related_ids)

            # 3. Persist associations (replace rows for this job on re-process).
            if self._job_companies is not None and rows:
                self._job_companies.replace_for_job(state.job_id, rows)

            # 4. Fall back the display company when no hiring company was
            #    extracted but a related (e.g. publishing recruiter) exists.
            if not hiring_name and related:
                best = max(related, key=lambda r: r.get("confidence") or 0.0)
                fallback_name = (best.get("name") or "").strip()
                if fallback_name:
                    self._jobs.update_fields(state.job_id, company=fallback_name)

        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to link company: {e}")

        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
