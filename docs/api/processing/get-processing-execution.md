# Get Processing Execution API

## Purpose

The Processing Execution API provides the current snapshot of a Job ProcessingExecution.

This endpoint is used by the frontend to initialize the detailed execution state before subscribing to SSE updates.

The endpoint provides:

- Current execution status.
- Current workflow progress.
- Current workflow step.
- Completed steps.
- Running steps.
- Failed steps.
- Nested workflow step details.
- Workflow metadata.

This endpoint returns a snapshot only.

Live updates are delivered through SSE.

---

# Endpoint

## Get Processing Execution

GET

    /api/processing/executions/{execution_id}

---

# Path Parameters

| Parameter    | Description                    |
| ------------ | ------------------------------ |
| execution_id | ProcessingExecution identifier |

---

# Response

Example:

    {
      "execution_id": "execution-123",
      "job_id": "job-456",
      "status": "processing",
      "created_at": "2026-01-01T10:00:00Z",
      "started_at": "2026-01-01T10:01:00Z",
      "completed_at": null,

      "current_step": {
        "id": "fetch_content",
        "title": "Fetching Content",
        "status": "running",
        "progress": 60
      },

      "workflow": {
        "id": "job_context_preparation",
        "name": "Job Context Preparation",
        "engine": "langgraph",
        "checkpoint_id": "checkpoint-123",
        "steps": []
      }
    }

---

# ProcessingExecution Object

## Fields

| Field        | Description                                 |
| ------------ | ------------------------------------------- |
| execution_id | ProcessingExecution identifier              |
| job_id       | Related Job identifier                      |
| status       | Current execution status                    |
| created_at   | Execution creation time                     |
| started_at   | Execution start time                        |
| completed_at | Execution completion time                   |
| current_step | Currently running user-facing workflow step |
| workflow     | Workflow progress snapshot                  |

---

# Execution Status

Possible values:

    queued

    processing

    completed

    failed

    cancelled

---

# Workflow Object

The workflow object represents the user-facing processing flow.

The frontend uses this object to render:

- Timeline.
- Progress indicators.
- Expandable workflow steps.
- Step details.

Example:

    {
      "workflow": {
        "id": "job_context_preparation",
        "name": "Job Context Preparation",
        "engine": "langgraph",
        "checkpoint_id": "checkpoint-123",

        "steps": [
          {
            "id": "load_job",
            "title": "Load Job",
            "status": "completed"
          },
          {
            "id": "collect_sources",
            "title": "Collect Sources",
            "status": "completed"
          },
          {
            "id": "fetch_content",
            "title": "Fetch Content",
            "status": "running",
            "progress": 60
          }
        ]
      }
    }

---

# Workflow Metadata

The workflow object contains execution metadata.

| Field         | Description                            |
| ------------- | -------------------------------------- |
| id            | Stable workflow identifier             |
| name          | User-facing workflow name              |
| engine        | Workflow execution engine              |
| checkpoint_id | Current workflow checkpoint identifier |
| steps         | Workflow progress tree                 |

Example:

    {
      "engine": "langgraph",
      "checkpoint_id": "checkpoint-123"
    }

---

# Workflow Step

Each workflow step represents a user-visible execution stage.

A step contains:

| Field       | Description                            |
| ----------- | -------------------------------------- |
| id          | Stable step identifier                 |
| node_id     | Internal workflow node identifier      |
| title       | User-facing title                      |
| status      | Step status                            |
| progress    | Optional percentage                    |
| children    | Optional nested steps                  |
| error       | Optional failure information           |
| displayable | Whether frontend should show this step |

Example:

    {
      "id": "fetch_content",
      "node_id": "fetch_content_node",
      "title": "Fetch Content",
      "status": "processing",
      "progress": 60,
      "displayable": true,

      "children": [
        {
          "id": "primary_url",
          "node_id": "fetch_primary_url",
          "title": "Primary URL",
          "status": "completed",
          "displayable": true
        },
        {
          "id": "company_url",
          "node_id": "fetch_company_url",
          "title": "Company Website",
          "status": "processing",
          "progress": 40,
          "displayable": true
        }
      ]
    }

---

# Step Visibility Rules

Not every internal workflow node should be visible in UI.

The backend decides visibility.

Internal nodes such as:

- Checkpoint restore.
- Retry handling.
- Internal validation.
- Technical recovery steps.

should have:

    displayable: false

Frontend must only render:

    displayable: true

---

# Step Status

Possible values:

    pending

    processing

    completed

    failed

    skipped

---

# Current Step

The current_step field represents the active user-facing workflow step.

Example:

    {
      "current_step": {
        "id": "build_context",
        "title": "Building Context",
        "status": "processing",
        "progress": 35
      }
    }

The frontend should highlight this step.

---

# Failure Information

When execution fails:

Example:

    {
      "status": "failed",

      "error": {
        "code": "SOURCE_FETCH_FAILED",
        "message": "Unable to fetch primary source"
      }
    }

---

# Empty Workflow

A ProcessingExecution may exist before workflow execution starts.

Example:

    {
      "status": "queued",

      "workflow": {
        "steps": []
      }
    }

Frontend displays:

    Waiting for execution

---

# Frontend Usage

The frontend lifecycle:

    Open Processing Queue

        |

        v

    GET /api/processing/executions/{execution_id}

        |

        v

    Render initial workflow state

        |

        v

    Subscribe SSE

        |

        v

    Apply workflow events

---

# Consistency With SSE

This endpoint returns a snapshot.

SSE returns changes after the snapshot.

Frontend flow:

1. Load execution snapshot.
2. Connect SSE stream.
3. Apply newer workflow events.
4. Update local state.

Relevant events:

- execution.started
- workflow.step.started
- workflow.step.progress
- workflow.step.completed
- workflow.step.failed
- execution.completed
- execution.failed
- execution.cancelled

If an event gap is detected:

- Request this endpoint again.
- Replace local execution state.

---

# Security

The endpoint must verify:

- User access to Job.
- User ownership or permission.
- Execution visibility.

Unauthorized executions must return:

    404 Not Found

Do not expose existence of inaccessible executions.

---

# Related Documents

- docs/api/sse/processing-events.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/domain/processing/workflow-progress.md
- docs/architecture/runtime/workflow-progress.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/features/jobs/workflow-progress.md
