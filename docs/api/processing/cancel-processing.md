# Cancel Processing API

## Purpose

The Cancel Processing API allows users to stop a currently running Job ProcessingExecution.

Cancellation affects the active execution only.

The original Job is not deleted.

After cancellation:

- ProcessingExecution status becomes `cancelled`.
- Running workflow steps stop.
- Processing Queue entry is removed.
- Job remains available in the Jobs list.

---

# Endpoint

## Cancel Processing Execution

POST

    /api/processing/executions/{execution_id}/cancel

---

# Path Parameters

| Parameter    | Description                    |
| ------------ | ------------------------------ |
| execution_id | ProcessingExecution identifier |

---

# Usage

Used by:

- Processing Queue Drawer.
- Job live processing view.
- Job execution details.

Main flow:

    User clicks Cancel

        |

        v

    Frontend sends cancel request

        |

        v

    Backend requests execution cancellation

        |

        v

    Worker stops execution

        |

        v

    SSE sends cancellation event

---

# Request Body

No request body is required.

Example:

    POST /api/processing/executions/execution-123/cancel

---

# Response

Example:

    {
      "execution_id": "execution-123",
      "status": "cancelled",
      "cancelled_at": "2026-01-01T10:10:00Z"
    }

---

# Cancellation Rules

Cancellation is allowed only when execution status is:

    queued

    processing

Cancellation is not allowed when execution status is:

    completed

    failed

    cancelled

---

# Processing Status Transition

Before:

    processing

Action:

    cancel

After:

    cancelled

State transition:

    processing

        |

        v

    cancelled

---

# Workflow Behavior

When cancellation happens:

- Current workflow execution receives cancellation signal.
- Running LangGraph execution is stopped.
- Pending workflow steps are not executed.
- Checkpoints remain available for auditing.

---

# Queue Behavior

If execution is:

## Processing

The execution is removed from active Processing Queue.

Example:

Before:

    Processing Queue

    Processing

    Senior Backend Engineer

After:

    Processing Queue

    Empty

---

## Queued

The queue entry is removed immediately.

The Job remains in Jobs list.

---

# SSE Events

After successful cancellation:

Backend emits:

    execution.cancelled

Example event:

    {
      "type": "execution.cancelled",
      "execution_id": "execution-123",
      "timestamp": "2026-01-01T10:10:00Z"
    }

---

# Frontend Behavior

After receiving success response:

Frontend should:

1. Update execution status.
2. Show cancelled state.
3. Remove execution from Processing section.
4. Wait for SSE confirmation.

Example UI:

    Senior Backend Engineer

    Status:

    Cancelled

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
      "message": "Execution cannot be cancelled"
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

- User access to the Job.
- User permission to cancel execution.
- Execution ownership or visibility.

Inaccessible executions should return:

    404 Not Found

---

# Related Documents

- docs/api/processing/get-processing-execution.md
- docs/api/processing/get-processing-queue.md
- docs/api/sse/processing-events.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/job-state-machine.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/process-job-live.md
