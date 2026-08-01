# Workflow Step

## Purpose

WorkflowStep represents a user-visible stage inside a ProcessingExecution workflow.

A WorkflowStep is the bridge between:

- Internal workflow execution nodes.
- User-facing processing progress.
- Frontend workflow visualization.

WorkflowSteps are owned by the Processing domain.

They are not owned by:

- LangGraph.
- TaskIQ.
- Frontend.

LangGraph executes workflow nodes, but the Processing domain defines which execution states become visible WorkflowSteps.

---

# Concept

A ProcessingExecution contains a workflow.

A workflow contains multiple WorkflowSteps.

Example:

```text
ProcessingExecution

    Job Context Preparation

        |
        +-- Load Job
        |
        +-- Collect Sources
        |
        +-- Fetch Content
        |
        +-- Build Context
```

---

# Responsibilities

WorkflowStep is responsible for:

- Representing processing progress.
- Exposing execution state to frontend.
- Tracking nested processing stages.
- Providing user-readable workflow status.

WorkflowStep is not responsible for:

- Running tasks.
- Calling workers.
- Managing queues.
- Executing LangGraph nodes.

---

# Relationship

```text
Job

 |
 v

ProcessingExecution

 |
 v

Workflow

 |
 v

WorkflowStep

 |
 +-- Child WorkflowStep
```

---

# WorkflowStep Object

Example:

```json
{
  "id": "fetch_content",
  "node_id": "langgraph_fetch_content",
  "title": "Fetch Content",
  "status": "processing",
  "progress": 60,
  "displayable": true,
  "children": []
}
```

---

# Fields

| Field        | Description                              |
| ------------ | ---------------------------------------- |
| id           | Stable workflow step identifier          |
| node_id      | Internal execution node identifier       |
| title        | User-facing step title                   |
| status       | Current step status                      |
| progress     | Completion percentage                    |
| displayable  | Whether frontend should render this step |
| children     | Nested workflow steps                    |
| error        | Failure information                      |
| started_at   | Step start timestamp                     |
| completed_at | Step completion timestamp                |

---

# Step Identifier

The `id` field is a stable domain identifier.

Examples:

```text
load_job

collect_sources

fetch_content

build_context

analyze_content
```

Rules:

- Must not change between executions.
- Must not depend on database identifiers.
- Must be safe for frontend usage.

---

# Node Identifier

The `node_id` represents the internal workflow engine node.

Example:

```text
langgraph_fetch_content_node
```

Rules:

- Used internally.
- May change with implementation.
- Must not be used as frontend identity.

---

# Status

Possible values:

```text
pending

processing

completed

failed

skipped
```

---

# Status Meaning

## Pending

Step has not started.

Example:

```text
Build Context

Pending
```

---

## Processing

Step is currently running.

Example:

```text
Fetch Content

Processing 60%
```

---

## Completed

Step finished successfully.

Example:

```text
Collect Sources

Completed
```

---

## Failed

Step execution failed.

Example:

```text
Fetch Content

Failed
```

---

## Skipped

Step was intentionally not executed.

Example:

```text
Optional Metadata Fetch

Skipped
```

---

# Progress

Progress represents estimated completion.

Range:

```text
0 - 100
```

Example:

```json
{
  "progress": 75
}
```

Rules:

- Optional.
- Only meaningful for processing steps.
- Frontend should not calculate progress.
- Backend owns progress calculation.

---

# Nested Steps

WorkflowSteps may contain child steps.

Example:

```json
{
  "id": "fetch_content",
  "title": "Fetch Content",
  "status": "processing",
  "children": [
    {
      "id": "primary_url",
      "title": "Primary URL",
      "status": "completed"
    },
    {
      "id": "additional_sources",
      "title": "Additional Sources",
      "status": "processing",
      "progress": 40
    }
  ]
}
```

Nested steps allow:

- High-level workflow display.
- Expand/collapse details.
- Technical progress inspection.

---

# Display Rules

Not every internal execution node should be visible.

A WorkflowStep contains:

```text
displayable
```

Example:

Visible:

```text
Fetch Content
```

Hidden:

```text
Restore LangGraph checkpoint
```

Hidden steps:

- Internal recovery.
- Technical validation.
- Retry handling.
- Persistence operations.

Frontend renders only:

```text
displayable = true
```

---

# Error Object

When a step fails:

Example:

```json
{
  "error": {
    "code": "FETCH_FAILED",
    "message": "Unable to fetch source content"
  }
}
```

Fields:

| Field   | Description               |
| ------- | ------------------------- |
| code    | Stable error identifier   |
| message | User-facing error message |

---

# Workflow Engine Relationship

Current workflow engine:

```text
LangGraph
```

Relationship:

```text
LangGraph Node

        |

        v

WorkflowStep
```

The domain does not expose LangGraph implementation details.

The mapping layer converts:

```text
LangGraph State

        |

        v

WorkflowProgress

        |

        v

WorkflowStep
```

---

# Persistence

WorkflowStep state may be stored as part of:

```text
ProcessingExecution
```

or managed through:

```text
WorkflowProgress snapshot
```

The source of truth is:

```text
ProcessingExecution workflow state
```

---

# SSE Integration

WorkflowStep changes produce SSE events.

Examples:

```text
workflow.step.started

workflow.step.progress

workflow.step.completed

workflow.step.failed
```

Frontend updates WorkflowProgress using these events.

---

# Frontend Usage

Frontend uses WorkflowStep for:

- Timeline rendering.
- Progress bars.
- Expandable workflow tree.
- Current step highlighting.

Example:

```text
✓ Load Job

✓ Collect Sources

⟳ Fetch Content
  ├─ ✓ Primary URL
  └─ ⟳ Company Website

○ Build Context
```

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/domain/processing/workflow-progress.md
- docs/domain/processing/events.md
- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md
- docs/ux/features/jobs/workflow-progress.md
