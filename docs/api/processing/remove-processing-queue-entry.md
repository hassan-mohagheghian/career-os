# Remove Processing Queue Entry API

## Purpose

The Remove Processing Queue Entry API removes an execution from the Processing Queue view.

This action only affects the temporary processing queue representation.

It does not delete:

- The Job.
- The ProcessingExecution history.
- Workflow data.
- Audit information.

The Job remains available in the Jobs list.

---

# Endpoint

## Remove Processing Queue Entry

DELETE

    /api/processing/queue/{execution_id}

---

# Path Parameters

| Parameter    | Description                    |
| ------------ | ------------------------------ |
| execution_id | ProcessingExecution identifier |

---

# Usage

Used by:

- Processing Queue Drawer.
- Failed execution management.
- Queued execution management.

Main flow:

    User clicks Remove

        |

        v

    Frontend sends remove request

        |

        v

    Backend removes queue visibility entry

        |

        v

    SSE updates connected clients

---

# Request Body

No request body is required.

Example:

    DELETE /api/processing/queue/execution-123

---

# Response

Example:

    {
      "execution_id": "execution-123",
      "removed": true
    }

---

# Removal Rules

The behavior depends on execution status.

Allowed:

    queued

    failed

Not allowed:

    processing

    completed

    cancelled

---

# Queued Execution Removal

When a queued execution is removed:

Before:

    Processing Queue

    Queued

    Python Developer

After:

    Processing Queue

    Empty

Execution result:

- Queue entry removed.
- ProcessingExecution cancelled.
- Job remains available.

State transition:

    queued

        |

        v

    cancelled

---

# Failed Execution Removal

When a failed execution is removed:

Before:

    Processing Queue

    Failed

    Frontend Engineer

After:

    Processing Queue

    Empty

Execution result:

- Queue entry removed.
- Failed execution history remains.
- Job remains available.

The failed ProcessingExecution status does not change.

---

# Processing Execution Behavior

Running executions cannot be removed.

Reason:

A running worker must be controlled through:

    POST /api/processing/executions/{execution_id}/cancel

Removing a running execution would create an inconsistent runtime state.

---

# Workflow Behavior

Removing a queue entry does not delete workflow information.

Workflow data remains accessible through:

    GET /api/processing/executions/{execution_id}

---

# SSE Events

After successful removal:

For queued executions:

    execution.cancelled

Example:

    {
      "type": "execution.cancelled",
      "execution_id": "execution-123"
    }

For failed executions:

    queue.entry.removed

Example:

    {
      "type": "queue.entry.removed",
      "execution_id": "execution-456"
    }

---

# Frontend Behavior

After successful response:

Frontend should:

1. Remove item from Queue section.
2. Keep Job in Jobs list.
3. Update local state after SSE confirmation.

Example:

Before:

Senior Backend Engineer

Failed to fetch source

After:

No failed executions

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
      "message": "Processing execution cannot be removed"
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
- Permission to remove queue entries.
- Execution visibility.

Inaccessible executions should return:

    404 Not Found

---

# Related Documents

- docs/api/processing/get-processing-queue.md
- docs/api/processing/get-processing-execution.md
- docs/api/processing/cancel-processing.md
- docs/api/sse/processing-events.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/job-state-machine.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/process-job-live.md
