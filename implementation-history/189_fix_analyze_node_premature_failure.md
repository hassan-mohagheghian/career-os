# Prompt 189 - Fix analyze node premature failure

## Objective

The "Analyze Job" / "Analyze Company" LLM steps fail after only 2 attempts (potentially within seconds) when the LLM returns invalid JSON or a response that doesn't match the required Pydantic schema. The configured timeout (`WORKER_JOB_TIMEOUT=600s`) is not utilized as a retry budget. The execution appears in the "Failed" section after a few seconds instead of utilizing the full timeout.

## Current State

- `analyze_node.py:_obtain_valid_payload()` makes exactly 2 LLM calls (initial + 1 retry with `_RETRY_SHORTEN_HINT`), each with `timeout=240`
- If both fail (e.g., LLM returns truncated JSON quickly), the node sets `state.status = FAILED` and the execution ends up failed in seconds
- Same pattern exists in `analyze_company_node.py`
- `process_execution_task` has `retry_on_error=True, retry_count=3` which retries the whole task, but on retry the same workflow failure repeats deterministically
- The runner (`execution_runner.py:172-189`) marks execution as FAILED on any exception and re-raises for TaskIQ retry — but the execution is already FAILED in DB before the retry starts

## Implementation Steps

### 1. Refactor `analyze_node.py:_obtain_valid_payload()` — time-budgeted retry loop

Replace the fixed 2-attempt retry with a loop that uses a time budget:

```python
import time
from shared.infrastructure.taskiq.config import WORKER_JOB_TIMEOUT

_MAX_ATTEMPTS = 10
_BACKOFF_CAP = 16.0
_STEP_BUDGET_SECONDS = WORKER_JOB_TIMEOUT - 60  # leave 60s buffer for other steps

def _obtain_valid_payload(self, llm, prompt, schema):
    """Run the LLM with retries until valid or budget exhausted."""
    deadline = time.monotonic() + self._STEP_BUDGET_SECONDS
    last_reason = ""

    for attempt in range(self._MAX_ATTEMPTS):
        if attempt > 0:
            backoff = min(2.0 ** (attempt - 1), self._BACKOFF_CAP)
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
                last_reason = f"LLM call failed: {e}"
                continue
            last_reason = "the response was not parseable JSON"
            continue

        payload, reason = self._validate(resp)
        if payload is not None:
            return payload, ""
        last_reason = reason

    return None, last_reason or "exhausted retries"
```

Key properties:
- If LLM fails fast (seconds), retries ~10 times within the budget
- If LLM hangs near 240s timeout, fewer retries but still respects budget
- Exponential backoff prevents hammering the provider
- Uses `WORKER_JOB_TIMEOUT` from env as the budget source

### 2. Same refactoring for `analyze_company_node.py`

Apply the identical `_obtain_valid_payload` pattern to `analyze_company_node.py`.

### 3. Add retry logging

Each retry attempt logs at `info` level with attempt number, elapsed time, and failure reason — aids debugging without overwhelming logs.

### 4. Update existing tests

The existing tests in `test_job_analysis.py` assert exact call counts (e.g., `len(llm.calls) == 2`). Update these tests to account for the new retry behavior:

- `test_retries_once_on_json_parse_failure_then_succeeds` → still expects 2 calls (succeeds on retry, so loop stops)
- `test_no_retry_when_generic_error` → still expects 1 call (non-JSON error, no retry)
- `test_schema_invalid_output_fails_with_clean_message` → now expects more calls (retries up to budget)
- `test_schema_invalid_once_then_valid_retries` → still expects 2 calls (succeeds on retry)
- `test_schema_invalid_twice_fails` → now expects more calls (retries up to budget)
- Add new test: `test_retries_within_time_budget` — verifies the loop respects the deadline
- Add new test: `test_non_json_error_stops_immediately` — verifies non-format errors don't retry

## Files to Modify

- `apps/backend/processing/application/workflows/job_analysis/nodes/analyze_node.py`
- `apps/backend/processing/application/workflows/company_analysis/nodes/analyze_company_node.py`
- `apps/backend/tests/processing/application/test_job_analysis.py`

## Files NOT Modified (and why)

- `execution_runner.py` — runner's retry-on-exception logic is still useful for infrastructure failures (Redis down, network blip). The analyze node's internal retries handle format errors; the runner/TaskIQ retries handle infrastructure errors.
- `tasks.py` — keep `retry_on_error=True, retry_count=3` for infrastructure resilience. The analyze node now retries internally, so workflow format errors don't reach TaskIQ retry (they're exhausted within the node).
- `reconcile_stuck_executions` — no changes needed; heartbeat mechanism is correct.

## Testing Requirements

1. Run `uv run pytest apps/backend/tests/processing/ -v` to verify no regressions
2. Verify the analyze node retries (check logs for retry attempts)
3. Verify the analyze node respects the time budget (doesn't run indefinitely)
4. Verify the analyze node still fails cleanly after budget exhaustion

## Constraints

- Follow DDD boundaries (no cross-context imports beyond what already exists)
- Use `structlog` for logging (no `print()`)
- The analyze node is in `processing.application.workflows` — can import from `shared.infrastructure.taskiq.config` for `WORKER_JOB_TIMEOUT`
- Keep the existing `CLEAN_FAILURE_MESSAGE` constant and error format for frontend compatibility
