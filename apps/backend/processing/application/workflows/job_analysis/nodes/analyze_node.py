"""AnalyzeNode — the single combined LLM call for a job.

Runs job.analyze via LLMService (the only sanctioned way to call a provider).
Emit mid-call progress updates so the frontend sees live progress.
"""

from __future__ import annotations

import json
from typing import Any

from ai.infrastructure.service import get_llm_service

from processing.application.services.job_analysis_prompt import (
    JOB_ANALYSIS_PROMPT_VERSION,
    JOB_ANALYSIS_SCHEMA_VERSION,
    build_job_analysis_output_schema,
    build_job_analysis_prompt,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "analyze"


def _coerce_payload(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


class AnalyzeNode:
    def __init__(self, llm_service: Any | None = None, event_publisher: Any | None = None):
        self._llm = llm_service
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        progress_ops.update_step(self._events, state, NODE_ID, 30)

        job_text = state.analysis_context.get("job_text") or ""
        profile_text = state.analysis_context.get("profile_text") or ""
        scoring_rules = state.analysis_context.get("scoring_rules") or ""
        resume_text = state.analysis_context.get("resume_text") or ""

        if not job_text:
            state.errors.append(f"[{NODE_ID}] No job text to analyze for {state.job_id}")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        prompt = build_job_analysis_prompt(job_text, profile_text, scoring_rules, resume_text)
        llm = self._llm or get_llm_service()
        try:
            resp = llm.generate_structured(
                prompt,
                schema=build_job_analysis_output_schema(),
                timeout=240,
            )
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] LLM analysis failed: {e}")
            state.status = ExecutionStatus.FAILED
            progress_ops.fail_step(self._events, state, NODE_ID, str(e))
            return state

        progress_ops.update_step(self._events, state, NODE_ID, 80)
        payload = _coerce_payload(resp.content)
        if not payload:
            state.errors.append(f"[{NODE_ID}] LLM returned no parseable analysis")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        payload["prompt_version"] = JOB_ANALYSIS_PROMPT_VERSION
        payload["schema_version"] = JOB_ANALYSIS_SCHEMA_VERSION
        state.analysis_context["raw_payload"] = payload
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
