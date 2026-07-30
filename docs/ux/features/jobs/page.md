# Jobs Page

## Purpose

The Jobs page is the primary workspace for managing imported jobs.

Users can:

- Import jobs
- Browse imported jobs
- Search and filter jobs
- Review processing status
- Start legacy processing
- Start ProcessingExecution
- Monitor background executions
- Open job details
- Review completed AI analysis

The page is centered around two concepts:

- Jobs
- Processing Executions

Jobs remain the primary business entity.

ProcessingExecution is the infrastructure responsible for running asynchronous AI workflows.

The legacy processing system remains available until migration is complete.

---

# Design Goals

- Jobs are always the primary focus.
- Browsing should never be interrupted by processing.
- Processing runs completely in the background.
- Live execution progress is always available.
- The page should scale to thousands of jobs.
- Users should understand exactly where each execution currently is.
- Future execution types should reuse the same infrastructure.

---

# Page Structure

```
Jobs Page

│

├── Jobs Header

├── Toolbar

├── Row-based Job List

├── Job Details Drawer

└── Processing Queue Drawer
```

---

# Default Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Jobs                                                     Queue           + Add Job          │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ Search                                                                            Filters    │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│ □ Senior Backend Engineer                    GetYourGuide               Berlin               │
│   Overall A++      Processing Running        Fit 92     Success 95                     [...] │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│ □ Python Platform Engineer                   Karla                      Berlin               │
│   Overall A       Completed                  Fit 84     Success 81                     [...] │
│                                                                                              │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│ □ Staff Backend Engineer                     EMIL Group                 Munich               │
│   Overall B       Queued                     Fit 71     Success 63                     [...] │
│                                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Jobs Header

Responsibilities

- Display page title
- Open Processing Queue
- Import jobs

Controls

| Control | Description                   |
| ------- | ----------------------------- |
| Queue   | Opens Processing Queue Drawer |
| Add Job | Opens Import Job Drawer       |

---

# Toolbar

Responsibilities

- Search jobs
- Filter jobs
- Sort jobs

Controls

| Control | Description                         |
| ------- | ----------------------------------- |
| Search  | Search by title, company or keyword |
| Filters | Filter jobs                         |
| Sort    | Sort jobs                           |

---

# Job List

The Job List is the primary workspace.

Jobs are displayed as rows rather than cards.

The row layout improves:

- scanning
- sorting
- filtering
- batch operations
- processing visibility

Each row represents one Job.

Selecting a row opens the Job Details Drawer.

---

# Job Row

Each row displays:

- Selection checkbox
- Job title
- Company
- Location
- Overall Score
- Fit Score
- Success Score
- Current ProcessingExecution status
- Updated time
- Quick actions

Example

```
□ Senior Backend Engineer

GetYourGuide

Berlin

Overall A++

Fit 92

Success 95

Running

[...]

```

---

# Row Actions

Each row contains two processing actions.

## Legacy Process

Uses the existing processing implementation.

This action remains available until migration is complete.

The implementation is intentionally unchanged.

---

## Process V2

Creates a new ProcessingExecution.

The execution is processed asynchronously.

Execution flow:

ProcessingExecution

↓

Queue

↓

Worker

↓

LangChain

↓

Result persistence

↓

Live updates through SSE

Legacy processing is never modified by this action.

---

# ProcessingExecution

Each ProcessingExecution belongs to exactly one Job.

The Job row always displays the latest execution.

Displayed information includes:

- Current status
- Current workflow step
- Last update time

The row never displays workflow logs.

Detailed execution information is available inside the Processing Queue Drawer.

---

# Execution Types

The infrastructure supports multiple execution types.

Current:

- Job Processing

Future:

- Company Processing
- Resume Generation
- Resume Optimization
- Cover Letter Generation
- Company Analysis
- Career Insights
- Market Analysis

The current Jobs page only exposes Job Processing.

---

# Job Details Drawer

Selecting a Job row opens the Job Details Drawer.

The drawer is independent from Processing.

The drawer displays:

- Job information
- Imported resources
- Parsed content
- Scores
- Recommendations
- Processing history
- Actions

The drawer never displays live workflow execution.

Live execution belongs to the Processing Queue Drawer.

---

# Processing Queue Drawer

The Processing Queue Drawer is the operational workspace for monitoring background executions.

The drawer is opened from:

- Queue button
- Process V2 button
- Active execution indicator

It never replaces the Jobs page.

The Jobs list always remains visible.

---

# Processing Drawer Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Processing Queue                                                [Close]      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Running (2)                                                                  │
│                                                                              │
│ Senior Backend Engineer                                                      │
│ Step: Extract Structured Information                                         │
│ ██████████████░░░░░░░░░░░░░░░░░░ 43%                                          │
│                                                                              │
│ Python Platform Engineer                                                     │
│ Step: Calculate Scores                                                       │
│ ███████████████████████████░░░░ 81%                                           │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ Waiting (3)                                                                  │
│                                                                              │
│ Backend Engineer                                                             │
│ Staff Engineer                                                               │
│ Platform Developer                                                           │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ Failed (1)                                                                   │
│                                                                              │
│ Senior Python Engineer                                                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

# Processing Execution Details

Selecting an execution expands its details.

The details page contains:

- Overview
- Timeline
- Current Step
- Progress
- Logs
- Execution Metadata

---

# Timeline

The timeline visualizes workflow progress.

