# Processing Domain Events

## Purpose

This document describes domain events generated during processing execution.

Domain events represent important changes in the processing lifecycle.

They allow different parts of the system to react without creating direct dependencies.

Domain events are independent from:

- TaskIQ
- Redis
- SSE transport
- Frontend implementation
- LangGraph implementation

---

# Event Architecture

Event flow:

ProcessingExecution

↓

Domain Event

↓

Event Handler

↓

Consumers

Examples:

- Persistence
- Notifications
- SSE publishing
- Analytics

---

# Event Categories

Processing events are divided into two categories:

1. Execution Lifecycle Events
2. Workflow Progress Events

---

# Execution Lifecycle Events

These events represent changes in ProcessingExecution.

## ProcessingExecutionCreated

Triggered when a new execution is created.

Payload:

- execution_id
- job_id
- created_at

---

## ProcessingExecutionQueued

Triggered when execution is dispatched for background processing.

Payload:

- execution_id
- queued_at

Note:

This event does not depend on TaskIQ.

TaskIQ is only the current execution mechanism.

---

## ProcessingExecutionStarted

Triggered when processing begins.

Payload:

- execution_id
- started_at

---

## ProcessingExecutionCompleted

Triggered after successful completion.

Payload:

- execution_id
- completed_at

---

## ProcessingExecutionFailed

Triggered when execution fails — either from a workflow error (the runner publishes
the exception message) or from `reconcile_stuck_executions` when a RUNNING execution
has exceeded `WORKER_JOB_TIMEOUT` (default 600s) since `started_at`. The reconcile
timeout message is plain and honest: `"Execution timed out after {elapsed}s. Check
status or retry."` (it makes no claim about worker liveness).

Payload:

- execution_id
- error_message
- failed_at

---

# Workflow Events

Workflow events represent progress inside LangGraph execution.

Examples:

## WorkflowStarted

The LangGraph workflow has started.

Payload:

- execution_id
- workflow_id

---

## WorkflowNodeStarted

A workflow node started execution.

Payload:

- execution_id
- node_name

---

## WorkflowNodeCompleted

A workflow node completed.

Payload:

- execution_id
- node_name
- result_metadata

---

## WorkflowProgressUpdated

Workflow progress changed.

Payload:

- execution_id
- stage
- progress

---

## WorkflowCompleted

Workflow finished successfully.

---

## WorkflowFailed

Workflow execution failed.

Payload:

- execution_id
- node_name
- error

---

# Event Ownership

## Domain Layer

Owns:

- ProcessingExecution lifecycle events

Examples:

- Created
- Queued
- Started
- Completed
- Failed

---

## Workflow Layer

Owns:

- Workflow execution events

Examples:

- Node started
- Node completed
- Workflow progress

---

## Infrastructure Layer

Consumes events for:

- SSE publishing
- Logging
- Metrics
- Notifications

---

# Event Persistence

Not all events need permanent storage.

## Persistent Events

Examples:

- Execution created
- Execution completed
- Execution failed

Stored in PostgreSQL.

## Temporary Events

Examples:

- Node progress
- Intermediate workflow updates

May be stored through:

- LangGraph checkpoints
- Event streaming mechanisms

---

# SSE Integration

SSE consumes events but does not create them.

Flow:

Domain Event

↓

Event Handler

↓

SSE Publisher

↓

Frontend Client

The frontend only receives events through the API layer.

---

# TaskIQ Integration

TaskIQ does not produce domain events directly.

Incorrect:

TaskIQ Worker

↓

TaskIQ Event

↓

Frontend

Correct:

TaskIQ Worker

↓

ProcessingExecution Update

↓

Domain Event

↓

SSE

---

# Example Processing Flow

1. API creates execution

Event:

ProcessingExecutionCreated

2. TaskIQ task dispatched

Event:

ProcessingExecutionQueued

3. Worker starts workflow

Event:

ProcessingExecutionStarted

4. LangGraph nodes execute

Events:

WorkflowNodeStarted

WorkflowNodeCompleted

5. Workflow finishes

Event:

ProcessingExecutionCompleted

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/api/sse/processing-events.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/queue/processing/taskiq-processing.md
- docs/ai/langgraph-state.md
