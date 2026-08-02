# Job Processing Workflow

## Purpose

This document describes the workflow responsible for processing jobs.

The workflow analyzes job information, extracts relevant data, uses AI providers, and generates scoring and career guidance.

---

# Architecture Flow

Job

↓

ProcessingExecution

↓

TaskIQ Worker

↓

LangGraph Workflow

↓

Processing Nodes

↓

Result

---

# Workflow Responsibilities

The job processing workflow is responsible for:

- Collecting job information
- Extracting structured data
- Running AI analysis
- Generating job score
- Generating career guidance
- Persisting final results

---

# Workflow Graph

START

↓

Load Job Context

↓

Fetch External Data

↓

Extract Information

↓

Normalize Data

↓

Analyze Job

↓

Generate Score

↓

Generate Career Guidance

↓

Persist Result

↓

END

---

# Node Description

## Load Job Context

Loads job information from the domain layer.

Input:

- job_id
- execution_id

Output:

- job context

---

## Fetch External Data

Retrieves additional information.

Examples:

- Company website
- External resources
- Job descriptions

Output:

- External content

---

## Extract Information

Transforms raw content into structured information.

Examples:

- Required skills
- Experience level
- Responsibilities
- Technologies

---

## Normalize Data

Creates consistent workflow input.

Examples:

- Skill normalization
- Category mapping

---

## Analyze Job

Uses AI capabilities to analyze the job.

Examples:

- Difficulty estimation
- Skill analysis
- Market relevance

---

## Generate Score

Generates job intelligence score.

Examples:

- Career fit score
- Skill match score
- Opportunity score

---

## Generate Career Guidance

Generates recommendations.

Examples:

- Required improvements
- Learning path
- Career direction

---

## Persist Result

Stores final business results.

Stored in:

PostgreSQL

---

# Workflow State

Workflow state contains:

- Job context
- Extracted information
- Analysis results
- LLM responses
- Generated insights

Workflow state is managed by LangGraph.

---

# ProcessingExecution Integration

Each workflow execution belongs to a ProcessingExecution.

ProcessingExecution tracks:

- Status
- Lifecycle
- Failure state

LangGraph tracks:

- Workflow progress
- Node execution
- Checkpoints

---

# Failure Handling

## External Data Failure

Example:

- Website unavailable

Handled by:

- Node retry
- Alternative sources

---

## LLM Failure

Example:

- Provider unavailable

Handled by:

- Retry policy
- Provider fallback

---

## Workflow Failure

Example:

- Invalid state

Handled by:

- LangGraph checkpoint recovery

---

# Progress Events

Workflow nodes emit progress events.

Example:

Fetch Data Started

↓

Extract Started

↓

Analysis Started

↓

Scoring Started

↓

Completed

Events are delivered through SSE.

Related:

docs/api/sse/processing-events.md

---

# Realized Trace-Through

How a single job URL moves through the system today, from the frontend
click to the live progress stream. Each step is a verified wiring of the
current implementation (paths + line numbers).

## 1. Frontend — user submits a job URL and starts processing

- Add-job form: `apps/frontend/src/features/jobs/components/AddJobForm.tsx`
  `handleSubmit` (line 67) → `useCreateJob().createJob` →
  `POST /api/jobs` (`apps/frontend/src/features/jobs/hooks/useCreateJob.ts`
  line 36). This creates the job record only.
- Start processing: `apps/frontend/src/widgets/jobs-page-v2/index.tsx`
  `handleProcessV2` (line 42) calls `processMutation.mutate(id)` then opens
  the Processing Drawer. The mutation uses `jobApi.processJob`
  (`apps/frontend/src/entities/job/api.ts` line 56) → `POST /api/jobs/{jobId}/process`.
- Live progress is consumed globally by `useProcessingEvents()`
  (`apps/frontend/src/widgets/jobs-page-v2/index.tsx` line 33), hook in
  `apps/frontend/src/shared/hooks/useProcessingEvents.ts` (SSE_URL = `/events/processing`, line 8).

## 2. API route — receive the process request

`apps/backend/processing/presentation/api/process_router.py` — `process_job`
(line 21, `POST /api/jobs/{jobId}/process`):

1. Resolves the job (line 26).
2. `CreateProcessingExecutionUseCase(...).execute(...)` creates a
   `ProcessingExecution` of type `JOB_PROCESSING` (lines 33-39).
