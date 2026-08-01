# Process Job API

## Purpose

This document describes the API endpoint responsible for starting job processing.

The API does not execute processing synchronously.

It creates a processing execution and dispatches background execution.

---

# Architecture Flow

The request flow:

Client

↓

Process Job API

↓

Create ProcessingExecution

↓

Dispatch TaskIQ Task

↓

TaskIQ Worker

↓

LangGraph Workflow

↓

SSE Events

---

# Endpoint

## Start Job Processing

POST /api/jobs/{job_id}/process

Starts a new processing execution for a job.

---

# Request

Path parameters:

| Parameter | Type | Description    |
| --------- | ---- | -------------- |
| job_id    | UUID | Job identifier |

Request body:

Optional processing configuration.

Example fields:

- workflow configuration
- provider configuration
- execution options

---

# Response

The API returns immediately after creating the execution.

Response:

- execution identifier
- current status
- event stream URL

Example:

{
execution_id,
status,
events_url
}

---

# Execution Lifecycle

After the API request:

1. ProcessingExecution is created

Status:

created

↓

2. TaskIQ task is dispatched

Status:

queued

↓

3. TaskIQ worker receives task

Status:

running

↓

4. LangGraph workflow starts

↓

5. Workflow produces progress events

↓

6. Execution completes or fails

---

# Background Execution

The API does not:

- Run workflows
- Call LLM providers
- Fetch external URLs
- Execute analysis logic

Those responsibilities belong to:

TaskIQ Worker

and

LangGraph Workflow

---

# TaskIQ Integration

After creating ProcessingExecution:

The application dispatches:

process_job_execution_task(execution_id)

TaskIQ responsibilities:

- Execute background task
- Manage retries
- Run worker process

TaskIQ does not contain business logic.

---

# LangGraph Workflow

The workflow performs processing steps.

Example:

Job Input

↓

Fetch URL

↓

Extract Content

↓

Analyze Content

↓

LLM Processing

↓

Generate Score

↓

Generate Career Guidance

↓

Save Result

---

# Status Response

The API exposes execution status.

Possible states:

- created
- queued
- running
- completed
- failed

The detailed progress is delivered through SSE.

---

# Progress Updates

Clients should subscribe to:

GET /api/processing/{execution_id}/events

Events include:

- execution.started
- workflow.started
- workflow.progress
- workflow.completed
- workflow.failed

---

# Error Handling

## Request Errors

Examples:

- Invalid job identifier
- Missing required data
- Validation failure

Returned immediately by API.

---

## Processing Errors

Examples:

- LLM provider failure
- URL extraction failure
- Workflow node failure

Handled asynchronously.

The client receives:

- workflow.failed event
- failed execution status

---

# Security

The endpoint must validate:

- User permissions
- Job ownership
- Processing access

Execution identifiers must not expose internal database identifiers.

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/queue/processing/taskiq-processing.md
- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/api/sse/processing-events.md
- docs/ai/langgraph-state.md
