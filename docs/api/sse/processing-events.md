# Processing Events SSE API

## Purpose

The Processing Events SSE API provides real-time updates for Job ProcessingExecution lifecycle and workflow progress.

The frontend uses this stream to update:

- Processing Queue.
- Workflow Progress UI.
- Execution status.
- Workflow step progress.
- Failure states.
- Queue changes.

This API does not expose internal execution implementation.

The frontend must not depend on:

- TaskIQ task names.
- Worker names.
- LangGraph node names.
- Internal runtime details.

The API exposes user-facing processing events.

---

# Architecture

The event flow:

```text
ProcessingExecution

        |

        v

Background Worker (TaskIQ)

        |

        v

Workflow Engine (LangGraph)

        |

        v

Processing Event Mapper

        |

        v

SSE Stream

        |

        v

Frontend State
```

The Processing Event Mapper converts internal execution changes into stable user-facing events.

---

# Endpoint

## Subscribe Processing Events

GET

    /api/sse/processing-events

Response:

Content-Type:

    text/event-stream

The connection remains open until:

- Client disconnects.
- Authentication expires.
- Server shutdown occurs.

---

# Authentication

The SSE connection requires authenticated user context.

Only events belonging to accessible Jobs should be streamed.

Unauthorized executions must not be exposed.

---

# Event Model

All events share a common structure.

Example:

```json
{
  "id": "event-id",
  "type": "event.type",
  "timestamp": "2026-01-01T10:00:00Z",
  "job_id": "job-id",
  "execution_id": "execution-id",
  "payload": {}
}
```

Fields:

| Field        | Description                            |
| ------------ | -------------------------------------- |
| id           | Unique event identifier                |
| type         | Event type                             |
| timestamp    | Event creation time                    |
| job_id       | Related Job identifier                 |
| execution_id | Related ProcessingExecution identifier |
| payload      | Event specific data                    |

---

# Execution Events

## execution.created

Triggered when a new ProcessingExecution is created.

Purpose:

- Add item to Processing Queue.
- Show queued state.

Payload:

```json
{
  "status": "queued"
}
```

---

## execution.started

Triggered when execution starts processing.

Purpose:

- Move execution from queued state to processing state.

Payload:

```json
{
  "status": "processing"
}
```

---

## execution.completed

Triggered when execution finishes successfully.

Purpose:

- Remove item from Processing Queue.
- Update Job state.

Payload:

```json
{
  "status": "completed"
}
```

---

## execution.failed

Triggered when execution fails.

Purpose:

- Show failed state.
- Display failure reason.

Payload:

```json
{
  "status": "failed",
  "error": {
    "code": "FETCH_FAILED",
    "message": "Unable to fetch source"
  }
}
```

---

## execution.cancelled

Triggered when execution is cancelled.

Payload:

```json
{
  "status": "cancelled"
}
```

---

# Queue Events

## queue.entry.removed

Triggered when a queue entry is removed.

Purpose:

- Remove item from Processing Queue UI.
- Keep Job history unchanged.

Payload:

```json
{
  "execution_id": "execution-123"
}
```

---

# Workflow Step Events

Workflow steps represent user-facing processing stages.

They are independent from internal LangGraph nodes.

Example:

Internal:

```text
fetch_sources_node
```

Public:

```text
Fetching Sources
```

---

# workflow.step.started

Triggered when a visible workflow step starts.

Payload:

```json
{
  "step": {
    "id": "fetch_content",
    "title": "Fetch Content",
    "status": "processing",
    "displayable": true
  }
}
```

---

# workflow.step.progress

Triggered when step progress changes.

Payload:

```json
{
  "step": {
    "id": "fetch_content",
    "title": "Fetch Content",
    "status": "processing",
    "progress": 60,
    "displayable": true
  }
}
```

---

# workflow.step.completed

Triggered when a workflow step finishes.

Payload:

```json
{
  "step": {
    "id": "fetch_content",
    "title": "Fetch Content",
    "status": "completed",
    "displayable": true
  }
}
```

---

# workflow.step.failed

Triggered when a workflow step fails.

Payload:

```json
{
  "step": {
    "id": "fetch_content",
    "title": "Fetch Content",
    "status": "failed",
    "displayable": true,
    "error": {
      "code": "SOURCE_FETCH_FAILED",
      "message": "Primary source unavailable"
    }
  }
}
```

---

# Nested Step Updates

A workflow step may contain child steps.

Example:

```text
Fetch Content

    Primary URL

    Company Website

    Additional Links
```

Payload:

```json
{
  "step": {
    "id": "fetch_content",
    "children": [
      {
        "id": "primary_url",
        "title": "Primary URL",
        "status": "completed"
      },
      {
        "id": "company_url",
        "title": "Company Website",
        "status": "processing",
        "progress": 40
      }
    ]
  }
}
```

---

# Frontend Synchronization Rules

The frontend maintains a local execution state.

Initial state:

```text
REST API snapshot
```

Continuous updates:

```text
SSE events
```

Flow:

```text
Open Processing Queue

        |

        v

GET /api/processing/queue

        |

        v

GET /api/processing/executions/{id}

        |

        v

Subscribe SSE

        |

        v

Apply events

        |

        v

Update UI
```

---

# Event Ordering

Events contain:

- timestamp
- unique identifier

Frontend should process events in order.

If an event gap is detected:

1. Fetch execution snapshot again.
2. Replace local state.
3. Continue consuming SSE events.

---

# Retry Behavior

Retry creates a new ProcessingExecution.

The frontend receives:

```text
execution.created
```

for the new execution.

The previous failed execution remains unchanged.

---

# Cancellation Behavior

When cancellation succeeds:

Frontend receives:

```text
execution.cancelled
```

The Processing Queue entry is removed.

---

# Empty State

When no active executions exist:

- SSE connection remains open.
- No event is emitted.

---

# Related Documents

- docs/api/processing/get-processing-queue.md
- docs/api/processing/get-processing-execution.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/domain/processing/workflow-progress.md
- docs/architecture/runtime/workflow-progress.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/features/jobs/workflow-progress.md
- docs/workflows/job-processing.md (realized trace-through + current two-path note)
