# Frontend Sync Architecture

## Purpose

This document defines how frontend state synchronizes with backend processing execution state.

The frontend displays real-time Job processing progress using:

- REST API snapshots.
- SSE events.
- Local UI state.

The frontend does not own processing state.

The backend is the source of truth.

---

# Architecture

The synchronization model:

    Backend

        |

        +----------------+

        |                |

        v                v

    REST Snapshot       SSE Events


        |

        v


    Frontend State Layer


        |

        v


    UI Components

---

# State Sources

Frontend state has two sources.

## Initial State

Loaded through REST API.

Purpose:

- Initial page rendering.
- Drawer opening.
- Browser refresh recovery.

Example:

    GET /api/processing/executions/{execution_id}

Returns:

- Execution status.
- Current workflow progress.
- Completed steps.
- Running steps.
- Failed steps.

---

## Live Updates

Received through SSE.

Purpose:

- Real-time updates.
- Progress changes.
- Step transitions.
- Execution completion.

Events:

- execution.created
- execution.started
- workflow.step.started
- workflow.step.progress
- workflow.step.completed
- workflow.step.failed
- execution.completed
- execution.failed
- execution.cancelled

---

# Synchronization Flow

When user opens Processing Queue:

    Open Drawer


        |

        v


    Fetch Processing Executions


        |

        v


    Store Snapshot


        |

        v


    Connect SSE Stream


        |

        v


    Receive Events


        |

        v


    Update Local State


        |

        v


    Render UI

---

# Initial Snapshot

The frontend should never wait for SSE to build the initial state.

The flow:

    REST API

        ↓

    ProcessingExecution Snapshot

        ↓

    UI

Example state:

    {
      execution_id: "123",

      status: "running",

      current_step: {
        id: "fetch_content",
        title: "Fetch Content",
        progress: 60
      },

      workflow: {
        steps: []
      }
    }

---

# SSE Event Handling

SSE events update existing frontend state.

Example:

Initial:

    Fetch Content

    Running

    Progress: 40%

Event:

    workflow.step.progress

Payload:

    progress: 60

Updated UI:

    Fetch Content

    Running

    Progress: 60%

---

# Event Processing Rules

The frontend should:

- Process events in order.
- Ignore duplicated events.
- Recover from missing events.
- Replace state from snapshot when needed.

## Workflow Bootstrap

The Processing Drawer fetches each execution's workflow once when it opens. If
the execution is still queued, that fetch can return no workflow (the backend
only persists `workflow_progress` once the runner starts). The drawer handles
this by bootstrapping workflow state from the first live event:

- On `execution.started` / `execution.completed` / `execution.failed` /
  `execution.cancelled`, or the first `workflow.step.*` event for an execution
  with no cached workflow, the drawer refetches that execution's workflow a
  single time and renders the steps.
- Step events that arrive for an execution that already has a workflow are
  merged locally without refetching.
- The refetch is one-shot: once a workflow is loaded it is never replaced by a
  stale REST snapshot, so live SSE-merged progress is never clobbered.

---

# Event Recovery

If frontend detects:

- Missing event.
- Invalid state transition.
- Connection reconnect.

It should:

1. Request latest snapshot.
2. Replace local execution state.
3. Continue SSE subscription.

Example:

    SSE disconnected

          |

          v

    GET /api/processing/executions/{id}

          |

          v

    Restore state

          |

          v

    Continue stream

---

# Frontend State Model

The frontend should maintain:

## ProcessingExecution State

Contains:

- Execution status.
- Job information.
- Workflow progress.
- Current step.

Example:

    ProcessingExecutionState

        executionId

        jobId

        status

        workflowProgress

---

# Workflow State

Workflow state contains:

- Ordered steps.
- Current active step.
- Nested steps.
- Progress.

Example:

    WorkflowProgress

        Context Preparation

            Load Job

            Collect Sources

            Fetch Content

                Primary URL

                Company Website

---

# UI State

UI-only state is separate.

Examples:

- Drawer open/closed.
- Expanded workflow step.
- Selected execution.
- Error dialog visibility.

The frontend must not mix UI state with execution state.

---

# Component Data Flow

Example:

    ProcessingQueueDrawer


            |

            v


    ProcessingExecutionList


            |

            v


    ProcessingExecutionItem


            |

            v


    WorkflowProgress


            |

            v


    WorkflowStep

---

# TanStack Query Integration

REST snapshots should be managed by TanStack Query.

Example:

Query:

    processingExecutionQuery

Responsibilities:

- Cache execution snapshot.
- Handle loading.
- Handle errors.
- Refetch when required.

---

# SSE Integration With Cache

SSE events should update existing cache.

Example:

Event:

    workflow.step.progress

Action:

    Update processingExecutionQuery cache

The frontend should avoid unnecessary refetches for normal updates.

---

# Query Invalidation Rules

Refetch snapshot when:

- SSE reconnects.
- Event sequence gap detected.
- Execution state becomes inconsistent.
- User manually refreshes.

---

# Optimistic Updates

Avoid optimistic updates for:

- Workflow progress.
- Execution state.
- Step completion.

These values are controlled by backend execution.

Optimistic updates are only acceptable for UI actions:

- Drawer open.
- Expand/collapse.
- Local preferences.

---

# Processing Queue Lifecycle

Example:

Job Created

    ↓

ProcessingExecution Created

    ↓

Queue Entry Added

    ↓

SSE:

execution.created

    ↓

Worker Starts

    ↓

SSE:

execution.started

    ↓

Workflow Runs

    ↓

SSE:

workflow.step.progress

    ↓

Completed

    ↓

SSE:

execution.completed

    ↓

Remove Queue Entry

---

# Error Handling

Frontend should display:

## Execution Error

Example:

    Processing failed

    Unable to fetch source

## Step Error

Example:

    Fetch Content

    Failed

    Primary URL timeout

The frontend should not expose:

- Stack traces.
- Worker exceptions.
- Internal node errors.

---

# Loading States

Required states:

## Drawer Loading

When snapshot is loading.

## Empty State

No active executions.

## Reconnecting

When SSE reconnects.

## Recovering

When snapshot recovery is running.

---

# Related Documents

- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md
- docs/domain/processing/workflow-progress.md
- docs/ux/features/jobs/processing-queue.md
