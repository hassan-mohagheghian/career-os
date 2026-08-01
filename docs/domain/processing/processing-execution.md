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
