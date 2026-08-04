# Prompt: Implement the New Jobs List (Feature-Sliced) While Preserving the Legacy UI

## Objective

Implement the new **Jobs List** experience based on the project documentation.

This is **Frontend only**.

Do **NOT** implement the ProcessingExecution backend yet.

The legacy Jobs page must remain available but be clearly marked as **Deprecated** until the migration is complete.

---

# Read These Documents First

## Architecture

* docs/feature-sliced-design.md
* docs/fsd-rules.md
* docs/frontend-architecture.md
* docs/frontend-sync.md
* docs/nextjs-app-router.md

## UX

* docs/ux/features/jobs/page.md
* docs/ux/features/jobs/job-row.md
* docs/ux/features/jobs/processing-queue.md
* docs/ux/flows/jobs/browse-jobs.md
* docs/ux/flows/jobs/process-job.md
* docs/ux/flows/jobs/process-job-live.md

## API

* docs/api/jobs/list-jobs.md

## Domain

* docs/domain/jobs/job-list-item.md
* docs/domain/jobs/job-search.md

## Feature

* docs/features/job-processing.md

---

# Scope

Implement the new Jobs page using Feature-Sliced Design.

Do not touch the backend.

Mock or use placeholder values whenever required.

---

# Legacy Page

Do NOT delete the existing Jobs page.

Keep it operational.

Rename or visually mark it as:

* Deprecated
* Legacy
* Old Jobs List

The new Jobs page should become the default implementation.

---

# Feature-Sliced Structure

Create a completely new implementation.

Suggested structure:

app/

pages/

widgets/

features/

entities/

shared/

Do not reuse the legacy component hierarchy unless absolutely necessary.

---

# Jobs List

Implement the new row-based layout described in:

docs/ux/features/jobs/page.md

The Jobs page should contain:

* Header
* Search
* Filters
* Sort
* Jobs Table
* Processing Queue Drawer

---

# Job Row

Each row must display:

* Job Title
* Company
* Location
* Remote Badge
* Visa Badge
* Overall Score
* Fit Score
* Success Score
* Processing Status
* Updated Time
* Actions

Follow:

docs/ux/features/jobs/job-row.md

---

# New Processing Button

Each Job Row currently contains a legacy Process button.

Do NOT modify it.

Instead:

Add a completely new action.

Example label:

* Process V2

or

* AI Processing

or

* New Pipeline

Clicking this button should navigate the Job into the new processing workflow.

For now it may simply call the new API endpoint or a mocked handler.

Do not remove or replace the legacy Process button.

---

# Processing Queue Drawer

Implement the new drawer exactly as documented.

For now it can display mock data.

It should support:

* Running
* Waiting
* Completed
* Failed

No live updates are required yet.

---

# Data

The backend currently does not provide every field required by the new UI.

Whenever data is unavailable:

Use safe placeholders.

Examples:

Location

"Unknown"

Company Logo

Placeholder Avatar

Scores

—

Visa

Unknown

Remote

Unknown

Updated

—

Never crash because a property is missing.

The UI should gracefully degrade.

---

# Search

Implement:

* Search input
* Filters
* Sorting UI

Backend integration may be mocked.

The UI structure must exist.

---

# Table

Use a row-based table.

Do NOT use cards.

Optimize for:

* density
* scanning
* comparison

---

# Components

Create reusable components.

Examples:

JobRow

ScoreBadge

StatusBadge

ProcessingButton

JobActions

ProcessingStatus

JobsTable

JobsToolbar

JobsHeader

ProcessingDrawer

---

# State

Use TanStack Query where appropriate.

Local UI state should remain local.

Avoid global state unless necessary.

---

# Styling

Follow the existing design system.

Reuse shared UI components whenever possible.

Avoid introducing a new styling system.

---

# Types

Create proper TypeScript models based on:

docs/domain/jobs/job-list-item.md

Never use "any".

---

# Code Quality

* Strict TypeScript
* Feature-Sliced Design
* Small reusable components
* No duplicated code
* No TODO comments
* No dead code

---

# Deliverables

Implement:

* New Jobs Page
* New Jobs Table
* New Job Row
* New Processing Queue Drawer
* New Processing Button
* Search
* Filters
* Sorting UI
* Placeholder data support
* Feature-Sliced structure

Do NOT implement:

* ProcessingExecution backend
* SSE
* ARQ
* LangGraph
* Processing Timeline
* State Machine
* Live progress updates

Those will be implemented in later phases.
