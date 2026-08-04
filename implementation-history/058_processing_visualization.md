# Prompt 057 - Implement Processing Execution Visualization From Backend To Frontend

## Objective

Implement the complete Processing Execution visualization system.

The goal is to expose the existing LangGraph Job Context Preparation Workflow execution state to the frontend in real time.

The workflow itself already exists.

DO NOT create a new workflow.

DO NOT modify the existing JobContextPreparationGraph stages unless required for emitting progress information.

The implementation must add:

- ProcessingExecution progress tracking.
- WorkflowStep state mapping.
- SSE event streaming.
- Processing Queue integration.
- Frontend live workflow visualization.

---

# Existing Workflow Context

The existing workflow was implemented in:

Prompt 056 - Implement Job Context Preparation Workflow Using LangGraph

Current workflow:

```
Job

↓

Load Job

↓

Collect Sources

↓

Fetch Content

↓

Extract Content

↓

Build Context

↓

Validate Context

↓

Ready For Analysis
```

This prompt only adds observability and visualization.

---

# Read Documentation First

Before making changes read:

- docs/domain/processing/processing-execution.md
- docs/domain/processing/workflow-progress.md
- docs/domain/processing/workflow-step.md
- docs/domain/processing/events.md
- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md
- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/process-job-live.md
- docs/architecture/runtime/workflow-progress.md
- docs/architecture/sse-architecture.md

---

# Architecture Rules

Follow:

- Modular Monolith architecture.
- DDD boundaries.
- Existing Processing bounded context.

Do not create shared generic progress systems.

Workflow execution progress belongs to:

```
Processing Context
```

---

# Backend Implementation

## 1. Workflow Progress Model

Implement WorkflowProgress tracking.

Location:

```
domain/processing
```

The model represents user-facing workflow progress.

It contains:

```
WorkflowProgress

    steps[]

    current_step

    overall_progress
```

Each step:

```
WorkflowStep

    id

    node_id

    title

    status

    progress

    children

    error
```

Important:

`node_id` is internal.

Frontend only uses:

- id
- title
- status
- progress
- children

---

# LangGraph Integration

Do not expose LangGraph state directly.

Create a mapping layer:

```
LangGraph State

        |

        v

WorkflowProgress Mapper

        |

        v

WorkflowStep
```

Example:

Internal node:

```
FetchSourcesNode
```

Public step:

```
Fetching Sources
```

---

# Progress Updates

Each LangGraph node execution must update ProcessingExecution progress.

Example:

Before:

```
Fetch Content

pending
```

When started:

```
Fetch Content

processing
```

During execution:

```
Fetch Content

processing
60%
```

After:

```
Fetch Content

completed
```

---

# TaskIQ Integration

TaskIQ remains responsible only for background execution.

Update existing task:

```
process_job_context_task(execution_id)
```

The task should:

1. Load ProcessingExecution.
2. Start workflow.
3. Emit execution.started.
4. Execute LangGraph graph.
5. Update workflow progress after each node.
6. Emit workflow events.
7. Complete or fail execution.

TaskIQ must not contain workflow business logic.

---

# Event System

Implement processing events.

Events:

```
execution.created

execution.started

workflow.step.started

workflow.step.progress

workflow.step.completed

workflow.step.failed

execution.completed

execution.failed

execution.cancelled

queue.entry.removed
```

Events must be user-facing.

Do not expose:

- TaskIQ task names.
- Worker identifiers.
- LangGraph node implementation details.

---

# SSE API

Implement:

```
GET /api/sse/processing-events
```

Requirements:

- Authentication aware.
- Stream only accessible executions.
- Support multiple connected clients.
- Keep connection alive.

The frontend lifecycle:

```
REST Snapshot

        +

SSE Events

        |

        v

Live UI State
```

---

# Processing Snapshot APIs

Implement:

## Get Processing Queue

Example:

```
GET /api/processing/queue
```

Returns:

- queued executions
- processing executions
- failed executions

---

## Get Execution Detail

Example:

```
GET /api/processing/executions/{execution_id}
```

Returns:

- execution status
- current step
- workflow progress tree
- nested steps
- errors

---

# Frontend Implementation

## Processing Queue Drawer

Implement the Processing Queue UI.

Location:

existing Jobs feature.

The drawer must display:

```
Processing

Queued

Failed
```

---

# Processing Item

Each item displays:

```
Job Title

Current Step

Progress

Status
```

Example:

```
Senior Backend Engineer

Fetching Sources

██████████──── 60%
```

---

# Workflow Detail View

When user opens an execution:

Show workflow tree.

Example:

```
✓ Load Job

✓ Collect Sources

⟳ Fetch Content
    ✓ Primary URL
    ⟳ Company Website

○ Build Context

○ Validate Context
```

Requirements:

- Expand/collapse nested steps.
- Highlight current step.
- Show progress.
- Show failure messages.

---

# SSE Frontend Integration

Frontend flow:

```
Open Drawer

↓

Fetch Queue Snapshot

↓

Fetch Execution Snapshot

↓

Subscribe SSE

↓

Apply Events

↓

Update UI
```

If event ordering gap happens:

- Refetch snapshot.
- Replace local state.

---

# Frontend State Management

Use existing frontend architecture.

Do not create a second source of truth.

Processing state should contain:

```
Execution

    status

    workflow

    current_step

    progress
```

---

# UI Rules

Do NOT show:

- LangGraph node names.
- TaskIQ details.
- Worker information.

Show only:

- User meaningful steps.
- Progress.
- Errors.
- Current activity.

---

# Testing Requirements

## Backend Tests

Test:

- WorkflowStep mapping.
- Progress updates.
- Event generation.
- SSE payload format.
- Snapshot APIs.

---

## Frontend Tests

Test:

- Drawer rendering.
- Queue sections.
- SSE updates.
- Step expansion.
- Progress updates.
- Failure display.

---

# Migration Rule

Before implementation:

Check if an older processing visualization exists.

If it exists:

- Remove obsolete implementation.
- Remove obsolete tests.
- Replace with this architecture.

Do not keep multiple execution visualization systems.

---

# Expected Final Architecture

```
Frontend

↓

Processing Queue Drawer

↓

REST Snapshot API

+

SSE Stream

↓

Processing Context

↓

ProcessingExecution

↓

TaskIQ Background Task

↓

LangGraph Workflow

↓

WorkflowProgress Mapper

↓

WorkflowStep Events

↓

Live UI
```

---

# Important Constraints

Do not add:

- LLM calls.
- Analysis workflow.
- Scoring workflow.
- Recommendation workflow.

This implementation only prepares:

```
Job Processing Context

+

Real-time Execution Visualization
```

Future prompts will add:

- LLM analysis.
- Evaluation.
- Recommendations.
