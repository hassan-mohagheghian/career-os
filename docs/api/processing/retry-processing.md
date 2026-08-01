# Retry Processing API

## Purpose

The Retry Processing API creates a new processing attempt for a failed Job execution.

Retry does not restart the previous execution.

A new ProcessingExecution is created and added to the Processing Queue.

The original failed execution remains available for history and auditing.

---

# Endpoint

## Retry Failed Processing Execution

POST

    /api/processing/executions/{execution_id}/retry

---

# Path Parameters

| Parameter    | Description                           |
| ------------ | ------------------------------------- |
| execution_id | Failed ProcessingExecution identifier |

---

# Usage

Used by:

- Processing Queue Drawer.
- Failed execution view.
- Job processing history.

Main flow:

    User clicks Retry

        |

        v

    Frontend sends retry request

        |

        v

    Backend validates failed execution

        |

        v

    Create new ProcessingExecution

        |

        v

    Add new execution to Queue

        |

        v

    Worker starts processing

        |

        v

    SSE sends execution updates

---

# Request Body

No request body is required.

Example:

    POST /api/processing/executions/execution-123/retry

---

# Response

Example:

    {
      "execution_id": "execution-456",
      "job_id": "job-123",
      "status": "queued",
      "created_at": "2026-01-01T11:00:00Z",
      "retry_of": "execution-123"
    }

---

# Retry Rules

Retry is allowed only when execution status is:

    failed

Retry is not allowed when execution status is:

    queued

    processing

    completed

    cancelled

---

# Execution Relationship

A retry creates a new ProcessingExecution.

Example:

Previous execution:

    execution-123

    status: failed

New execution:

    execution-456

    status: queued

    retry_of: execution-123

---

# State Transition

Original execution:

    failed

        |

        v

    remains failed

New execution:

    queued

        |

        v

    processing

---

# Queue Behavior

After retry:

1. Create new ProcessingExecution.
2. Add it to Processing Queue.
3. New execution waits for available worker.
4. Previous failed execution remains unchanged.

Example:

Before:

    Failed

    Senior Backend Engineer

    execution-123

After:

    Failed

    Senior Backend Engineer

    execution-123


    Queued

    Senior Backend Engineer

    execution-456

---

# Workflow Behavior

A retry starts a new workflow execution.

The new workflow:

- Creates a new LangGraph execution.
- Creates a new checkpoint lifecycle.
- Creates a new workflow progress tree.
- Does not reuse previous runtime state.

Previous execution data remains available for inspection.

---

# SSE Events

After successful retry:

Backend emits:

    execution.created

Example:

    {
      "type": "execution.created",
      "execution_id": "execution-456",
      "retry_of": "execution-123",
      "timestamp": "2026-01-01T11:00:00Z"
    }

Then normal execution events continue:

- execution.started
- workflow.step.started
- workflow.step.progress
- workflow.step.completed
- execution.completed
- execution.failed

---

# Frontend Behavior

After receiving success response:

Frontend should:

1. Remove old failed item only if user action requires it.
2. Add new queued item.
3. Subscribe to SSE updates.
4. Show new execution progress.

Example UI:

Before:

    Failed

    Senior Backend Engineer

    Failed to fetch source

After:

    Failed

    Senior Backend Engineer

    Failed to fetch source


    Queued

    Senior Backend Engineer

    Waiting for worker

---

# Error Responses

## Execution Not Found

HTTP 404

Example:

    {
      "code": "EXECUTION_NOT_FOUND",
      "message": "Processing execution not found"
    }

---

## Invalid State

HTTP 409

Example:

    {
      "code": "INVALID_EXECUTION_STATE",
      "message": "Only failed executions can be retried"
    }

---

## Unauthorized

HTTP 401

---

## Forbidden

HTTP 403

---

# Security

The endpoint must verify:

- User access to Job.
- Permission to retry processing.
- Execution visibility.

Inaccessible executions should return:

    404 Not Found

---

# Related Documents

- docs/api/processing/get-processing-execution.md
- docs/api/processing/get-processing-queue.md
- docs/api/processing/cancel-processing.md
- docs/api/sse/processing-events.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/job-state-machine.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/process-job-live.md
