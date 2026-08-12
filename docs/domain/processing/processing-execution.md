# Processing Execution

## Purpose

This document describes the domain concept of ProcessingExecution.

ProcessingExecution represents one attempt of running a long-running processing operation.

It is responsible for tracking execution lifecycle, status, and domain-level execution information.

ProcessingExecution is independent from:

- TaskIQ
- Redis
- Worker implementation
- LangGraph implementation

---

# Responsibility

ProcessingExecution is responsible for:

- Representing a processing attempt
- Tracking execution status
- Storing execution metadata
- Recording execution timestamps
- Tracking failures
- Exposing execution state to other layers

ProcessingExecution is not responsible for:

- Running background tasks
- Managing queues
- Executing workflows
- Calling external providers

---

# Architecture Position

ProcessingExecution belongs to the domain layer.

Flow:

API

↓

ProcessingExecution

↓

TaskIQ Task

↓

TaskIQ Worker

↓

LangGraph Workflow

↓

Domain Updates

The domain object exists before background execution starts.

---

# Lifecycle

A ProcessingExecution follows this lifecycle:

Created

↓

Queued

↓

Running

↓

Completed

or

Created

↓

Queued

↓

Running

↓

Failed

---

# States

## Created

The execution record has been created.

The workflow has not started yet.

## Queued

The execution has been dispatched for background processing.

A TaskIQ task has been created.

## Running

The worker has started execution.

The workflow is currently processing.

## Completed

The workflow finished successfully.

## Failed

The workflow failed.

Failure information should be stored with the execution.

---

# Domain State Model

Example:

ProcessingExecution

- id
- job_id
- status
- workflow_id
- created_at
- started_at
- completed_at
- failed_at
- error_message

---

# Workflow Integration

ProcessingExecution tracks workflow execution.

LangGraph manages:

- Workflow graph
- Node state
- Checkpoints
- Intermediate results

ProcessingExecution manages:

- Execution lifecycle
- User-visible status
- High-level metadata

---

# Task Execution Integration

TaskIQ interacts with ProcessingExecution through application services.

Example flow:

Application Service

↓

Create ProcessingExecution

↓

Dispatch TaskIQ Task

Worker:

↓

Load ProcessingExecution

↓

Start LangGraph Workflow

↓

Update Execution Status

---

# Events

ProcessingExecution can produce domain events.

Examples:

## ExecutionCreated

Triggered when a new execution is created.

## ExecutionQueued

Triggered when execution is dispatched.

## ExecutionStarted

Triggered when processing begins.

## ExecutionCompleted

Triggered after successful completion.

## ExecutionFailed

Triggered after failure.

---

# Failure Handling

Failures are divided into categories.

## Infrastructure Failures

Examples:

- Worker crash
- Redis unavailable
- Temporary network issues

Handled by:

- TaskIQ retry mechanism

## Domain Processing Failures

Examples:

- Invalid processing input
- Workflow failure
- Provider failure

Stored in:

ProcessingExecution

---

# Persistence

ProcessingExecution is persisted in PostgreSQL.

PostgreSQL stores:

- Execution lifecycle
- Status
- Metadata
- Error information

LangGraph checkpoint storage manages workflow state separately.

---

# Relationship With Job

A Job can have multiple ProcessingExecutions.

Example:

Job

|

+-- ProcessingExecution 1

|

+-- ProcessingExecution 2

|

+-- ProcessingExecution 3

Each execution represents one processing attempt.

---

# Source of Truth for the Job List

ProcessingExecution is the **source of truth** for the processing state shown
in the Jobs list (`GET /api/jobs/list`):

- Each list row carries a projection of the job's **latest** execution
  (id, status, started_at, finished_at) and `job_status = latest.status`.
- The `processing_status` list filter matches only jobs whose latest execution
  (by `created_at`) has the given status.
- Jobs without an execution show `latest_processing_execution = null` and
  `job_status = null`; the legacy `jobs.status` column is not used by the list.

The projection is produced without N+1 queries: the repository batch-loads the
latest execution per target id and resolves status filters with a single window
query (`ROW_NUMBER() OVER (PARTITION BY target_id ORDER BY created_at DESC)`).

---

# Legacy execution types

`ExecutionType` can lose members when a feature is removed (e.g.
`application_preparation` was dropped from the enum when the preparation feature
was deleted). Databases that ran executions before the removal may keep orphaned
rows whose `execution_type` is no longer a valid enum value.

Two safeguards keep those rows from crashing read paths:

1. **Data migration** — `application_003_cleanup_preparation_executions` hard-deletes
   orphaned rows for removed types on upgrade (rule 8: dead completion rows are
   discarded). The DELETE is guarded by a table-exists check because
   `processing_executions` is a startup-created table (`Base.metadata.create_all()`),
   not alembic-managed — CI runs `alembic upgrade head` on a fresh DB before the
   table exists, so the cleanup no-ops there. Irreversible by design.
2. **Defensive parse** — `ProcessingExecution.from_dict` maps any `execution_type`
   string that is not a current enum value to `ExecutionType.LEGACY` instead of
   raising `ValueError`. A `LEGACY` execution is **not dispatchable**: it has no
   runner branch and can never be started or retried, so it only ever appears in
   history/queue listings.

---

# API Exposure

Clients access execution information through APIs.

Examples:

- Execution status endpoint
- SSE progress endpoint

Clients should not access TaskIQ directly.

---

# Related Documents

- docs/api/processing/process-job.md
- docs/api/sse/processing-events.md
- docs/queue/processing/taskiq-processing.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/ai/langgraph-state.md
