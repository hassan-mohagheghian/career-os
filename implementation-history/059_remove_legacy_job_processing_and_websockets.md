# Prompt 059 - Remove Legacy Job Processing Components, APIs, and WebSockets

## Objective

Consolidate job processing onto the modern v2 ProcessingExecution queue over
SSE, then remove the legacy job-processing pipeline.

Scope of removal:

- Legacy components and APIs for job processing.
- The WebSocket (Socket.IO) infrastructure completely.

After this prompt, the job processing API surface is:

- Modern ProcessingExecution + TaskIQ + LangGraph + SSE.
- No WebSocket-based progress.

See `docs/adr/020-execution-queue-vs-llm-pipeline.md` for the decision and
rationale.

---

# Read Documentation First

Before making changes read:

- docs/adr/020-execution-queue-vs-llm-pipeline.md
- docs/adr/019-taskiq-migration.md
- docs/adr/018-background-service.md
- docs/workflows/job-processing.md
- docs/api/sse/processing-events.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/job-state-machine.md
- docs/domain/processing/workflow-progress.md
- docs/ux/flows/jobs/process-job-live.md

---

# Architecture Rules

Follow:

- Modular Monolith architecture.
- DDD boundaries.
- Existing Processing bounded context.

Do not create shared generic progress systems.

Do not keep two execution systems.

---

# Current State

Two parallel job-processing paths exist today:

| Concern | v2 queue (SSE) | Legacy LLM pipeline (Socket.IO) |
| --- | --- | --- |
| Trigger | `POST /api/jobs/{id}/process` | `POST /api/pending/{id}/process` |
| Task | `process_execution_task` | `process_job_task` |
| Runner | `ProcessingExecutionRunner` | `JobWorker._execute_pipeline` |
| Graph | `JobContextPreparationGraph` | `build_job_processing_graph` |
| Real-time | SSE `/events/processing` | Socket.IO broadcaster |
| LLM + score + save | not wired | present (`LLMService`, `persist_results`) |

The v2 queue currently stops at context preparation (no LLM). Before the
legacy path is removed, the v2 execution graph must reach the end of the
pipeline: LLM extraction, analysis, scoring, and persistence, with progress
emitted over SSE.

---

# Implementation Steps

## 1. Complete the v2 Pipeline (LLM + Score + Save)

Extend the execution flow so it no longer stops at context preparation.

Required stages added after context preparation:

1. LLM extraction of structured fields — via `LLMService.generate_structured`.
2. Escrow analysis.
3. Fit / Success / Overall scoring
   (`overall = fit * 0.6 + success * 0.4`).
4. Persistence of the job and summary via the repositories.

Emit a step event for each new stage through
`RedisProcessingEventPublisher` so progress streams over the existing SSE
channel.

## 2. Remove Legacy Backend

Remove the legacy job-processing pipeline and its endpoints/workers:

- `POST /pending`
- `POST /pending/{id}/process`
- `POST /pending/process-all`
- `process_job_task` and the `JobWorker` legacy graph path
- `enqueue_job` helpers used only by the legacy path
- any legacy Socket.IO broadcaster wiring in the app entrypoint

Keep what the v2 path depends on (Shared Kernel, Processing context, LLM,
repositories).

## 3. Remove WebSocket / Socket.IO Completely

- Remove SocketIO registration/entrypoints.
- Remove all emitted WebSocket events for job processing
  (`pending:update|log|complete|error|progress`).
- Remove frontend hooks that depend on SocketIO for jobs
  (`useSocketIO`, `usePending` socket listeners).
- Ensure no route or dependency imports the removed broadcaster.

## 4. Remove Legacy Frontend

- Remove the legacy Add-Job / pending-job UI paths that call the removed
  `/pending` endpoints.
- Keep the v2 jobs list, Processing Drawer, and `useProcessingEvents`.

## 5. Migrate Behavior

- Confirm the v2 path reproduces the legacy pipeline's persistence and
  scoring outputs.
- Update or remove legacy tests (backend + frontend) for the removed
  job-processing surface.

---

## Migration Rule

Follow ADR-020 pre-requisite:

The v2 SSE path must reach the end of the pipeline (analyze → score →
persist) BEFORE deleting the legacy path.

Remove obsolete implementation only after parity is verified.

---

## Testing Requirements

Backend:

- REST API points for the v2 flow still return responses.
- Worker runs JOB_PROCESSING to completion, persistence verified.
- No entry imports the removed Socket.IO broadcaster.

Frontend:

- Jobs list, add job, and processing drawer still render.
- SSE updates.
- No references to removed `useSocketIO` or `/pending` endpoints.
- Remove obsolete tests.

---

## Expected Final Architecture

```
Frontend (jobs-v2)

↓

Rest Snapshot + SSE Stream

↓

Processing Context

↓

ProcessingExecution

↓

TaskIQ Background Task

↓

LangGraph Workflow

    Job Context Prep → LLM Analysis → Score → Persist

↓

WorkflowProgress Mapper
  + step events

↓

Live UI
```

---

## Important Constraints

- Do not create a new workflow.
- Do not add a second execution/visualization system.
- Use the existing Processing + AI contexts.
- All AI calls go through `LLMService`.
- Use SQLAlchemy for persistence.
- No `print()`; use structlog.
- Do not remove the SSE-based real-time visualization.