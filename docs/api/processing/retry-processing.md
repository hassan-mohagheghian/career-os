# Retry Processing API

## Purpose

The Retry Processing API creates a new processing attempt for a failed Job execution.

Retry does not restart the previous execution.

A new ProcessingExecution is created and added to the Processing Queue.

The previous failed execution is **cancelled** so it leaves the Failed section —
the platform keeps a single active execution per target (queued / processing /
failed). The cancelled row remains in the database for history and auditing.

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

    Cancel previous failed execution (removed from Failed section)

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

Retry keeps a single active execution per target. If the target already has a
queued / processing / failed execution other than the one being retried, the
request is rejected with HTTP 409.

---

# Execution Relationship

A retry creates a new ProcessingExecution and cancels the previous one.

Example:

Previous execution:

    execution-123

    status: failed → cancelled (on retry)

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

    cancelled (removed from the Failed section, kept in DB for history)

New execution:

    queued

        |

        v

    processing

---

# Queue Behavior

After retry:

1. Cancel the previous failed execution (it leaves the Failed section).
2. Create a new ProcessingExecution.
3. Add it to Processing Queue.
4. New execution waits for available worker.

Only one active execution is kept per target.

Example:

Before:

    Failed

    Senior Backend Engineer

    execution-123

After:

    Queued

    Senior Backend Engineer

    execution-456

The cancelled previous execution (`execution-123`) no longer appears in the
Failed section.

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

    queue.entry.removed

for the cancelled previous execution, and:

    execution.created

for the new one.

Example:

    {
      "type": "queue.entry.removed",
      "execution_id": "execution-123",
      "status": "cancelled",
      "timestamp": "2026-01-01T11:00:00Z"
    }

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

1. Remove the old failed item (the backend has cancelled it).
2. Add new queued item.
3. Subscribe to SSE updates.
4. Show new execution progress.

Example UI:

Before:

    Failed

    Senior Backend Engineer

    Failed to fetch source

After:

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
