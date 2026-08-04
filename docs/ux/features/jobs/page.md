# Jobs Page

## Purpose

The Jobs page is the primary workspace for browsing, managing, and processing imported jobs.

Users can:

- Import new jobs
- Browse imported jobs
- Search jobs
- Filter jobs
- Sort jobs
- View job details
- Start AI Processing Execution
- Monitor live processing
- Open the Processing Queue
- Retry failed executions
- Review completed executions

The Jobs page always remains the primary workspace.

Background processing is completely separated from browsing and is monitored through the Processing Queue.

---

# Design Principles

The page follows these principles.

- Jobs are always the primary business entity.
- Browsing must never be blocked by background processing.
- Processing is asynchronous.
- The Job List is optimized for very large datasets.
- Users can continue working while jobs are processing.
- Live updates are received through Server-Sent Events (SSE).
- The Processing Queue is a monitoring tool, not a replacement for the Job List.

---

# High-Level Layout

```text
Jobs Page

├── Header
├── Toolbar
├── Job List
└── Processing Queue Drawer
```

---

# Desktop Layout

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Jobs                                                    Queue (2 Running • 4 Waiting)      + Import Job      │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Search .................................................................................................... │
│                                                                                                              │
│ Sort ▼                                         Filters ▼                                   Refresh          │
├──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│ # │ Job │ Company │ Location │ Overall │ Fit │ Success │ Rec │ Processing │ Updated │ Actions          │
│──────────────────────────────────────────────────────────────────────────────────────────────────────────────│
│                                                                                                              │
│ 1 │ Senior Backend Engineer │ GetYourGuide │ Berlin │ A++ │ 95 │ 91 │ ★ Apply │ Ready │ 2m │ ...          │
│ 2 │ Backend Engineer        │ Karla        │ Berlin │ A+  │ 90 │ 88 │ ☆ Apply │ Running │ now │ ...        │
│ 3 │ Python Developer        │ Flexa        │ Remote │ A   │ 86 │ 84 │ — Skip │ Failed │ 5m │ ...          │
│                                                                                                              │
│                                         Loading more jobs...                                                 │
│                                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Primary Sections

## Header

Responsibilities

- Display page title.
- Display processing queue summary.
- Open Processing Queue drawer.
- Open Import Job dialog.

Controls

| Control    | Description                        |
| ---------- | ---------------------------------- |
| Queue      | Opens the Processing Queue drawer. |
| Import Job | Opens the Import Job dialog.       |

---

## Queue Badge

The Queue button always displays current execution statistics.

Example

```text
Queue

2 Running

4 Waiting
```

The badge is updated in real time through SSE.

---

## Toolbar

Responsibilities

- Search jobs.
- Filter jobs.
- Sort jobs.
- Refresh current result set.

Controls

| Control        | Description                              |
| -------------- | ---------------------------------------- |
| Search         | Search by title, company or keyword.     |
| Status         | Filter by latest processing status.      |
| Location       | Filter by location (substring).          |
| Remote         | Filter by remote / on-site.              |
| Visa           | Filter by visa sponsorship.              |
| Favorites      | Toggle favorites-only view.              |
| Recommendation | Filter by apply / consider / skip.       |
| Sort           | Sort current result set.                 |
| Clear          | Clears all active filters.               |
| Refresh        | Reload current query.                    |

Changing filters never reloads the entire page.

The current scroll position is preserved whenever possible.

---

# Job List

The Job List is implemented as a virtualized row-based table.

The frontend **does not use page numbers**.

Instead it uses **Infinite Loading**.

The backend still exposes a paginated API.

The frontend automatically requests the next page while the user scrolls.

The Job List preserves:

- Search
- Filters
- Sorting
- Scroll position

when opening Job Details.

---

# Infinite Loading

Loading sequence

```text
Open Jobs

↓

Load first page

↓

Render rows

↓

User scrolls

↓

Reach loading threshold

↓

Request next page

↓

Append rows

↓

Repeat until has_next = false
```

Configuration

| Property          | Value               |
| ----------------- | ------------------- |
| Initial page size | 50                  |
| Next page size    | 50                  |
| Load threshold    | 80% of visible list |
| Pagination        | Backend only        |
| Frontend UX       | Infinite Loading    |

The user never interacts with page numbers.

