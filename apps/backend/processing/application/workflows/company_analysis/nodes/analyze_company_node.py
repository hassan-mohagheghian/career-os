"""AnalyzeCompanyNode — the single combined LLM call for a company.

Runs company.analyze_company via LLMService (the only sanctioned way to call a
provider). The LLM response is strictly validated against
CompanyCombinedAnalysisOutput before it is accepted: only schema-valid output
is stored and persisted. Anything else (retry once) fails the step with a
clean, user-facing message.

Emits mid-call progress updates so the frontend sees live progress.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ai.infrastructure.service import get_llm_service
from pydantic import ValidationError
from shared.infrastructure.taskiq.config import WORKER_JOB_TIMEOUT

from processing.application.services.company_analysis_prompt import (
    COMPANY_ANALYSIS_PROMPT_VERSION,
    COMPANY_ANALYSIS_SCHEMA_VERSION,
    build_company_analysis_output_schema,
    build_company_analysis_prompt,
)
from processing.application.services.company_analysis_validation import (
    CompanyCombinedAnalysisOutput,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "analyze_company"

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
        validated = CompanyCombinedAnalysisOutput.model_validate(payload)
        return validated.model_dump(), ""
    except ValidationError as e:
        return None, _format_validation_error(e)


_RETRY_SHORTEN_HINT = (
    "\n\nIMPORTANT: Your previous attempt was cut off or did not match the required schema. "
    "Respond again with a SHORTER, COMPLETE JSON object matching the schema exactly: keep "
    "extraction.description to at most 60 words, at most 4 factor items per list, and at most "
    "40 words per explanation. Include all required fields: extraction (name, website, "
    "company_type) and scores (fit, success). Never truncate the "
    "JSON — every string and bracket must be closed."
)

_MAX_ATTEMPTS = 10
_BACKOFF_CAP = 16.0
_STEP_BUDGET_SECONDS = max(60, WORKER_JOB_TIMEOUT - 60)


class AnalyzeCompanyNode:
    def __init__(self, llm_service: Any | None = None, event_publisher: Any | None = None):
        self._llm = llm_service
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        progress_ops.update_step(self._events, state, NODE_ID, 30)

        company_text = state.analysis_context.get("company_text") or ""
        company_type = state.analysis_context.get("company_type") or "UNKNOWN"
        scoring_rules = state.analysis_context.get("scoring_rules") or ""
        resume_text = state.analysis_context.get("resume_text") or ""
        profile_documents = state.analysis_context.get("profile_documents") or ""
        target_countries = state.analysis_context.get("target_countries") or "your target countries"

        if not company_text:
            state.errors.append(f"[{NODE_ID}] No company content to analyze for {state.company_id}")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        prompt = build_company_analysis_prompt(
            company_text, company_type, scoring_rules, resume_text=resume_text,
            profile_documents=profile_documents, target_countries=target_countries,
        )
        schema = build_company_analysis_output_schema()
        llm = self._llm or get_llm_service()

        payload, reason = self._obtain_valid_payload(llm, prompt, schema)
        if payload is None:
            return self._fail(state, reason)

        progress_ops.update_step(self._events, state, NODE_ID, 80)
        payload["prompt_version"] = COMPANY_ANALYSIS_PROMPT_VERSION
        payload["schema_version"] = COMPANY_ANALYSIS_SCHEMA_VERSION
        state.analysis_context["raw_payload"] = payload
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _obtain_valid_payload(
        self, llm: Any, prompt: str, schema: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, str]:
        """Run the LLM with retries until the response validates or the time budget is exhausted.

        Uses exponential backoff between retries and respects a total time
        budget derived from ``WORKER_JOB_TIMEOUT`` so that transient format
        errors do not fail the execution in seconds.
        """
        deadline = time.monotonic() + _STEP_BUDGET_SECONDS
        last_reason = ""

        for attempt in range(_MAX_ATTEMPTS):
            if attempt > 0:
                backoff = min(2.0 ** (attempt - 1), _BACKOFF_CAP)
                time.sleep(backoff)

            if time.monotonic() >= deadline:
                break

            remaining = deadline - time.monotonic()
            call_timeout = max(30, min(int(remaining), 240))
            prompt_to_use = prompt if attempt == 0 else prompt + _RETRY_SHORTEN_HINT

            try:
                resp = llm.generate_structured(prompt_to_use, schema=schema, timeout=call_timeout)
            except Exception as e:
                if not _is_json_parse_error(e):
                    return None, f"LLM call failed: {e}"
                last_reason = "the response was not parseable JSON"
                continue

            payload, reason = self._validate(resp)
            if payload is not None:
                return payload, ""
            last_reason = reason

        return None, last_reason or "exhausted retries"

    @staticmethod
    def _validate(resp: Any) -> tuple[dict[str, Any] | None, str]:
        if resp is None:
            return None, "the response was not parseable JSON"
        return _extract_valid_payload(resp.content)

    def _fail(self, state: CompanyProcessingState, reason: str) -> CompanyProcessingState:
        state.errors.append(f"[{NODE_ID}] {CLEAN_FAILURE_MESSAGE} ({reason})")
        state.status = ExecutionStatus.FAILED
        progress_ops.fail_step(self._events, state, NODE_ID, CLEAN_FAILURE_MESSAGE)
        return state
