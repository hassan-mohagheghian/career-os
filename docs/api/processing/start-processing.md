# Start Processing API

## Purpose

The Start Processing API starts a queued Job ProcessingExecution immediately.

A queued execution is already waiting in the background queue. Start re-dispatches
it so a worker picks it up right away.

The original Job is not modified.

After starting:

- ProcessingExecution stays `queued` until a worker claims it.
- The execution moves to the Processing section once running.
- The Job remains available in the Jobs list.

---

# Endpoint

## Start Queued Processing Execution

POST

    /api/processing/executions/{execution_id}/start

---

# Path Parameters

| Parameter    | Description                    |
| ------------ | ------------------------------ |
| execution_id | ProcessingExecution identifier |

---

# Usage

Used by:

- Processing Queue Drawer (Waiting section).

Main flow:

    User clicks Start

        |

        v

    Frontend sends start request

        |

        v

    Backend re-dispatches queued execution

        |

        v

    Worker picks up execution

        |

        v

    Execution starts processing

---

# Request Body

No request body is required.

Example:

    POST /api/processing/executions/execution-123/start

---

# Response

Example:

    {
      "execution_id": "execution-123",
      "job_id": "job-123",
      "status": "queued",
      "started": true
    }

---

# Start Rules

Start is allowed only when execution status is:

    queued

    starting

Start is not allowed when execution status is:

    running

    completed

    failed

    cancelled

---

# Processing Status Transition

Before:

    queued

Action:

    start

After:

    queued

        |

        v

    running

State transition:

    queued

        |

        v

    running

Start does not change the status itself — the worker transitions the execution
to running when it claims the task.

---

# Queue Behavior

After start:

1. The execution remains in the Waiting section until claimed.
2. Once a worker claims it, it moves to the Processing section.
3. The Job is never removed from the Jobs list.

---

# SSE Events

After successful start:

Backend emits:

    execution.started

Example event:

    {
      "type": "execution.started",
      "execution_id": "execution-123",
      "timestamp": "2026-01-01T10:00:00Z"
    }

Then normal workflow events continue:

- workflow.step.started
- workflow.step.progress
- workflow.step.completed
- execution.completed
- execution.failed

---

# Frontend Behavior

After receiving success response:

Frontend should:

1. Refresh the Processing Queue snapshot.
2. Keep the item in the Waiting section until it starts.
3. Show the item in the Processing section once running.

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
      "message": "Execution cannot be started"
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
- Permission to start execution.
- Execution ownership or visibility.

Inaccessible executions should return:

    404 Not Found

---

# Related Documents

- docs/api/processing/get-processing-execution.md
- docs/api/processing/get-processing-queue.md
- docs/api/processing/cancel-processing.md
- docs/api/processing/retry-processing.md
- docs/api/processing/remove-processing-queue-entry.md
- docs/api/sse/processing-events.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/job-state-machine.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/processing-queue.md