The backend remains fully paginated.

Benefits

- Continuous browsing.
- Smaller network requests.
- Excellent performance.
- Preserved scroll position.
- Scales to tens of thousands of jobs.

---

# Job Selection

Selecting a row opens the Job Details drawer.

The row never expands inline.

Opening Job Details never interrupts active processing.

The Processing Queue drawer may remain open independently.

---

# Data Refresh

The list is refreshed through two mechanisms.

## Manual Refresh

The Refresh button reloads the current query.

## Automatic Refresh

Live SSE updates mutate the affected row in place (status, timestamps,
scores) without re-rendering the whole table.

When an execution reaches a **terminal state** (completed / failed /
cancelled), the list query is also invalidated and refetched in the
background. This guarantees the row reflects what is actually persisted by
the pipeline — e.g. the job title extracted during analysis and the final
execution status — even across a reload. Non-terminal events update the row
in place only.

# Job Row

Each row represents a single Job.

The row provides a compact overview of:

- Job identity
- Company
- Location
- AI evaluation
- Processing state
- Last update
- Available actions

Rows are never expandable.

Selecting a row opens the Job Details Drawer.

---

# Row Columns

| Column         | Description                                         |
| -------------- | --------------------------------------------------- |
| Select         | Multi-selection checkbox for future bulk operations |
| Favorite       | Star toggle for bookmarked jobs                     |
| Job            | Job title and employment type                       |
| Company        | Company logo and company name                       |
| Location       | City, country or Remote                             |
| Overall        | Overall AI Score                                    |
| Fit            | Fit Score                                           |
| Success        | Success Score                                       |
| Recommendation | Apply / Consider / Skip badge                       |
| Processing     | Current Processing Execution state                  |
| Updated        | Relative update time                                |
| Actions        | Row actions                                         |

---

# Column Details

##

Displays the legacy numeric identifier.

Example

```text
42
```

This value exists only for compatibility.

All new APIs use the UUID v7 identifier.

---

## Job

Displays

- Job title
- Employment type

Example

```text
Senior Backend Engineer

Full-time
```

---

## Company

Displays

- Company logo
- Company name

Example

```text
◉ GetYourGuide
```

If no logo exists

```text
□ GetYourGuide
```

---

## Location

Displays

Examples

```text
Berlin

Germany
```

or

```text
Remote
```

---

## Favorite

Displays a star toggle for the job's favorite flag.

```text
★   favorited

☆   not favorited
```

The toggle is optimistic and does not reload the list. Activating the Favorites
filter in the toolbar shows only favorited jobs.

---

## Recommendation

Displays the analysis recommendation as a compact badge.

```text
Apply
Consider
Skip
```

Color and meaning

| Badge     | Meaning   | Color   |
| --------- | --------- | ------- |
| Apply     | Overall ≥ 80 | Emerald |
| Consider  | Overall ≥ 60 | Amber   |
| Skip      | Otherwise    | Gray    |

Jobs without a completed analysis show an em dash (`—`).

The column is display-only (no sort). Filtering by recommendation happens
through the toolbar's Recommendation filter.

---

# Overall Score

The Overall Score is the primary recommendation score.

It is calculated independently.

It is **not** the average of Fit and Success.

Example

```text
A++

94

Excellent Match
```

Color

| Grade | Color  |
| ----- | ------ |
| A++   | Green  |
| A+    | Green  |
| A     | Lime   |
| B     | Blue   |
| C     | Orange |
| D     | Red    |

Hovering displays

```text
Overall Score

Calculated using

• Shared Rules

• Job Rules

• AI Recommendation Rules
```

---

# Fit Score

Measures technical compatibility.

Example

```text
95
```

Hover

```text
Fit Score

Python Backend

DDD

FastAPI

PostgreSQL
```

---

# Success Score

Measures application success probability.

Example

```text
91
```

Hover

```text
Success Score

Visa

Relocation

Language

Market

Company
```

---

# Processing Column

The Processing column represents the current Processing Execution.

Examples

## Ready

```text
Ready
```

---

## Queued

```text
Queued

Position #3
```

---

## Starting

```text
Starting...
```

---

## Running

```text
Extracting Resources

43%

2m remaining
```

---

## Completed

```text
Completed

5 minutes ago
```

