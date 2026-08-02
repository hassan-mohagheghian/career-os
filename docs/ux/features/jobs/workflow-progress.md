# Workflow Progress Component

## Purpose

The Workflow Progress component displays the current execution progress of a Job workflow.

It provides users with:

- Current processing stage.
- Completed steps.
- Running steps.
- Failed steps.
- Nested workflow details.
- Progress visibility.

The component is used inside:

- Processing Queue Drawer.
- Job Details page.
- Future execution history views.

---

# Responsibility

Workflow Progress is responsible for displaying workflow state.

It does not:

- Execute workflows.
- Manage execution state.
- Communicate directly with LangGraph.
- Manage SSE connections.

The component only consumes WorkflowProgress data.

---

# Data Source

Input model:

WorkflowProgress

Provided by:

- ProcessingExecution API.
- SSE processing events.

Related documents:

- docs/domain/processing/workflow-progress.md
- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md

---

# Component Structure

WorkflowProgress

    WorkflowStepList

        WorkflowStep

            WorkflowStepChildren

---

# UI Concept

The default view should show high-level workflow steps.

Users should be able to expand steps to see details.

The UI should balance:

- Visibility.
- Simplicity.
- Debugging capability.

---

# UI Mock: Workflow Progress Tree

Place:

This is the main workflow visualization.

Example:

    Workflow Progress

    Context Preparation

    ✓ Load Job
      Completed

    ✓ Collect Sources
      Completed

    ⟳ Fetch Content
      Progress: 60%

        ✓ Primary Job URL
          Completed

        ⟳ Company Website
          Running
          Progress: 40%

        ○ Additional Links
          Pending

    ○ Extract Content
      Pending

    ○ Build Context
      Pending

---

# Step Display

Each workflow step displays:

- Status icon.
- Step title.
- Progress percentage.
- Optional child steps.
- Optional error information.

Example:

Running step:

Fetch Content

Status:

Running

Progress:

60%

Completed step:

✓ Fetch Content

Status:

Completed

Failed step:

! Fetch Content

Status:

Failed

Pending step:

○ Fetch Content

Status:

Pending

---

# Step States

Supported states:

- pending
- running
- completed
- failed
- skipped

---

# Status Representation

## Pending

Meaning:

The step has not started yet.

Display:

○

---

## Running

Meaning:

The step is currently executing.

Display:

⟳

Optional:

Progress percentage.

Example:

Fetch Content

Running

60%

---

## Completed

Meaning:

The step finished successfully.

Display:

✓

Example:

✓ Fetch Content

Completed

---

## Failed

Meaning:

The step failed.

Display:

!

The UI may display:

- Error message.
- Retry action.

Example:

! Fetch Content

Failed

Reason:

Primary URL timeout

---

## Skipped

Meaning:

The step was intentionally skipped.

Display:

—

---

# Nested Steps

Steps may contain children.

Example:

Parent step:

Fetch Content

Children:

- Primary URL.
- Company Website.
- Additional Links.

Rules:

- Children are hidden by default.
- Users expand when needed.
- Parent progress is calculated by backend.
- Frontend only renders the received state.

---

# Expand / Collapse Behavior

Default:

Collapsed.

Collapsed state:

    Fetch Content

    Progress: 60%

Expanded state:

    Fetch Content

    Progress: 60%

        ✓ Primary URL

        ⟳ Company Website

        ○ Additional Links

---

# UI Mock: Step Expansion States

Collapsed:

    +--------------------------------+
    | ⟳ Fetch Content          60%   |
    +--------------------------------+

Expanded:

    +--------------------------------+
    | ⟳ Fetch Content          60%   |
    +--------------------------------+
    |                                |
    |   ✓ Primary URL                |
    |     Completed                  |
    |                                |
    |   ⟳ Company Website            |
    |     Running 40%                |
    |                                |
    |   ○ Additional Links            |
    |     Pending                    |
    |                                |
    +--------------------------------+

---

# Progress Calculation

The component does not calculate progress.

Backend provides:

- Step progress.
- Workflow progress.

Frontend responsibility:

- Render progress.
- Render state.
- Render transitions.

---

# Animation Rules

Allowed:

- Progress bar animation.
- Step status transition.
- Expand/collapse animation.

Avoid:

- Continuous movement.
- Excessive animations.
- Automatic expansion of steps.

---

# Error Display

Failed steps may show error details.

Example:

Fetch Content

Status:

Failed

Reason:

Primary URL timeout

Error details should be expandable.

Errors are prefixed with the failing step, e.g. `[load_job]`:

Reason:

`[load_job] Failed to parse job data: ...`

---

# Responsive Behavior

Desktop:

Display full workflow tree.

Mobile:

Display collapsed step list.

Users expand individual steps when needed.

---

# Accessibility

Requirements:

- Keyboard expandable steps.
- Screen reader labels.
- Status should not rely only on color.
- Progress values must have accessible labels.

---

# Empty State

If workflow has no steps:

Display:

No workflow progress available.

---

# Loading State

While loading:

Display:

Workflow Progress

Loading steps...

---

# Integration With Processing Queue

Processing Queue owns:

- Execution item.
- Job status.
- Actions.

Workflow Progress owns:

- Step visualization.
- Progress display.
- Step expansion.

---

# Design Rules

- Show high-level workflow steps by default.
- Hide detailed child steps initially.
- Allow manual expansion.
- Do not expose internal LangGraph nodes.
- Do not expose worker implementation details.
- Do not connect directly to SSE.
- Consume state from parent components.

---

# Related Documents

- docs/ux/features/jobs/processing-queue.md
- docs/ux/flows/jobs/process-job-live.md
- docs/domain/processing/workflow-progress.md
- docs/api/processing/get-processing-execution.md
- docs/api/sse/processing-events.md
- docs/architecture/frontend-sync.md
