# Processing Queue

## Purpose

The Processing Queue provides a real-time execution view for Jobs that are queued or currently being processed.

The Processing Queue does not own Jobs.

Jobs always remain in the Jobs list.

The Processing Queue represents temporary processing execution state created by a ProcessingExecution.

The execution relationship is:

Jobs

↓

ProcessingExecution

↓

Background Execution (TaskIQ)

↓

Workflow Execution (LangGraph)

↓

Workflow Steps

The Processing Queue allows users to:

- Monitor background processing.
- Track execution state.
- View workflow progress.
- Inspect processing steps.
- Retry failed executions.
- Cancel running executions.
- Remove queued or failed execution entries.

---

# Related Documents

Backend concepts:

- docs/domain/processing/processing-execution.md
- docs/domain/processing/job-state-machine.md
- docs/domain/processing/events.md

Runtime:

- docs/architecture/runtime/background-service.md
- docs/architecture/runtime/background-workflows.md
- docs/architecture/runtime/workflow-progress.md

API:

- docs/api/sse/processing-events.md

Design system:

- docs/ux/design-system/drawer.md

---

# Container

Current implementation:

- Drawer

Future implementations:

- Split View
- Side Panel
- Processing Dashboard

The behavior defined in this document is independent from the container type.

---

# Concept

The Processing Queue is not the Jobs list.

Jobs always exist in the Jobs list.

The Processing Queue only displays active execution information.

Example:

Jobs List

    Senior Backend Engineer     Imported

    Python Developer            Queued

    Staff Engineer              Processing

    Frontend Engineer           Failed

Processing Queue

    Processing

    - Staff Engineer


    Queued

    - Python Developer


    Failed

    - Frontend Engineer

When processing completes successfully:

- ProcessingExecution becomes completed.
- Queue entry is removed.
- Job remains in Jobs list.
- Job status changes to Processed.

The Job is never moved between lists.

---

# Execution Model

Each Processing Queue item represents one ProcessingExecution.

The UI should display execution state, not internal implementation details.

The relationship:

Job

↓

ProcessingExecution

↓

Workflow Progress

↓

Workflow Steps

↓

Step Details

The UI must not directly expose:

- LangGraph node names.
- TaskIQ task names.
- Worker implementation details.

The UI displays user-facing workflow steps.

---

# Queue Sections

The Processing Queue contains:

- Processing
- Queued
- Failed

Completed executions are not displayed.

# Drawer Overview

    ┌─────────────────────────────────────────────┐
    │ Processing Queue                      Close │
    ├─────────────────────────────────────────────┤
    │                                             │
    │ Processing (2)                              │
    │                                             │
    │ ┌─────────────────────────────────────────┐ │
    │ │ Senior Backend Engineer                 │ │
    │ │ Preparing Context                       │ │
    │ │ Fetching Sources                        │ │
    │ │ ███████████░░░░░ 60%                    │ │
    │ │                              Details    │ │
    │ └─────────────────────────────────────────┘ │
    │                                             │
    │ Queued (3)                                  │
    │                                             │
    │ ┌─────────────────────────────────────────┐ │
    │ │ Python Developer                        │ │
    │ │ Waiting for available worker            │ │
    │ │                         Start Remove    │ │
    │ └─────────────────────────────────────────┘ │
    │                                             │
    │ Failed (1)                                  │
    │                                             │
    │ ┌─────────────────────────────────────────┐ │
    │ │ Frontend Engineer                       │ │
    │ │ Failed to fetch source                  │ │
    │ │                         Retry Remove    │ │
    │ └─────────────────────────────────────────┘ │
    │                                             │
    └─────────────────────────────────────────────┘

---

# Processing

Processing displays Jobs with active ProcessingExecution.

Displayed information:

- Job title.
- Current workflow step.
- Progress.
- Execution duration (optional).

Example:

    Senior Backend Engineer

    Preparing Context

    Fetching Sources

    Progress: 60%

Available actions:

- Cancel

Rules:

- Cannot be reordered.
- Cannot be removed.
- Only one active execution exists per Job.

---

# Workflow Progress

Each Processing item can expand to show workflow progress.

The default view shows only the current user-facing step.

Example:

    Senior Backend Engineer

    Fetching Sources

    [Details]

Expanded view:

    Workflow Progress


    ✓ Load Job


    ✓ Collect Sources


    ⟳ Fetch Sources

        ✓ Primary Job URL

        ⟳ Company Website

        ○ Additional Links


    ○ Extract Content


    ○ Build Context


    ○ Validate Context

Example Expanded Workflow:

    Senior Backend Engineer

    Context Preparation

    Progress: 60%


    ┌────────────────────────────────────┐
    │ Workflow Progress                  │
    ├────────────────────────────────────┤
    │                                    │
    │ ✓ Load Job                         │
    │                                    │
    │ ✓ Collect Sources                  │
    │                                    │
    │ ⟳ Fetch Content                    │
    │                                    │
    │     ✓ Primary Job URL              │
    │     ⟳ Company Website              │
    │     ○ Additional Links             │
    │                                    │
    │ ○ Extract Content                  │
    │                                    │
    │ ○ Build Context                    │
    │                                    │
    │ ○ Validate Context                 │
    │                                    │
    └────────────────────────────────────┘

---

# Workflow Step Levels

The UI supports two levels.