---

## Failed

```text
Failed

Retry available
```

---

## Cancelled

```text
Cancelled
```

The Processing column updates live using SSE.

Only the affected row is updated.

The table must never refresh completely.

---

# Updated Column

Displays relative time.

Examples

```text
Just now

2 minutes ago

Yesterday
```

Hover shows the absolute timestamp, converted to the browser's **local** time.

```text
Jul 30, 2026, 4:32 PM (your local time)
```

The backend stores and serializes datetimes in UTC without a timezone marker;
the shared `DateTime` component interprets them as UTC and renders them in the
user's local timezone, so the displayed value always matches the current local
clock.

---

# Row Actions

Each row contains two processing systems.

The Legacy system remains available.

The new AI Processing Execution is introduced alongside it.

| Action         | Description                               |
| -------------- | ----------------------------------------- |
| Legacy Process | Existing processing pipeline (deprecated) |
| AI Process     | Starts Processing Execution               |
| Retry          | Retry failed execution                    |
| Cancel         | Cancel queued execution                   |
| Details        | Open Job Details                          |
| More           | Additional actions                        |

---

# AI Process Button

The new button starts the Processing Execution workflow.

It is independent of the legacy implementation.

Clicking the button

```text
Ready

↓

Queued

↓

Processing Queue
```

The Jobs page remains visible.

The Queue drawer updates automatically.

---

# Legacy Process Button

The previous implementation remains available.

It is marked as

```text
Legacy
```

or

```text
Deprecated
```

No new features are added to the legacy workflow.

It exists only for migration compatibility.

# Processing Queue Drawer

The Processing Queue is a monitoring workspace.

It is **not** the primary place for managing jobs.

Users continue browsing the Job List while monitoring active executions.

The drawer slides in from the right.

It never replaces the Jobs page.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ Processing Queue                             │
│                                              │
│ Running (2)                                  │
│──────────────────────────────────────────────│
│ Senior Backend Engineer                      │
│ Extracting Resources                         │
│ ████████████░░░░░░░░░░ 43%                   │
│                                              │
│ Python Developer                             │
│ Scoring Job                                  │
│ ██████████████████░░░░ 71%                   │
│                                              │
│──────────────────────────────────────────────│
│ Waiting (4)                                  │
│──────────────────────────────────────────────│
│ Backend Engineer                             │
│ Position #1                                  │
│                                              │
│ DevOps Engineer                              │
│ Position #2                                  │
│                                              │
│──────────────────────────────────────────────│
│ Failed (1)                                   │
│──────────────────────────────────────────────│
│ Rust Engineer                                │
│ Retry                                        │
└──────────────────────────────────────────────┘
```

---

# Drawer Sections

The drawer always contains three sections.

## Running

Contains executions currently processed by workers.

Each execution displays

- Job title
- Current workflow step
- Progress bar
- Percentage
- Estimated remaining time

---

## Waiting

Contains queued executions.

Each execution displays

- Job title
- Queue position

Example

```text
Queued

Position #4
```

---

## Failed

Contains failed executions.

Each execution displays

- Job title
- Failure state
- Retry action

---

# Running Item

Example

```text
Senior Backend Engineer

Extracting Resources

██████████░░░░░░░░░░

43%

Estimated

2m remaining
```

---

# Workflow Progress

The drawer reflects the Processing Execution workflow.

Typical execution

```text
Queued

↓

Starting

↓

Initializing Context

↓

Loading Rules

↓

Loading Prompt

↓

Extracting Resources

↓

Extracting Job

↓

Scoring Job

↓

Generating Summary

↓

Persisting Results

↓

Completed
```

Each transition is streamed immediately through SSE.

---

# Live Updates

The drawer is completely event-driven.

Every Processing Execution publishes events.

Examples

```text
Queued

↓

Running

↓

Extracting Resources

↓

Scoring

↓

Completed
```

Only the affected execution is updated.

The drawer never refreshes completely.

---

# Server-Sent Events

The frontend subscribes once.

```text
GET

/api/sse/processing
```

The connection remains open.

Incoming events update

- Running list
- Waiting list
- Failed list
- Progress bars
- Current workflow stage
- Queue positions

No polling is used.

---

# Job Details Integration

Clicking an execution inside the drawer opens the Job Details drawer.

The Processing Queue drawer automatically closes.

The user always has only one drawer open.

---

# User Flows

## Start Processing

```text
Click

