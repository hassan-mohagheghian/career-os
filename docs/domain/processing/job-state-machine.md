# Job State Machine

## Purpose

This document describes the lifecycle of a Job entity.

The Job state machine represents the business state of a job.

It is separate from:

- ProcessingExecution lifecycle
- TaskIQ execution state
- LangGraph workflow state

---

# State Ownership

Job state belongs to the domain model.

Job state represents:

- Availability of the job
- Processing readiness
- Business lifecycle

ProcessingExecution represents:

- A single processing attempt
- Execution progress
- Workflow execution

A Job can have multiple ProcessingExecutions.

---

# Relationship Between Job and ProcessingExecution

Job

|

+-- ProcessingExecution #1

|

+-- ProcessingExecution #2

|

+-- ProcessingExecution #3

The Job lifecycle does not depend on the background execution technology.

---

# Job States

## Created

The job has been created.

No processing has started.

Transitions:

Created

↓

Ready

---

## Ready

The job contains enough information to start processing.

Possible actions:

- Start processing
- Update job information

Transition:

Ready

↓

Processing

---

## Processing

A processing execution is currently running.

Important:

This state does not mean a worker is running.

It means the job has an active ProcessingExecution.

Flow:

Job

↓

ProcessingExecution Created

↓

TaskIQ Execution

↓

LangGraph Workflow

---

## Completed

Processing finished successfully.

The job contains generated results.

---

## Failed

Processing failed.

Failure information belongs to:

- ProcessingExecution
- Error metadata

The job can potentially be retried by creating a new ProcessingExecution.

---

# State Diagram

Created

↓

Ready

↓

Processing

↓

Completed

or

Processing

↓

Failed

---

# Processing Integration

When a job starts processing:

1. Create ProcessingExecution

Status:

created

2. Dispatch TaskIQ task

3. ProcessingExecution moves to:

queued

4. Worker starts workflow

5. ProcessingExecution moves to:

running

6. LangGraph executes the workflow (two phases):

- Phase 1 — JobContextPreparationGraph: load_job → collect_sources →
  fetch_sources → extract_content → build_context → validate_context →
  persist_context → context_ready | execution_failed (no LLM)
- Phase 2 — JobAnalysisGraph: load_context → prepare_profile → analyze →
  extract_skills → score → recommend → summarize → persist →
  analysis_ready | execution_failed (exactly one LLM call: job.analyze)

7. Job state updates after successful completion

---

# Retry Model

Retries do not reset the Job lifecycle.

Example:

Job

State:

Failed

New ProcessingExecution created:

ProcessingExecution #2

↓

Queued

↓

Running

↓

Completed

Job:

Failed

↓

Processing

↓

Completed

The failed attempt (ProcessingExecution #1) is **cancelled** when the retry is
created, so it leaves the queue's Failed section. The platform keeps a single
active execution per job (queued / processing / failed); a new execution is
refused with HTTP 409 while one is already active.

---

# TaskIQ Relationship

TaskIQ manages execution infrastructure only.

TaskIQ states:

- queued
- running
- retrying
- failed

These states should not become Job domain states.

---

# LangGraph Relationship

LangGraph manages workflow execution state.

Examples:

- current node
- checkpoint
- intermediate data
- workflow recovery

LangGraph state does not replace Job state.

---

# Events

Job lifecycle events:

## JobCreated

A new job was created.

## JobReady

The job is ready for processing.

## JobProcessingStarted

A processing execution started.

## JobCompleted

Processing finished successfully.

## JobFailed

Processing failed.

---

# Persistence

Job state is stored in PostgreSQL.

ProcessingExecution state is also stored separately.

Example:

jobs table:

- id
- status

processing_executions table:

- id
- job_id
- status
- workflow_id

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/queue/processing/taskiq-processing.md
- docs/ai/langgraph-state.md
