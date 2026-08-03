# AI Workflows

## Purpose

This document describes the AI workflow architecture.

AI workflows define how complex processing tasks are orchestrated using LangGraph.

A workflow is responsible for coordinating multiple processing steps such as:

- Data fetching
- Content extraction
- Analysis
- LLM execution
- Scoring
- Insight generation

---

# Workflow Architecture

The workflow execution architecture:

API

↓

ProcessingExecution

↓

TaskIQ Background Task

↓

LangGraph Workflow

↓

Workflow Nodes

↓

LLM Providers / Tools

↓

Result

---

# Workflow Engine

LangGraph is the workflow execution engine.

LangGraph provides:

- Graph-based execution
- Node orchestration
- State management
- Checkpointing
- Recovery
- Resumable execution

Workflows should not be implemented as manually chained function calls.

---

# Workflow Responsibilities

A workflow is responsible for:

- Defining execution steps
- Connecting processing nodes
- Managing workflow transitions
- Coordinating tools and providers
- Producing intermediate results

A workflow is not responsible for:

- Queue management
- Worker lifecycle
- User authorization
- Job lifecycle management

---

# Relationship With ProcessingExecution

Each workflow execution belongs to a ProcessingExecution.

Relationship:

Job

|

ProcessingExecution

|

LangGraph Workflow Run

ProcessingExecution manages:

- Execution lifecycle
- User-visible status
- Failure state

LangGraph manages:

- Workflow state
- Node execution
- Checkpoints

---

# Workflow State

Workflow state is owned by LangGraph.

The state contains:

- Current node
- Intermediate results
- Tool outputs
- LLM responses
- Temporary workflow data
- Execution context

Workflow state should not be stored inside Job entities.

---

# Checkpointing

LangGraph checkpoints allow workflows to:

- Resume after failures
- Continue interrupted executions
- Persist intermediate state

Checkpoint data is separate from business data.

Business data:

PostgreSQL

Workflow state:

LangGraph checkpoint storage

---

# Workflow Nodes

A workflow consists of multiple nodes.

Example:

Job URL

↓

Fetch Content Node

↓

Extract Information Node

↓

Analyze Content Node

↓

LLM Analysis Node

↓

Score Generation Node

↓

Career Guidance Node

Each node:

- Receives workflow state
- Performs one responsibility
- Updates workflow state

---

# Job Processing Workflow

A job processing run is executed by **two LangGraph phases** inside a single
ProcessingExecution (`POST /api/jobs/{id}/process`):

## Phase 1 — JobContextPreparationGraph (no LLM)

`processing/application/workflows/job_context_preparation/graph.py`

```
START → load_job → collect_sources → fetch_sources → extract_content
      → build_context → validate_context → persist_context
      → context_ready | execution_failed → END
```

No LLM calls. `persist_context` writes the combined text to the job row
(`raw_description` + `description`) via `JobService.persist_prepared_context`
so the analysis phase has a durable LLM input.

## Phase 2 — JobAnalysisGraph (exactly one LLM call)

`processing/application/workflows/job_analysis/graph.py`

```
START → load_context → prepare_profile → analyze → extract_skills → score
      → recommend → summarize → persist
      → analysis_ready | execution_failed → END
```

Exactly **one LLM call** per job: `analyze` runs the versioned `job.analyze`
prompt (`processing/application/services/job_analysis_prompt.py`) via
`LLMService.generate_structured(prompt, schema=…, timeout=240)`. Scoring and
recommendation are deterministic (`processing/application/services/job_analysis_scoring.py`):
scores clamped 0-100, `overall = round(fit*0.6 + success*0.4)`,
`apply` ≥ 80 / `consider` ≥ 60 / else `skip`. `persist` writes the `jobs` row
projection, the `summaries` row (legacy grade via `grade_for_overall`), and
the canonical `job_analysis` table (schema `job`).

If Phase 1 ends with `execution_failed`, Phase 2 is skipped.

The runner (`processing/infrastructure/runner/execution_runner.py`) runs
Phase 1, then — when the result is not `FAILED` — builds and invokes the
analysis graph with the same `JobProcessingState`.

Both phases share one user-facing workflow (`WORKFLOW_ID="job_processing"`,
`WORKFLOW_NAME="Job Processing") with 13 steps; internal nodes
(`load_context`, `prepare_profile`, `execution_failed`, `context_ready`,
`analysis_ready`) stay hidden from the frontend.

---

# Tool Integration

Workflow nodes can use tools.

Examples:

- Web fetching
- Search providers
- Data extraction tools
- LLM providers

Tools are called by workflow nodes.

---

# Failure Handling

Failures can happen at different levels.

## Task Execution Failure

Examples:

- Worker crash
- Redis unavailable

Handled by:

- TaskIQ retry mechanism

## Workflow Failure

Examples:

- Invalid state
- Provider failure
- Node execution error

Handled by:

- LangGraph checkpoints
- Workflow recovery

## Business Failure

Examples:

- Invalid job data
- Missing required information

Handled by:

- Domain validation

---

# Progress Reporting

Workflow progress is exposed through events.

Flow:

LangGraph Node

↓

Workflow Event

↓

Processing Event

↓

SSE

↓

Frontend

Related:

docs/api/sse/processing-events.md

---

# Workflow Lifecycle

Created

↓

Initialized

↓

Running

↓

Checkpointed

↓

Completed

or

Running

↓

Failed

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/queue/processing/taskiq-processing.md
- docs/ai/langgraph.md
- docs/ai/langgraph-state.md