## Level 1: User-facing Steps

Displayed by default.

Examples:

- Load Job
- Collect Sources
- Fetch Content
- Extract Content
- Build Context
- Validate Context
- Ready For Analysis

## Level 2: Step Details

Displayed after expansion.

Examples:

Fetch Content

    ✓ Primary Job URL

    ✓ Company Website

    ✕ GitHub URL

    Reason:
    Timeout

---

# Workflow Step State

Workflow steps have independent states.

Possible values:

- Pending
- Running
- Completed
- Failed
- Skipped

Example:

    Fetch Content

    Running

    Progress: 45%

---

# Queue Entry State

Queue state is different from workflow step state.

Possible values:

- Queued
- Running
- Completed
- Failed
- Cancelled

Example:

Queue state:

    Running

Workflow state:

    Fetching Sources

These concepts must not be combined.

---

# Queued

Queued displays Jobs waiting for execution.

Displayed information:

- Job title.
- Waiting reason.
- Queue position (optional).

Possible waiting reasons:

- Waiting for available worker.
- Scheduled retry.
- Manual pause.

Actions:

- Start.
- Remove.

Rules:

- Removing queue entry does not delete Job.
- Job remains in Jobs list.
- Queue entry is removed only.

---

# Failed

Failed displays failed ProcessingExecutions.

Displayed information:

- Job title.
- Failure reason.
- Last attempt time.

Actions:

- Retry.
- Remove.

Rules:

Retry:

- Cancels the failed execution (it leaves the Failed section).
- Creates a new ProcessingExecution.
- Creates a new queue entry (Queued).
- Only one active execution is kept per target.

Remove:

- Removes queue visibility only.
- Does not delete Job.

Failed Execution Detail:

    ┌──────────────────────────────────┐
    │ Frontend Engineer                │
    ├──────────────────────────────────┤
    │                                  │
    │ Status                           │
    │ Failed                           │
    │                                  │
    │ Step                             │
    │ Fetch Content                    │
    │                                  │
    │ Error                            │
    │ Primary URL timeout              │
    │                                  │
    │             Retry   Remove       │
    │                                  │
    └──────────────────────────────────┘

---

# Processing Completion

When execution completes successfully:

1. Mark ProcessingExecution as completed.
2. Remove queue entry.
3. Update Job status.
4. Notify frontend through SSE.

Before:

Jobs List

    Python Developer     Processing

Processing Queue

    Processing

    - Python Developer

After:

Jobs List

    Python Developer     Processed

Processing Queue

    Empty

---

# Real-Time Updates

The Processing Queue updates through SSE.

The frontend does not poll.

Supported events:

- execution.created
- execution.started
- workflow.step.started
- workflow.step.progress
- workflow.step.completed
- workflow.step.failed
- execution.completed
- execution.failed
- execution.cancelled

Live Update Example:

Before SSE event:

    Fetch Content

    ⟳ Running

After SSE event:

    Fetch Content

    ✓ Completed

Next step automatically becomes active:

    ⟳ Extract Content

---

# SSE Event Mapping

The backend should expose presentation-oriented workflow events.

The frontend should not depend on internal workflow implementation.

Example mapping:

Backend:

    FetchSourcesNode

Frontend:

    Fetching Sources

---

# Workflow Progress Example

A processing execution can expose:

    Context Preparation


    ✓ Load Job

    ✓ Collect Sources

    ⟳ Fetch Sources

    ○ Extract Content

    ○ Build Context

    ○ Validate Context

---

# Auto Refresh

The Processing Queue updates automatically when:

- A Job is queued.
- Execution starts.
- Workflow step changes.
- Progress changes.
- Execution completes.
- Execution fails.
- Execution is cancelled.
- Execution is retried.

Manual refresh is not required.

## Drawer Workflow Bootstrap

The drawer fetches each execution's workflow when it opens. If the execution is
still queued, the initial fetch may return no workflow yet — the backend only
persists workflow progress once the runner starts. The drawer then bootstraps
workflow state from the first live event:

- On `execution.started` (or another lifecycle event), or the first
  `workflow.step.*` event, the drawer refetches that execution's workflow once
  and renders the steps.
- Subsequent step events merge into the loaded workflow without refetching.
- The overall progress bar is recomputed client-side from the displayed steps
  so it advances during a run.

---

# Actions

| Action | Description                                |
| ------ | ------------------------------------------ |
| Cancel | Stop running execution                     |
| Start  | Start queued execution                     |
| Retry  | Create new execution from failed execution |
| Remove | Remove queue entry only                    |

---

# Queue Rules

- Jobs are the source of truth.
- Processing Queue is a live execution view.
- ProcessingExecution owns execution lifecycle.
- A Job has at most one active execution (enforced by the backend — creating a
  second one while an active execution exists returns HTTP 409).
- Retrying / reprocessing a failed Job cancels the failed execution so it leaves
  the Failed section and is replaced by a new queued execution.
- Completed executions disappear from Queue.
- Failed executions remain until retry or removal.
- Removing queue entry never deletes Job.
- Workflow details are expandable.
- Internal workflow implementation is hidden.

---

# Final UI Model

Job

↓

ProcessingExecution

↓

Queue Entry

↓

Workflow Progress

↓

Workflow Steps

↓

Step Details

---

# Empty State

No Jobs are currently being processed.

Jobs added to the queue will appear here.