Example

```
Queued

✓

Started

✓

Fetch Resources

✓

Validate Resources

✓

Extract Structured Information

● Running

Calculate Scores

Pending

Generate Recommendations

Pending

Completed
```

The active step is always highlighted.

---

# Live Progress

Progress is streamed using Server-Sent Events (SSE).

The UI updates automatically.

No manual refresh is required.

Displayed values include:

- Current status
- Current workflow step
- Percentage
- Current message
- Last update timestamp

---

# Execution Status

| Status    | Description                              |
| --------- | ---------------------------------------- |
| Created   | Execution exists but has not been queued |
| Queued    | Waiting for an available worker          |
| Starting  | Worker initialization                    |
| Running   | Workflow currently executing             |
| Completed | Successfully finished                    |
| Failed    | Finished with an unrecoverable error     |
| Cancelled | Execution cancelled                      |

---

# Job Status

Job Status and ProcessingExecution Status are different concepts.

Job Status describes the lifecycle of the Job entity.

ProcessingExecution Status describes the lifecycle of one execution.

A Job may have many ProcessingExecutions over time.

The UI always displays the latest execution.

---

# Processing Actions

While Running

Available actions:

- View Details

Unavailable:

- Process V2

---

While Queued

Available actions:

- Cancel

---

While Failed

Available actions:

- Retry

---

While Completed

Available actions:

- View Results
- Reprocess

---

# User Flow

## Process V2

```
User clicks Process V2

↓

ProcessingExecution created

↓

Queued

↓

Worker starts

↓

Workflow executes

↓

Progress streamed through SSE

↓

Completed

↓

Job updated
```

---

## Retry

```
Failed

↓

Retry

↓

New ProcessingExecution

↓

Queued

↓

Running

↓

Completed
```

---

## Legacy Processing

```
Legacy Process

↓

Existing Processing Pipeline

↓

Legacy Result
```

Legacy Processing remains unchanged until it is fully deprecated.

---

---

# Responsive Behavior

## Desktop

- Full-width row-based Jobs List
- Job Details Drawer opens from the right
- Processing Queue Drawer opens from the right
- Both drawers never replace the Jobs List

---

## Tablet

- Responsive row layout
- Narrower drawers
- Columns collapse when necessary

---

## Mobile

- Jobs displayed as compact rows
- Job Details opens as a full-screen sheet
- Processing Queue opens as a full-screen page
- Timeline becomes vertically scrollable

---

# Empty States

## No Jobs

Display:

- Empty illustration
- "No jobs have been imported yet."
- Add Job button

---

## No Active Executions

Display:

"No Processing Executions are currently running."

---

## No Failed Executions

Display:

"No failed executions."

---

# Loading States

Jobs List

- Skeleton rows
- Preserve table layout

Processing Queue

- Skeleton timeline
- Skeleton progress bars

---

# Error States

Jobs

- Unable to load jobs

Processing Queue

- Unable to load processing executions

SSE

- Lost connection
- Attempting to reconnect...

The UI should automatically reconnect.

---

# Batch Selection

The row layout supports future batch operations.

Potential future actions include:

- Batch Process
- Batch Delete
- Batch Retry
- Batch Export

Batch operations are not part of the current implementation.

---

# Sorting

The Jobs List should support sorting by:

- Updated Time
- Company
- Overall Score
- Fit Score
- Success Score
- Processing Status

---

# Filtering

Filters may include:

- Company
- Location
- Processing Status
- Overall Score
- Visa Sponsorship
- Remote
- Imported Date

---

# Search

Search should match:

- Job title
- Company
- Keywords
- Location

---

# Accessibility

The page should support:

- Keyboard navigation
- Screen readers
- High contrast mode
- Visible focus states

All interactive controls must be reachable without a mouse.

---

# Icons (Lucide)

| UI Element      | Icon              |
| --------------- | ----------------- |
| Add Job         | Plus              |
| Queue           | ListTodo          |
| Process V2      | Bot               |
| Legacy Process  | Play              |
| Search          | Search            |
| Filters         | SlidersHorizontal |
| Details         | Eye               |
| Retry           | RotateCcw         |
| Cancel          | Square            |
| Delete          | Trash2            |
| Success         | CircleCheck       |
| Failed          | CircleX           |
| Running         | LoaderCircle      |
| Timeline        | GitBranch         |
| Logs            | ScrollText        |
| Scores          | BadgePercent      |
| Recommendations | Sparkles          |

---

# Design Notes

The Jobs page is intentionally designed around **rows**, not cards.

Reasons:

- Faster scanning
- Better scalability
- Better sorting
- Better filtering
- Better operational visibility
- Consistent with professional tools such as GitHub, Jira, Linear, and Azure DevOps

Cards are intentionally avoided because this page is an operational workspace rather than a content browsing experience.

---

# Related Documents

Architecture

- docs/features/job-processing.md
- docs/domain/processing/processing-execution.md
- docs/domain/processing/events.md

API

- docs/api/processing/process-job.md
- docs/api/sse/processing-events.md

AI

- docs/ai/job-processing-chain.md
- docs/ai/job-processing-context.md

Queue

- docs/queue/processing/arq-processing.md

UX

- docs/ux/flows/jobs/process-job.md
- docs/ux/flows/jobs/process-job-live.md
- docs/ux/features/jobs/processing-queue.md

Development

- docs/development/sse.md
