"""AnalyzeNode — the single combined LLM call for a job.

Runs job.analyze via LLMService (the only sanctioned way to call a provider).
The LLM response is strictly validated against JobAnalysisOutput before it is
accepted: only schema-valid output is stored and persisted. Anything else
(retry once) fails the step with a clean, user-facing message.

Emits mid-call progress updates so the frontend sees live progress.
"""

from __future__ import annotations

import json
from typing import Any

from ai.infrastructure.service import get_llm_service
from pydantic import ValidationError

from processing.application.services.job_analysis_prompt import (
    JOB_ANALYSIS_PROMPT_VERSION,
    JOB_ANALYSIS_SCHEMA_VERSION,
    build_job_analysis_output_schema,
    build_job_analysis_prompt,
)
from processing.application.services.job_analysis_validation import JobAnalysisOutput
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "analyze"

CLEAN_FAILURE_MESSAGE = "The AI returned an analysis that does not match the required format."


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


def _is_json_parse_error(exc: Exception) -> bool:
    """True when the provider could not parse the model's (truncated) JSON."""
    msg = str(exc)
    return "Failed to parse" in msg and "JSON output" in msg


def _format_validation_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    loc = ".".join(str(part) for part in first.get("loc", ())) or "payload"
    return f"invalid field '{loc}': {first.get('msg', 'invalid value')}"


def _extract_valid_payload(content: Any) -> tuple[dict[str, Any] | None, str]:
    """Return (validated_payload, failure_reason). One of the two is None."""
    payload = _coerce_payload(content)
    if not payload:
        return None, "the response was not parseable JSON"
    try:
        validated = JobAnalysisOutput.model_validate(payload)
        return validated.model_dump(), ""
    except ValidationError as e:
        return None, _format_validation_error(e)


_RETRY_SHORTEN_HINT = (
    "\n\nIMPORTANT: Your previous attempt was cut off or did not match the required schema. "
    "Respond again with a SHORTER, COMPLETE JSON object matching the schema exactly: keep "
    "description to at most 60 words, list at most 6 skills, at most 2 insights, and at most 2 "
    "factors per list in scores_explanation. Include all required fields: scores (fit, success), "
    "recommendation, apply_reason, summary, skills, insights. Never truncate the JSON — every "
    "string and bracket must be closed."
)


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
        schema = build_job_analysis_output_schema()
        llm = self._llm or get_llm_service()

        payload, reason = self._obtain_valid_payload(llm, prompt, schema)
        if payload is None:
            return self._fail(state, reason)

        progress_ops.update_step(self._events, state, NODE_ID, 80)
        payload["prompt_version"] = JOB_ANALYSIS_PROMPT_VERSION
        payload["schema_version"] = JOB_ANALYSIS_SCHEMA_VERSION
        state.analysis_context["raw_payload"] = payload
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _obtain_valid_payload(
        self, llm: Any, prompt: str, schema: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, str]:
        """Run the LLM (with one retry) until the response validates against the schema."""
        first_reason = ""
        resp = None
        try:
            resp = llm.generate_structured(prompt, schema=schema, timeout=240)
        except Exception as e:
            if not _is_json_parse_error(e):
                return None, f"LLM call failed: {e}"
            first_reason = "the response was not parseable JSON"

        payload, reason = self._validate(resp)
        if payload is not None:
            return payload, ""

        try:
            resp = llm.generate_structured(
                prompt + _RETRY_SHORTEN_HINT, schema=schema, timeout=240
            )
        except Exception as e:
            return None, reason or first_reason or f"LLM retry failed: {e}"

        payload, retry_reason = self._validate(resp)
        if payload is not None:
            return payload, ""
        return None, reason or retry_reason or first_reason or "unparseable response"

    @staticmethod
    def _validate(resp: Any) -> tuple[dict[str, Any] | None, str]:
        if resp is None:
            return None, "the response was not parseable JSON"
        return _extract_valid_payload(resp.content)

    def _fail(self, state: JobProcessingState, reason: str) -> JobProcessingState:
        state.errors.append(f"[{NODE_ID}] {CLEAN_FAILURE_MESSAGE} ({reason})")
        state.status = ExecutionStatus.FAILED
        progress_ops.fail_step(self._events, state, NODE_ID, CLEAN_FAILURE_MESSAGE)
        return state
