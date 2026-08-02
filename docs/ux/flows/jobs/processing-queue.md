# Processing Queue Flow

## Purpose

This document defines the user flow for working with the **Processing Queue** while Jobs are being processed.

The flow describes how users:

- Open the Processing Queue.
- Monitor active executions.
- Review queued executions.
- Handle failed executions.
- Start queued executions.
- Cancel running executions.
- Retry failed executions.
- Remove queue entries.
- Recognize completion.

The Processing Queue is a monitoring tool.

It is not the primary place for managing Jobs.

Jobs always remain in the Jobs list.

---

# Related Documents

Feature specification:

- `docs/ux/features/jobs/processing-queue.md`
- `docs/ux/features/jobs/page.md`

Design system:

- `docs/ux/design-system/drawer.md`

Other flows:

- `docs/ux/flows/jobs/browse-jobs.md`
- `docs/ux/flows/jobs/process-job-live.md`

Backend concepts:

- `docs/domain/processing/processing-execution.md`
- `docs/domain/processing/workflow-progress.md`

API:

- `docs/api/processing/get-processing-queue.md`
- `docs/api/processing/get-processing-execution.md`
- `docs/api/sse/processing-events.md`

---

# Entry Points

Users can open the Processing Queue from:

- Jobs page header (Queue button).
- Jobs page Queue badge.
- Job Details drawer (monitor action).

The Queue badge always shows live statistics:

```text
Queue

2 Running

4 Waiting
```

---

# Opening The Queue

## User Action

User clicks the **Queue** button.

## System Behavior

The frontend:

1. Fetches the queue snapshot.

```
GET /api/processing/queue
```

2. Renders the current state.

3. Subscribes to the SSE stream.

```
GET /api/sse/processing-events
```

Flow:

```text
Open Queue

↓

Fetch Queue Snapshot

↓

Render State

↓

Subscribe SSE
```

## UI Mock: Processing Queue Drawer

```text
┌─────────────────────────────────────────────┐
│ Processing Queue                      Close │
├─────────────────────────────────────────────┤
│                                             │
│ Processing (2)                              │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Senior Backend Engineer                 │ │
│ │ Fetching Sources                        │ │
│ │ ██████████████░░░░ 60%                  │ │
│ │                             Details    │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Queued (3)                                  │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Python Developer                        │ │
│ │ Waiting for worker                      │ │
│ │                        Start   Remove   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Failed (1)                                  │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ Frontend Engineer                       │ │
│ │ Failed to fetch source                  │ │
│ │                         Retry   Remove  │ │
│ └─────────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

---

# Main Flow

```text
Open Queue

↓

Snapshot Loaded

↓

(Optional) Expand Execution

↓

Monitor Progress

↓

Continue Working

↓

Execution Completes
```

The user never leaves the Jobs page.

The drawer remains available while browsing.

---

# Processing Section

Displays Jobs currently executed by workers.

Each item shows:

- Job title.
- Current workflow step.
- Progress bar.
- Percentage.

Actions:

- Cancel.

## Start Processing

```text
Ready

↓

Queued

↓

Processing

↓

Completed
```

The Job appears in the Processing section while a worker handles it.

---

# Queued Section

Displays Jobs waiting for execution.

Each item shows:

- Job title.
- Waiting reason.

Possible waiting reasons:

- Waiting for available worker.
- Scheduled retry.
- Manual pause.

Actions:

- Start.
- Remove.

## Start Action

```text
Queued

↓

Start

↓

Processing

↓

Completed
```

Starting a queued execution moves it into the Processing section.

## Remove Action

Removing a queue entry:

- Removes the entry from the queue only.
- Does not delete the Job.

```text
Queued

↓

Remove

↓

Entry Removed

Job Remains in Jobs List
```

---

# Failed Section

Displays failed executions waiting for user action.

Each item shows:

- Job title.
- Failure reason.

Actions:

- Retry.
- Remove.

## Retry Action

```text
Failed

↓

Retry

↓

Queued

↓

Processing

↓

Completed
```

Retry creates a new ProcessingExecution.

The previous failed execution remains historical.

## Remove Action

Removing a failed entry:

- Removes queue visibility only.
- Does not delete the Job.

---

# Cancel Action

Cancelling a running execution:

```text
Processing

↓

Cancel

↓

Cancelled

↓

Entry Removed
```

Running executions request graceful termination.

Queued executions can be cancelled immediately.

---

# Monitoring Progress

Each Processing item can be expanded.

## Collapsed

```text
Senior Backend Engineer

Fetching Sources

██████████████░░░░ 60%

[Details]
```

## Expanded

```text
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
```

Progress updates are delivered through SSE.

Only the affected execution is updated.

The drawer never reloads completely.

---

# Live Updates

The queue is event-driven.

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
- queue.entry.removed

Example:

Before:

```text
Fetch Content

⟳ Running
```

After `workflow.step.completed`:

```text
Fetch Content

✓ Completed
```

The next step becomes active automatically.

---

# Completion

When processing completes successfully:

Before:

```text
Processing Queue

Senior Backend Engineer

Processing
```

After:

```text
Processing Queue

Empty
```

The Job remains in the Jobs list with status **Processed**.

The queue entry is temporary.

---

# Reconnection

If the SSE connection fails:

```text
Reconnecting...
```

The frontend:

1. Re-fetches the execution snapshot.
2. Restores workflow state.
3. Continues listening.

The user can continue browsing in the meantime.

---

# Empty States

## No Active Executions

```text
No active processing jobs.

Jobs added to the queue will appear here.
```

## No Failed Executions

```text
No failed executions.
```

---

# Responsive Behavior

## Desktop

Medium drawer (`md`) sliding from the right.

The Jobs list remains visible.

## Tablet

Medium drawer (`md`).

## Mobile

Full-screen drawer.

---

# Accessibility

- Keyboard navigation.
- Focus trap while the drawer is open.
- Escape closes the drawer.
- Progress bars expose ARIA progress values.
- Queue changes are announced to screen readers.
- Focus returns to the Queue button after closing.

---

# Related Documents

- `docs/ux/features/jobs/processing-queue.md`
- `docs/ux/features/jobs/page.md`
- `docs/ux/design-system/drawer.md`
- `docs/ux/flows/jobs/process-job-live.md`
- `docs/api/processing/get-processing-queue.md`
- `docs/api/sse/processing-events.md`
