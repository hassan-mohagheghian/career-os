# Workflow Progress

## Purpose

Workflow Progress defines the user-facing representation of a Job Processing workflow execution.

It provides a stable model between:

- Backend execution runtime.
- LangGraph workflow engine.
- ProcessingExecution.
- Frontend workflow visualization.

The Workflow Progress model allows the system to expose:

- Current processing stage.
- Completed stages.
- Running stages.
- Failed stages.
- Nested step progress.
- Execution details.

The frontend must depend on this model instead of internal workflow implementation.

---

# Architecture

The relationship:

    Job

        |

        v

    ProcessingExecution

        |

        v

    WorkflowProgress

        |

        v

    WorkflowSteps

The WorkflowProgress model is owned by the processing domain.

It is not owned by:

- LangGraph.
- TaskIQ.
- Worker implementation.

LangGraph is the execution engine.

WorkflowProgress is the presentation and domain progress model.

---

# Goals

Workflow Progress should provide:

- Stable UI representation.
- Human-readable execution steps.
- Progress tracking.
- Nested workflow visibility.
- SSE event compatibility.
- Historical execution inspection.

---

# Non Goals

WorkflowProgress does not represent:

- Internal LangGraph graph structure.
- Every internal node.
- Worker lifecycle.
- Queue implementation details.

Example:

Internal LangGraph:

    FetchSourcesNode

Public Workflow Step:

    Fetching Sources

---

# WorkflowProgress Model

A WorkflowProgress contains:

- Workflow identifier.
- Current active step.
- Ordered steps.
- Overall progress.
- Workflow status.

Example:

    WorkflowProgress

        id

        status

        progress

        current_step

        steps

---

# Workflow Status

Possible values:

    pending

    running

    completed

    failed

    cancelled

---

# Workflow Step Model

A WorkflowStep represents one user-facing stage.

Fields:

| Field    | Description         |
| -------- | ------------------- |
| id       | Stable identifier   |
| title    | User-facing name    |
| status   | Current state       |
| progress | Optional percentage |
| children | Nested steps        |
| metadata | Optional details    |
| error    | Failure information |

Example:

    {
      "id": "fetch_content",
      "title": "Fetch Content",
      "status": "running",
      "progress": 60
    }

---

# Step Status

Possible values:

    pending

    running

    completed

    failed

    skipped

---

# Nested Steps

A workflow step can contain child steps.

This allows detailed visualization without exposing internal implementation.

Example:

    Fetch Content

        Primary Job URL

        Company Website

        Additional Links

Model:

    WorkflowStep

        id: fetch_content

        children:

            primary_url

            company_url

            additional_links

---

# Example Workflow

Job Processing workflow — a single combined workflow
(`WORKFLOW_ID="job_processing"`, `WORKFLOW_NAME="Job Processing"`) covering
both phases:

    Load Job

    Collect Sources

    Fetch Content

    Extract Content

    Build Context

    Validate Context

    Save Context

    Analyze Job

    Extract Skills

    Score Job

    Recommendation

    Summarize

    Save Results

Internal nodes that are never exposed as steps: `execution_failed`,
`context_ready`, `analysis_ready`, `load_context`, `prepare_profile`.

Future steps can be added

    Generation

without changing frontend architecture.

---

# Progress Calculation

Progress can exist at multiple levels.

## Step Progress

Example:

    Fetch Content

    Progress: 60%

## Workflow Progress

Example:

    Context Preparation

    Progress: 45%

The backend owns progress calculation.

The frontend only renders values.

---

# Current Step

The current_step field represents the active user-facing step.

Example:

    current_step:

        id:
        fetch_content

        title:
        Fetch Content

        status:
        running

        progress:
        60

The frontend highlights this step.

---

# Step Metadata

Optional metadata can provide additional information.

Examples:

    {
      "source_count": 5,
      "completed_sources": 3
    }

Metadata should not contain UI-specific information.

---

# Error Model

Failed steps may include error information.

Example:

    {
      "status": "failed",

      "error": {
        "code": "FETCH_TIMEOUT",
        "message": "Source did not respond"
      }
    }

Errors are displayed by the frontend.

---

# LangGraph Integration

LangGraph manages execution.

WorkflowProgress represents execution visibility.

The mapping:

    LangGraph Node

            |

            v

    Workflow Step Adapter

            |

            v

    WorkflowProgress

The adapter prevents frontend coupling to LangGraph internals.

---

# TaskIQ Integration

TaskIQ executes background work.

TaskIQ does not own workflow progress.

The flow:

    TaskIQ Worker

        |

        v

    Start ProcessingExecution

        |

        v

    Execute LangGraph Workflow

        |

        v

    Update WorkflowProgress

        |

        v

    Emit SSE Event

---

# Persistence

WorkflowProgress may be stored as part of ProcessingExecution state.

Possible storage:

- Database JSON column.
- Dedicated workflow progress table.
- LangGraph checkpoint state.

The final decision belongs to persistence architecture.

---

# SSE Integration

WorkflowProgress changes generate events.

Examples:

    workflow.step.started

    workflow.step.progress

    workflow.step.completed

    workflow.step.failed

The SSE layer serializes WorkflowProgress changes.

---

# Frontend Usage

Frontend components consume:

    WorkflowProgress

not:

    LangGraphState

Example components:

- WorkflowTimeline.
- WorkflowStep.
- StepDetails.
- ProgressIndicator.

---

# Example Frontend View

Collapsed:

    Context Preparation

    Fetch Content

    Progress 60%

Expanded:

    Context Preparation


    ✓ Load Job

    ✓ Collect Sources

    ⟳ Fetch Content

        ✓ Primary URL

        ⟳ Company Website

        ○ Additional Links


    ○ Extract Content

---

# Versioning

WorkflowProgress is a public contract.

Changes must consider:

- Existing frontend versions.
- Stored executions.
- Historical data.

Breaking changes require:

- Migration.
- ADR.
- Version update.

---

# Related Documents

- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md
- docs/domain/processing/job-state-machine.md
- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md
- docs/architecture/runtime/workflow-progress.md
- docs/ux/features/jobs/processing-queue.md
