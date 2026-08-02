# Process Job Live Flow

## Purpose

This document defines the user flow for monitoring a Job while it is being processed.

The flow describes how users:

- Start processing a Job.
- Open live processing view.
- Monitor workflow progress.
- Observe step changes.
- Handle failures.
- Retry failed executions.
- Cancel running executions.

This flow does not define backend execution logic.

Related backend concepts:

- ProcessingExecution.
- WorkflowProgress.
- SSE Events.
- TaskIQ background execution.
- LangGraph workflow execution.

---

# Overview

The user-facing lifecycle:

Job

↓

Processing Started

↓

Processing Queue Entry Created

↓

Live Processing View

↓

Workflow Progress Updates

↓

Success / Failure

↓

Processed / Failed

---

# Entry Points

Users can enter live processing view from:

- Jobs List.
- Processing Queue.
- Job Details page.

---

# Start Processing

## User Action

User clicks:

Start Processing

## System Behavior

The system:

1. Creates a ProcessingExecution.
2. Adds the Job to Processing Queue.
3. Starts background processing.
4. Emits execution events.

## UI State

Immediately after starting:

Job Status:

Queued

Processing Queue:

Queued

Senior Backend Engineer

Waiting for worker

---

# Open Live Processing View

## User Action

User opens Processing Queue drawer.

## System Behavior

Frontend:

1. Requests current execution snapshot.
2. Loads WorkflowProgress.
3. Subscribes to SSE events.

Flow:

Open Drawer

↓

Fetch ProcessingExecution Snapshot

↓

Render Current State

↓

Subscribe SSE

---

# Loading State

Example:

Processing Queue

Loading executions...

---

# Processing View

When execution starts:

Senior Backend Engineer

Status:

Processing

Current Step:

Fetching Sources

Progress:

60%

Details ▼

## UI Mock: Live Processing Drawer

````text
┌─────────────────────────────────────────────┐
│ Processing Queue                      Close │
├─────────────────────────────────────────────┤
│                                             │
│ Processing                                  │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                 │ │
│ │                                         │ │
│ │ Current Step                            │ │
│ │ Fetch Content                           │ │
│ │                                         │ │
│ │ ███████████████░░░░░ 60%                │ │
│ │                                         │ │
│ │ Workflow Details                 ▼      │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Queued                                      │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Python Developer                        │ │
│ │ Waiting for worker                      │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Failed                                      │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Frontend Engineer                       │ │
│ │ Fetch failed                            │ │
│ │                         Retry           │ │
│ └─────────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘

---

# Workflow Expansion

Users can expand an execution item.

Collapsed:

Context Preparation

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

○ Build Context


## UI Mock: Expanded Workflow Progress

```text
+------------------------------------------+
| Senior Backend Engineer                  |
+------------------------------------------+
|                                          |
| Context Preparation                      |
|                                          |
| ✓ Load Job                               |
|                                          |
| ✓ Collect Sources                        |
|                                          |
| ⟳ Fetch Content                          |
|                                          |
|    ✓ Primary Job URL                     |
|                                          |
|    ⟳ Company Website                     |
|                                          |
|    ○ Additional Links                    |
|                                          |
| ○ Extract Content                        |
|                                          |
| ○ Build Context                          |
|                                          |
| ○ Validate Context                       |
|                                          |
+------------------------------------------+

---

# Workflow Steps

The user-facing workflow contains high-level steps.

Example:

Context Preparation

- Load Job
- Collect Sources
- Fetch Content
- Extract Content
- Build Context
- Validate Context

Internal LangGraph nodes are not directly displayed.

The frontend only receives WorkflowProgress.

---

# Real-Time Updates

The UI updates through SSE events.

Example:

Initial:

Fetch Content

Running

40%

Event:

workflow.step.progress

Payload:

progress: 70

Updated:

Fetch Content

Running

70%

---

# Step Completion

When a step completes:

Before:

⟳ Fetch Content

After:

✓ Fetch Content

The next step becomes active automatically.

---

# Failed Processing

When execution fails:

Senior Backend Engineer

Status:

Failed

Failed Step:

Fetch Content

Reason:

Source unavailable

Actions:

Retry

Remove

---

# Retry Flow

## User Action

User clicks:

Retry

## System Behavior

The system:

1. Creates a new ProcessingExecution.
2. Adds a new queue entry.
3. Starts processing again.

The previous failed execution remains historical.

---

# Cancel Flow

## User Action

User clicks:

Cancel

## System Behavior

The system:

1. Requests cancellation.
2. Stops execution.
3. Emits cancellation event.
4. Removes queue entry.

UI:

Processing

Cancelled

---

# Completion Flow

When processing completes successfully:

Before:

Processing Queue

Senior Backend Engineer

Processing

After:

Processing Queue

Empty

Job List:

Senior Backend Engineer

Processed

The Job remains in the Jobs list.

The Queue entry is temporary.

---

# SSE Reconnection

If SSE connection fails:

UI:

Reconnecting...

Frontend:

1. Re-fetches current execution snapshot.
2. Restores workflow state.
3. Continues listening.

---

# Empty State

When no active processing exists:

No active processing jobs.

Jobs added for processing will appear here.

---

# User Decisions

## Workflow Detail Visibility

The default view should show high-level workflow steps.

Example:

Context Preparation

Fetching Sources

Building Context

Detailed steps should be expandable.

Example:

Fetching Sources

    Primary URL

    Company Website

    Additional Links

Reason:

- Avoid overwhelming users.
- Keep progress understandable.
- Allow debugging when needed.

---

# Component Structure

Suggested UI structure:

ProcessingQueueDrawer

    ProcessingExecutionList

        ProcessingExecutionItem

            WorkflowProgress

                WorkflowStep

                    ChildSteps

---

# Data Dependencies

REST:

GET /api/processing/executions/{execution_id}

SSE:

/api/sse/processing-events

Models:

- ProcessingExecution
- WorkflowProgress
- WorkflowStep

---

# Related Documents

- docs/ux/features/jobs/processing-queue.md
- docs/ux/features/jobs/workflow-progress.md
- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md
- docs/domain/processing/workflow-progress.md
- docs/architecture/frontend-sync.md
- docs/workflows/job-processing.md (realized trace-through: click → queue → SSE)
````
