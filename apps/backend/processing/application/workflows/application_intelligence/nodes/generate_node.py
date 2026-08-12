"""GenerateNode — the single LLM call for an application artifact.

Runs one of the three generators (preparation / resume / cover letter) via
LLMService — the only sanctioned way to call a provider. The response is
strictly validated against the matching Pydantic output model before it is
accepted; anything else (retry once) fails with a clean, user-facing message.

Emits mid-call progress updates so the frontend sees live progress.
"""

from __future__ import annotations

import json
from typing import Any

from ai.infrastructure.service import get_llm_service
from pydantic import ValidationError

from processing.application.services.application_intelligence_prompts import (
    APPLICATION_INTELLIGENCE_PROMPT_VERSION,
    APPLICATION_INTELLIGENCE_SCHEMA_VERSION,
    build_cover_letter_prompt,
    build_document_output_schema,
    build_resume_prompt,
)
from processing.application.services.application_intelligence_validation import (
    DocumentOutput,
)
from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus, ExecutionType
from processing.domain.workflow.application_intelligence_state import (
    ApplicationIntelligenceState,
)

NODE_ID = "generate"

CLEAN_FAILURE_MESSAGE = "The AI returned a result that does not match the required format."


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
    msg = str(exc)
    return "Failed to parse" in msg and "JSON output" in msg


def _format_validation_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    loc = ".".join(str(part) for part in first.get("loc", ())) or "payload"
    return f"invalid field '{loc}': {first.get('msg', 'invalid value')}"


class GenerateNode:
    def __init__(self, llm_service: Any | None = None, event_publisher: Any | None = None):
        self._llm = llm_service
        self._events = event_publisher

    def __call__(self, state: ApplicationIntelligenceState) -> ApplicationIntelligenceState:
        progress_ops.start_step(self._events, state, NODE_ID)
        progress_ops.update_step(self._events, state, NODE_ID, 30)

        prompt, schema = self._plan_for(state.intent, state.context)
        if prompt is None:
            state.errors.append(f"[{NODE_ID}] Unsupported intent: {state.intent}")
            state.status = ExecutionStatus.FAILED
            progress_ops.fail_step(self._events, state, NODE_ID, CLEAN_FAILURE_MESSAGE)
            return state

        llm = self._llm or get_llm_service()
        payload, reason = self._obtain_valid_payload(state.intent, llm, prompt, schema)
        if payload is None:
            return self._fail(state, reason)

        progress_ops.update_step(self._events, state, NODE_ID, 80)
        payload["prompt_version"] = APPLICATION_INTELLIGENCE_PROMPT_VERSION
        payload["schema_version"] = APPLICATION_INTELLIGENCE_SCHEMA_VERSION
        state.result = payload
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    @staticmethod
    def _plan_for(intent: str, context: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
        if intent == ExecutionType.APPLICATION_RESUME:
            return build_resume_prompt(context), build_document_output_schema()
        if intent == ExecutionType.APPLICATION_COVER_LETTER:
            return build_cover_letter_prompt(context), build_document_output_schema()
        return None, None

    def _obtain_valid_payload(
        self,
        intent: str,
        llm: Any,
        prompt: str,
        schema: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str]:
        first_reason = ""
        resp = None
        try:
            resp = llm.generate_structured(prompt, schema=schema, timeout=240)
        except Exception as e:
            if not _is_json_parse_error(e):
                return None, f"LLM call failed: {e}"
            first_reason = "the response was not parseable JSON"

        payload, reason = self._validate(intent, resp)
        if payload is not None:
            return payload, ""

        try:
            resp = llm.generate_structured(
                prompt + _RETRY_SHORTEN_HINT, schema=schema, timeout=240
            )
        except Exception as e:
            return None, reason or first_reason or f"LLM retry failed: {e}"

        payload, retry_reason = self._validate(intent, resp)
        if payload is not None:
            return payload, ""
        return None, reason or retry_reason or first_reason or "unparseable response"

    @staticmethod
    def _validate(intent: str, resp: Any) -> tuple[dict[str, Any] | None, str]:
        if resp is None:
            return None, "the response was not parseable JSON"
        payload = _coerce_payload(resp.content)
        if not payload:
            return None, "the response was not parseable JSON"
        try:
            return DocumentOutput.model_validate(payload).dump_payload(), ""
        except ValidationError as e:
            return None, _format_validation_error(e)

    def _fail(self, state: ApplicationIntelligenceState, reason: str) -> ApplicationIntelligenceState:
        state.errors.append(f"[{NODE_ID}] {CLEAN_FAILURE_MESSAGE} ({reason})")
        state.status = ExecutionStatus.FAILED
        progress_ops.fail_step(self._events, state, NODE_ID, CLEAN_FAILURE_MESSAGE)
        return state


_RETRY_SHORTEN_HINT = (
    "\n\nIMPORTANT: Your previous attempt was cut off or did not match the required schema. "
    "Respond again with a SHORTER, COMPLETE JSON object matching the schema exactly: keep "
    "every list short (at most 5 hard_skills, 3 soft_skills, 3 items per list) and every "
    "string to at most 40 words. Never truncate the JSON — every string and bracket must "
    "be closed."
)