AI Process

↓

Job

Queued

↓

Appears

Waiting

↓

Worker Available

↓

Running

↓

Completed
```

---

## Failure

```text
Running

↓

Error

↓

Failed

↓

Retry

↓

Queued
```

---

## Cancel

```text
Queued

↓

Cancel

↓

Cancelled

↓

Removed

from Queue
```

Running executions cannot be cancelled immediately.

They request graceful termination.

---

# Empty States

## Running Empty

```text
No jobs are currently processing.
```

---

## Waiting Empty

```text
Queue is empty.
```

---

## Failed Empty

```text
No failed executions.
```

---

# Connection States

## Connected

```text
Live Updates

Connected
```

---

## Reconnecting

```text
Reconnecting...

Attempt 2
```

---

## Disconnected

```text
Connection Lost

Retrying...
```

The frontend automatically reconnects using EventSource.

---

# Performance Rules

The Processing Queue must

- Update only modified executions.
- Never reload the complete drawer.
- Never reload the Job List.
- Support hundreds of simultaneous executions.
- Preserve scroll position during updates.
- Batch frequent UI updates when necessary.

---

# Accessibility

- Progress bars expose ARIA progress values.
- Queue changes are announced to screen readers.
- Keyboard navigation is fully supported.
- Drawer can be closed with Escape.
- Focus returns to the Queue button after closing.

# Responsive Behavior

## Desktop

The Jobs page is optimized for widescreen development workstations.

Layout

- Full-width virtualized Job List.
- Right-side Processing Queue drawer.
- Persistent toolbar.
- Sticky table header.

The Job List always remains visible while the Processing Queue drawer is open.

---

## Tablet

The layout adapts to medium screens.

Changes

- Reduced column spacing.
- Company logo becomes optional.
- Processing drawer width is reduced.
- Secondary columns may collapse.

Priority order

1. Job
2. Company
3. Overall
4. Processing
5. Actions

---

## Mobile

The page switches to a mobile-friendly layout.

Changes

- Rows become stacked cards.
- Toolbar collapses.
- Filters open in a bottom sheet.
- Processing Queue opens as a full-screen modal.
- Infinite scrolling remains enabled.

---

# Search Behavior

Search is incremental.

Typing updates the result set after a **300ms debounce delay** — the toolbar
uses the shared `DebouncedInput` primitive (see
`docs/ux/design-system/input.md`). The input reflects keystrokes immediately,
but the server request fires only once typing pauses. Clearing the search is
immediate and cancels any pending request.

Supported fields

- Job Title
- Company Name
- Keywords
- Location

Search preserves

- Sorting
- Filters
- Scroll position (when possible)

---

# Filtering

Supported filters

- Favorites
- Recommendation
- Processing Status
- Location
- Overall Score
- Company
- Country
- Employment Type
- Remote / Hybrid / On-site
- Date Imported
- Processing State

Filters are applied server-side.

## Favorites Filter

A star toggle in the toolbar restricts the list to favorited jobs.

```text
☆ All Jobs
★ Favorites only
```

When active it counts as an active filter and is cleared by the toolbar's
Clear action alongside the others. Favoriting or unfavoriting a job while the
filter is active refetches the list so rows update immediately.

## Recommendation Filter

A dropdown in the toolbar restricts the list to jobs whose analysis produced
the selected recommendation.

```text
All
Apply
Consider
Skip
```

Jobs without a completed analysis never match. When active it counts as an
active filter and is cleared by the toolbar's Clear action alongside the
others.

## Processing Status Filter

The status filter lives in the toolbar and groups jobs by their **latest**
processing execution status:

```text
All
Created
Queued
Running
Completed
Failed
Not processed
```

`Not processed` selects jobs that have **no** processing execution at all —
jobs that were imported but never queued. Selecting it counts as an active
filter and is cleared by the toolbar's Clear action alongside the others.

---

# Location Filter

A compact input in the toolbar filters jobs by location.

Typing matches the job's location case-insensitively (substring match) — e.g.
`berlin` matches `Berlin, Germany`.

```text
Berlin, Germany
Amsterdam, Netherlands
Hamburg, Germany
```

The input is debounced (**300ms**, via `DebouncedInput`) so requests fire only
after typing pauses. An active location shows a ✕ clear button and counts as an
active filter, cleared by the toolbar's Clear action alongside the others.

---

# Sorting

Supported sort fields

- Imported Date
- Updated Date
- Overall Score
- Fit Score
- Success Score
- Company Name
- Job Title
- Status

Sorting is always performed by the backend.

Every sort follows a NULLS LAST policy: jobs where the sort column is empty
(for example a job that has not been scored yet) always sort last, in both
ascending and descending order.

The Status sort orders rows by the same status each row displays (the latest
processing execution). Jobs that were never processed always sort last, in both
ascending and descending order.

---

# Empty States

## No Jobs

```text
No jobs have been imported yet.