3. `DispatchProcessingExecutionService(exec_repo).dispatch(execution_id)`
   (line 41) sets status `QUEUED` and enqueues the task.

## 3. Dispatch + TaskIQ queue

- `shared/infrastructure/taskiq/client.py` — `enqueue_execution_sync` pushes
  the task id onto the broker.
- `shared/infrastructure/taskiq/config.py` — `RedisStreamBroker`.
- `shared/infrastructure/taskiq/tasks.py` — `process_execution_task`
  (line 76) runs `ProcessingExecutionRunner.run(execution_id)` via
  `asyncio.to_thread` (line 90).

## 4. Worker — ProcessingExecution runner

`apps/backend/processing/infrastructure/runner/execution_runner.py` —
`ProcessingExecutionRunner.run` (line 43):

- Marks the execution `RUNNING`, initializes `workflow_progress`, and
  publishes the `EXECUTION_STARTED` event (lines 60-70).
- Dispatches to `_run_workflow` (line 73).
- Publishes `EXECUTION_COMPLETED` / `EXECUTION_FAILED` (lines 99-105 / 82-89).

`_run_workflow` (line 123) delegates to `build_job_context_preparation_graph`
(line 141) and `graph.invoke(state)` (line 147).

## 5. Workflow — extraction / content prep (no LLM)

`apps/backend/processing/application/workflows/job_context_preparation/graph.py`:

- Node chain (lines 66-99): `load_job → collect_sources → fetch_sources →
  extract_content → build_context → validate_context → context_ready | execution_failed`.
- Graph docstring (line 12): "This phase must NOT include any LLM calls."

`apps/backend/processing/infrastructure/workflow/assembly.py` —
`build_job_context_preparation_graph` (line 26) wires the real infrastructure:

- `CompositeContentFetcher([HTTPXContentFetcher(), PlaywrightContentFetcher()])` (lines 31-33).
- `CompositeContentExtractor([TrafilaturaContentExtractor(), BeautifulSoupContentExtractor()])` (lines 34-36).
- `RedisProcessingEventPublisher()` (line 37).

## 6. SSE progress — emit and consume

- Publishing: `apps/backend/shared/infrastructure/events/processing_events.py`
  `publish_sync` (line 123); per-entity publisher
  `apps/backend/processing/infrastructure/events/redis_processing_event_publisher.py`.
- Gateway: `apps/backend/shared/presentation/api/processing_events_router.py`
  `GET /events/processing` (line 23) → `stream_pattern(CHANNEL_PATTERN)`
  (`shared/infrastructure/events/sse.py`).
- Frontend: `useProcessingEvents.ts` opens `EventSource('/events/processing')`
  and maps events onto the react-query cache (`jobs-v2-infinite`).

---

# Current State: Two Processing Paths (Important)

The realized trace-through above reflects the **v2 ProcessingExecution
queue** (SSE world). An older **legacy LLM pipeline** also exists. They do
not share the same workflow or the same real-time channel today:

| Concern | v2 queue (SSE) | Legacy LLM pipeline (Socket) |
| --- | --- | --- |
| Trigger | `POST /api/jobs/{id}/process` | `POST /api/pending/{id}/process` |
| Task | `process_execution_task` | `process_job_task` |
| Runner | `ProcessingExecutionRunner` | `JobWorker._execute_pipeline` |
| Graph | `JobContextPreparationGraph` (fetch + extract, **no LLM**) | `build_job_processing_graph` (`extract_raw → analyze → score → persist`) |
| Real-time | SSE `/events/processing` | Socket.IO broadcaster |
| LLM + score + save | **not wired here** | present (`LLMService`, `persist_results`) |

Implication: the modern SSE queue today **stops at context preparation**;
LLM analysis, scoring, and DB persistence still live on the legacy
Socket.IO path. See
`docs/adr/020-execution-queue-vs-llm-pipeline.md` for the decision and the
preferred resolution (add LLM analysis/scoring/persist steps to the v2
execution graph so a single SSE stream reaches the end).

---

# Testing

Workflow tests should verify:

- Node behavior
- State transitions
- Failure recovery
- Provider integration
- Final result generation

---

# Related Documents

- docs/ai/workflows.md
- docs/ai/langgraph.md
- docs/ai/langgraph-state.md
- docs/domain/processing/processing-execution.md
- docs/api/processing/process-job.md
- docs/api/sse/processing-events.md
- docs/adr/020-execution-queue-vs-llm-pipeline.md
