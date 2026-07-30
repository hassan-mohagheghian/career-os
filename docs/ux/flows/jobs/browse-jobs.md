# Browse Jobs Flow

## Purpose

This document describes how users browse, search, filter, sort, and start processing Jobs.

The Jobs page is the primary workspace of the application.

Processing is a secondary activity that should never interrupt browsing.

---

# User Goals

Users should be able to:

- Browse imported jobs
- Search for specific jobs
- Filter jobs
- Sort jobs
- View job details
- Start a new Processing Execution
- Monitor execution progress
- Continue browsing while processing runs

---

# Primary Flow

```text
Open Jobs Page

↓

Load Jobs

↓

Browse List

↓

(Optional)

Search

↓

(Optional)

Apply Filters

↓

(Optional)

Sort

↓

Select Job

↓

Open Job Details

↓

(Optional)

Start Processing Execution
```

---

# Initial Page Load

When the Jobs page opens:

1. Request the first page of jobs.
2. Display loading placeholders.
3. Render the table when data arrives.
4. Subscribe to Processing SSE events.
5. Continue listening while the page is open.

The page should never block while background processing is running.

---

# Searching

Users can type inside the search box.

The frontend should:

- debounce input
- preserve filters
- preserve sorting
- reload page 1

Search updates only the list.

No navigation occurs.

---

# Filtering

Users may filter by:

- Processing Status
- Job Status
- Company
- Location
- Remote
- Visa Sponsorship
- Score Range

Changing a filter reloads the list.

---

# Sorting

Users may sort by:

- Updated
- Created
- Overall Score
- Fit Score
- Success Score
- Company
- Title

Sorting affects only the current query.

---

# Opening Job Details

Selecting a row opens the Job Details drawer.

The list remains visible.

The current search state is preserved.

---

# Starting Processing

The user clicks:

```text
Start Processing
```

inside a Job row.

The frontend:

1. Sends

```text
POST /api/processing/jobs/{jobId}
```

2. Receives

```text
ProcessingExecutionId
```

3. Updates the row immediately.

4. Starts receiving SSE events.

The user never leaves the Jobs page.

---

# Live Updates

While browsing:

SSE events update only affected rows.

Example:

```text
Queued

↓

Running

↓

Extracting

↓

Scoring

↓

Completed
```

The entire table should never reload because one row changes.

---

# Concurrent Processing

Multiple jobs may execute simultaneously.

Each row updates independently.

The user may:

- continue browsing
- search
- filter
- open details
- start additional executions

without interrupting running executions.

---

# Failure Flow

```text
Running

↓

Failed
```

The row displays:

- failed state
- error badge
- Retry action

The user may retry without refreshing the page.

---

# Completion Flow

```text
Running

↓

Completed
```

When completed:

- scores update
- processing status changes
- last execution timestamp updates
- row animations stop

No manual refresh is required.

---

# Empty States

## No Jobs

Display:

- illustration
- explanation
- Add Job button

---

## No Search Results

Display:

```text
No jobs match your current filters.
```

Offer:

- Clear Filters

---

# Performance Requirements

The Jobs page should:

- use pagination
- virtualize rows if needed
- avoid full-page refreshes
- update only changed rows
- preserve current filters
- preserve current sorting
- preserve current page

---

# Related Documents

- docs/ux/features/jobs/page.md
- docs/api/jobs/list-jobs.md
- docs/api/sse/processing-events.md
- docs/features/job-processing.md