Import your first job to begin.
```

Actions

- Import Job

---

## No Search Results

```text
No matching jobs were found.

Try another keyword or remove filters.
```

---

## No Filter Results

```text
No jobs match the selected filters.
```

Action

```text
Clear Filters
```

---

# Loading States

## Initial Loading

Display

- Skeleton rows
- Loading indicator

The page layout must remain stable.

---

## Infinite Loading

When requesting the next page

```text
Loading more jobs...
```

Existing rows remain interactive.

---

## Refreshing

Refreshing does not clear the table.

Only affected rows are updated.

---

# Error States

## Backend Error

```text
Unable to load jobs.

Retry
```

---

## Network Error

```text
Connection lost.

Trying to reconnect...
```

---

## SSE Disconnected

```text
Live updates unavailable.

Reconnecting...
```

The user can continue browsing.

Only live updates pause temporarily.

---

# Row Density

Supported display modes

## Comfortable

Row Height

```text
80px
```

Default mode.

---

## Compact

Row Height

```text
64px
```

Optimized for large datasets.

---

# Accessibility

The page follows WCAG AA.

Requirements

- Keyboard navigation.
- Screen-reader labels.
- ARIA progress indicators.
- Visible focus states.
- High contrast support.
- Reduced motion support.

Keyboard shortcuts

| Shortcut | Action           |
| -------- | ---------------- |
| ↑ ↓      | Navigate rows    |
| Enter    | Open Job Details |
| Esc      | Close Drawer     |
| Ctrl + F | Focus Search     |

---

# Performance Requirements

The page must support

- 100,000+ jobs
- Virtual scrolling
- Infinite loading
- Partial row updates
- Stable scroll position

The frontend must never render all rows simultaneously.

Only visible rows are mounted.

---

# Design Tokens

## Status Colors

| Status    | Color  |
| --------- | ------ |
| Ready     | Gray   |
| Queued    | Blue   |
| Running   | Cyan   |
| Completed | Green  |
| Failed    | Red    |
| Cancelled | Orange |

---

## Score Colors

| Grade | Color  |
| ----- | ------ |
| A++   | Green  |
| A+    | Green  |
| A     | Lime   |
| B     | Blue   |
| C     | Orange |
| D     | Red    |

---

# Icons (Lucide)

| Element        | Icon              |
| -------------- | ----------------- |
| Import Job     | Plus              |
| Favorite       | Star              |
| Queue          | Workflow          |
| Search         | Search            |
| Filters        | SlidersHorizontal |
| Refresh        | RefreshCcw        |
| Legacy Process | PlayCircle        |
| AI Process     | Sparkles          |
| Retry          | RotateCcw         |
| Cancel         | Square            |
| Details        | Eye               |
| More           | EllipsisVertical  |
| Completed      | CircleCheck       |
| Failed         | CircleX           |
| Running        | LoaderCircle      |
| Waiting        | Clock3            |

---

# Related Documents

- `docs/workflows/job-processing.md`
- `docs/domain/processing/processing-execution.md`
- `docs/domain/processing/events.md`
- `docs/api/jobs/list-jobs.md`
- `docs/api/processing/process-job.md`
- `docs/api/sse/processing-events.md`
- `docs/ux/features/jobs/job-row.md`
- `docs/ux/features/jobs/processing-queue.md`
- `docs/ux/flows/jobs/browse-jobs.md`
- `docs/ux/flows/jobs/process-job-live.md`
- `docs/domain/processing/job-state-machine.md`
