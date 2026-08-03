"""PersistNode — writes the analysis result to the database.

Writes:
  - the queryable projection onto the jobs row (fields + scores)
  - the summaries row (summary, resumeFit, note, grade)
  - the canonical job_analysis row (full payload + scores + recommendation)
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from typing import Any

from processing.application.services.job_analysis_scoring import grade_for_overall
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "persist"


class PersistNode:
    def __init__(
        self,
        job_repo: Any,
        summary_repo: Any,
        analysis_repo: Any,
        event_publisher: Any | None = None,
    ):
        self._jobs = job_repo
        self._summaries = summary_repo
        self._analysis = analysis_repo
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.analysis_result or {}
        if not result:
            state.errors.append(f"[{NODE_ID}] No analysis result to persist for {state.job_id}")
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        try:
            self._persist_job(state.job_id, result)
            self._persist_summary(state.job_id, result)
            self._persist_analysis(state.job_id, result, state.analysis_context.get("raw_payload") or {})
            state.persisted = True
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to persist analysis: {e}")
            state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _persist_job(self, job_id: str, result: dict[str, Any]) -> None:
        fields = result.get("fields") or {}
        scores = result.get("scores") or {}
        self._jobs.update_fields(
            job_id,
            title=fields.get("title"),
            company=fields.get("company"),
            role=fields.get("role"),
            location=fields.get("location"),
            salary=fields.get("salary"),
            stack=fields.get("stack"),
            visa=fields.get("visa"),
            employment_type=fields.get("employment_type"),
            work_types=json.dumps(fields.get("work_types") or [], ensure_ascii=False),
            industry=fields.get("industry"),
            domain=fields.get("domain"),
            description=fields.get("description"),
            apply_reason=result.get("apply_reason"),
            fit_score=scores.get("fit"),
            success_score=scores.get("success"),
            overall_score=scores.get("overall"),
        )

    def _persist_summary(self, job_id: str, result: dict[str, Any]) -> None:
        fields = result.get("fields") or {}
        summary = result.get("summary") or {}
        overall = (result.get("scores") or {}).get("overall")
        self._summaries.upsert({
            "job_id": job_id,
            "company": fields.get("company"),
            "score": grade_for_overall(overall),
            "summary": summary.get("summary"),
            "resumeFit": summary.get("resume_fit"),
            "note": summary.get("note"),
        })

    def _persist_analysis(self, job_id: str, result: dict[str, Any], raw_payload: dict[str, Any]) -> None:
        generated_at = datetime.now(UTC).isoformat()
        prompt_version = raw_payload.get("prompt_version") or "1.0.0"
        schema_version = raw_payload.get("schema_version") or "1.0.0"
        payload = dict(result)
        payload["generated_at"] = generated_at
        payload["prompt_version"] = prompt_version
        payload["schema_version"] = schema_version
        self._analysis.upsert_by_job_id(
            job_id,
            {
                "payload": json.dumps(payload, ensure_ascii=False),
                "fit_score": (result.get("scores") or {}).get("fit"),
                "success_score": (result.get("scores") or {}).get("success"),
                "overall_score": (result.get("scores") or {}).get("overall"),
                "recommendation": result.get("recommendation"),
                "apply_reason": result.get("apply_reason"),
                "summary": (result.get("summary") or {}).get("summary"),
                "prompt_version": prompt_version,
                "schema_version": schema_version,
                "generated_at": generated_at,
            },
        )
