# ADR-020: Execution Queue (SSE) vs Legacy LLM Pipeline

## Status

Proposed

## Date

2026-08-02

## Context

The system currently has two largely parallel "processing worlds" for jobs:

1. **v2 ProcessingExecution queue (SSE world)** — the modern path used by the
   v2 frontend. Triggered by `POST /api/jobs/{id}/process`, it
   creates a `ProcessingExecution`, dispatches the `process_execution_task`
   through TaskIQ, and runs the `JobContextPreparationGraph`. This path
   publishes lifecycle + step events over SSE (`/events/processing`) and is
   consumed by `useProcessingEvents` and the Processing Drawer.

   The `JobContextPreparationGraph` explicitly **must not include LLM calls**
   (`processing/application/workflows/job_context_preparation/graph.py`).

2. **Legacy LLM pipeline (Socket.IO world).** Triggered by
   `POST /api/pending/{id}/process`, dispatched as `process_job_task`, and
   run by `JobWorker._execute_pipeline` over `build_job_processing_graph`.
   This path performs full LLM extraction, analysis, scoring, and DB
   persistence, and reports real-time progress over Socket.IO.

Consequence: the modern SSE queue currently **stops at context preparation**.
LLM analysis, scoring, and persistence still live on the legacy Socket.IO
path. Real-time progress therefore does not reach the end of the pipeline on
the channel the current UI uses.

## Decision

Consolidate job processing onto a single pipeline that runs to completion on
the **v2 ProcessingExecution queue over SSE**, and retire the legacy
Socket.IO job path.

Specifically:

1. Extend the `JobContextPreparationGraph` (or the execution runner that
   drives it) with the remaining stages:

   - LLM extraction of structured fields (`LLMService.generate_structured`).
   - Job analysis.
   - Fit / Success / Overall scoring (`overall = fit * 0.6 + success * 0.4`).
   - Persistence of the job and its summary via the repositories.

2. Route each new stage through `RedisProcessingEventPublisher` so pipeline
   progress (and the record of LLM analysis + persistence) is streamed over
   the existing SSE `/events/execution` channel — the channel the v2
   frontend already subscribes to.

3. The execution graph remains the single source of truth for workflow
   progress, mirroring the LangGraph-owns-state principle from ADR-012.

4. The legacy `process_job_task` / `JobWorker` Socket.IO path is then
   deprecated and, once the v2 path is verified, removed.

## Consequences

### Positive

- One end-to-end queue from the frontend click to the saved, scored job,
  with progress visible instantly along the whole pipeline.
- Single real-time channel (SSE) for the v2 UI; no Socket.IO/SSE split.
- Removes duplicate business logic across the two worker/graph families.
- Progress + LLM outputs all represented in `WorkflowProgress`
  (`docs/domain/processing/workflow-progress.md`).

### Negative

- The `JobContextPreparationGraph` "no LLM" invariant must be deliberately
  changed; design must keep preparation (fetch/extract) cleanly separated
  from LLM analysis so the prep graph can be tested and reused without a
  provider.
- Moving scoring + persistence into the execution flow reproduces behavior
  tests may already guarantee coverage for in the legacy path.
- Requires verified migration off the legacy Socket.IO job path and its
  tests (may include `jobs-v2` vs legacy UI coexistence).

## References

- `docs/domain/processing/processing-execution.md`
- `docs/domain/processing/workflow-progress.md`
- `docs/domain/processing/job-state-machine.md`
- `docs/workflows/job-processing.md` (realized trace-through + two-path note)
- `docs/api/sse/processing-events.md`
- `docs/adr/019-taskiq-migration.md`
- `docs/adr/012-job-lifecycle.md`