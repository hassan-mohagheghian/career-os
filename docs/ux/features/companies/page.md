# Companies Page

## Purpose

The Companies page is the workspace for browsing and managing processed companies.

Users can:

- Add a new company (via notes and links)
- Browse processed companies
- Search companies
- Filter companies by industry
- Sort companies
- View company details (intelligence, scores, notes, jobs)
- Edit company core data
- Reprocess a company
- Delete a company
- Open the Company Queue (legacy company processing pipeline)

The Companies page mirrors the Jobs v2 page UX: virtualized table, server-side
pagination, infinite scroll, and Sheet-based drawers.

---

# Design Principles

The page follows these principles.

- Companies are always the primary business entity.
- Browsing must never be blocked by background processing.
- Company processing is asynchronous and **legacy** — it is not the
  Processing-Execution / SSE model used by Jobs. It is monitored through the
  Company Queue drawer, which polls the pending-companies endpoint.
- The Company List is optimized for very large datasets.
- Users can continue working while companies are processing.

---

# High-Level Layout

```text
Companies Page

├── Header
├── Toolbar
├── Company List
├── Company Queue Drawer
├── Company Detail Drawer
├── Company Edit Drawer
└── Add Company Drawer
```

---

# Desktop Layout

```text
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ ⛭ Companies (128)                    Loaded 25 of 128          Queue (3)        + Add Company │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ Search .........................                                          [Industry ▾] [Clear]│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│ Grade │ Name │ Industry │ Location │ Size │ Jobs │ Scores │ Status │ Updated │ Actions     │
│───────────────────────────────────────────────────────────────────────────────────────────────│
│  A+   │ Acme │ Software │ Berlin   │ 1-50 │ 12   │ F 85 │ S 90 │ O 88 │ Processed │ 2m │ ⋯ │
│  B    │ Beta │ Fintech  │ Munich   │ 51-200│ 4    │ F 60 │ S 55 │ O 58 │ Completed │ 5m │ ⋯ │
│  —    │ Nova │ Health   │ —        │ —    │ 0    │ F —  │ S —  │ O —  │ Pending    │ 1h │ ⋯ │
│                                                                                               │
│                                        Loading more companies...                              │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# Primary Sections

## Header

Responsibilities

- Display page title and total count.
- Display loaded-vs-total count.
- Display Company Queue summary badge.
- Open Company Queue drawer.
- Open Add Company drawer.

Controls

| Control      | Description                        |
| ------------ | ---------------------------------- |
| Queue        | Opens the Company Queue drawer.    |
| Add Company  | Opens the Add Company drawer.      |

---

## Queue Badge

The Queue button displays the total number of pending companies across all
non-terminal states (created, pending, queued, processing, failed).

```text
Queue

3
```

The badge is refreshed by polling `GET /api/pending-companies` every 5 seconds
while the queue drawer state is tracked by the widget's react-query query.

---

## Toolbar

Responsibilities

- Search companies.
- Filter companies by industry.
- Clear active filters.

Controls

| Control  | Description                                       |
| -------- | ------------------------------------------------- |
| Search   | Search by name, industry, city or description.    |
| Industry | Filter by exact industry.                         |
| Clear    | Clears all active filters.                        |

Changing filters never reloads the entire page.

Search is debounced (300ms) via the shared `DebouncedInput` primitive.

---

# Company List

The Company List is implemented as a virtualized row-based table (mirrors the
Jobs v2 `JobsTable`).

The frontend **does not use page numbers**.

Instead it uses **Infinite Loading** via cursor-based pagination.

The backend exposes a cursor-paginated API (`GET /api/companies/list`).

The Company List preserves:

- Search
- Industry filter
- Sorting
- Scroll position

when opening Company Details.

---

# Infinite Loading

Loading sequence

```text
Open Companies

↓

Load first page (page_size=25)

↓

Render rows

↓

User scrolls

↓

Reach loading threshold (sentinel, 200px margin)

↓

Request next page with cursor

↓

Append rows

↓

Repeat until has_more = false
```

Configuration

| Property          | Value            |
| ----------------- | ---------------- |
| Initial page size | 25               |
| Next page size    | 25               |
| Pagination        | Backend only     |
| Frontend UX       | Infinite Loading |

---

# Row Columns

| Column    | Description                               |
| --------- | ----------------------------------------- |
| Grade     | Overall grade badge (A++ … D)             |
| Name      | Company logo and name                     |
| Industry  | Industry classification                   |
| Location  | City, Country                             |
| Size      | Company size band                         |
| Jobs      | Number of linked, non-deleted jobs        |
| Scores    | Fit / Success / Overall score values      |
| Status    | Legacy processing state                   |
| Updated   | Relative update time                      |
| Actions   | Row actions (Details, Reprocess, Edit, Delete) |

---

# Column Details

## Grade

Displays the overall grade badge.

```text
A++
```

Grade colors match the Jobs design tokens:

| Grade | Color |
| ----- | ----- |
| A++   | Green |
| A+    | Green |
| A     | Lime  |
| A-    | Green |
| B+    | Blue  |
| B     | Blue  |
| C     | Orange |
| D     | Red   |

When no grade exists an em dash (`—`) is shown.

---

## Name

Displays

- Company logo (if present)
- Company name

```text
◉ Acme GmbH
```

---

## Industry

Displays the company industry, truncated.

```text
Software Development
```

---

## Location

Displays `City, Country`, or an em dash.

```text
Berlin, Germany
```

---

## Size

Displays the company size band.

```text
51-200
```

---

## Jobs

Displays the count of linked jobs (`JobModel.deleted == 0`).

```text
12
```

Zero jobs displays `—`.

---

## Scores

Displays three compact score badges.

```text
F 85   S 90   O 88
```

Color thresholds (matches `ScoreBadge` in jobs-v2):

| Value  | Color   |
| ------ | ------- |
| ≥ 90   | Green   |
| ≥ 70   | Emerald |
| ≥ 50   | Yellow  |
| ≥ 30   | Orange  |
| < 30   | Red     |

Null scores display `—`.

---

## Status

Displays the legacy company processing status badge.

| Status     | Color   |
| ---------- | ------- |
| created    | Gray    |
| pending    | Sky     |
| queued     | Yellow  |
| processing | Blue (pulsing dot) |
| running    | Emerald (pulsing dot) |
| completed  | Green   |
| processed  | Green   |
| failed     | Red     |
| cancelled  | Red     |

---

## Updated

Displays relative time via the shared `DateTime` component.

```text
Just now

2 minutes ago
```

---

# Row Actions

Each row provides four icon actions (tooltip buttons):

| Action    | Description                           |
| --------- | ------------------------------------- |
| Details   | Opens Company Details drawer.         |
| Reprocess | Re-enqueues the company for processing. |
| Edit      | Opens Company Edit drawer.            |
| Delete    | Deletes the company (with confirm).   |

All row actions stop propagation so clicking an action never opens the detail
drawer.

---

# Company Detail Drawer

Selecting a row opens the Company Detail drawer (Sheet from the right).

The drawer shows:

- Overall grade + Fit / Success / Overall score cards
- Company name, logo, industry
- Location, size, company type, linked-job count badges
- Actions: View All Jobs, Website, Reprocess, Delete
- Tabs:
  - **Original Notes** — `CompanyNotesTab` (notes + links CRUD)
  - **Intelligence** — company intelligence sections (product or recruiter variant)
  - **Scores** — full score breakdown with factors and calculation
  - **Jobs** — linked jobs list (`CompanyJobsTab`)

The drawer loads the company once via `GET /api/companies/list/{id}`, which
returns all company data (base fields, status, notes, links, intelligence,
scores, jobs) in a single payload. The tabs read from that payload — no
separate `/links`, `/jobs` or local-history calls are made.

---

# Company Edit Drawer

The Edit drawer (Sheet) edits core company fields:

- Name (required)
- Industry
- City / Country
- Company Size / Company Type
- Website
- Description

Saving calls `PUT /api/companies/{id}` and invalidates the list and detail
queries.

---

# Add Company Drawer

The Add Company drawer (Sheet) collects:

- Free-text notes (company name, description, observations)
- Links (LinkedIn, Website, Careers, GitHub, custom)

Submitting calls `POST /api/pending-companies` with `notes`, `links`, and
`source: "web"`. The created pending company is enqueued for processing by the
legacy pipeline (`enqueue_company_sync`). After a successful submit the Company
Queue drawer opens.

---

# Company Queue Drawer

The Company Queue drawer (Sheet) monitors the **legacy** company processing
pipeline. It is a monitoring tool, not a replacement for the Company List.

The drawer polls `GET /api/pending-companies` every 5 seconds (react-query
`refetchInterval`).

Sections:

| Section              | Statuses included      | Actions                    |
| -------------------- | ---------------------- | -------------------------- |
| Created              | created                | Process, Delete            |
| Pending              | pending                | Process, Delete            |
| Queued               | queued                 | Delete                     |
| Processing           | processing, running    | Delete                     |
| Failed / Cancelled   | failed, cancelled      | Process, Delete            |

Each item shows its input text (or first note), current node / status, error,
and up to four parsed notes/links.

Process calls `POST /api/pending-companies/{id}/process`; Delete calls
`DELETE /api/pending-companies/{id}`.

> The company processing pipeline is legacy: `pending_companies` +
> `enqueue_company_sync` + the LangGraph company graph. It is intentionally
> **not** rebuilt as a Processing Execution. Polling is used instead of SSE.

---

# Sorting

Supported sort fields (backend, NULLS LAST):

- `created_at` (default, desc)
- `updated_at`
- `name`
- `overall_score` (via Scores column popover)
- `fit_score`
- `success_score`

Sorting is always performed by the backend. Rows where the sort column is empty
sort last in both directions.

---

# Empty States

## No Companies

```text
No companies have been processed yet.
```

## No Search Results

```text
No companies match your search.

Try another keyword or remove filters.
```

---

# Loading States

## Initial Loading

- Skeleton rows

## Infinite Loading

```text
Loading more companies...
```

Existing rows remain interactive.

---

# Error States

## Backend Error

```text
Unable to load companies.

Retry
```

---

# Performance Requirements

The page must support

- Large company datasets
- Virtual scrolling
- Infinite loading
- Stable scroll position

The frontend never renders all rows simultaneously; only visible rows are
mounted.

---

# Related Documents

- `docs/api/companies/list-companies.md`
- `docs/ux/features/companies/company-row.md`
- `docs/ux/features/companies/company-detail.md`
- `docs/ux/features/companies/add-company.md`
- `docs/ux/features/companies/company-queue.md`
- `docs/ux/flows/companies/browse-companies.md`
- `docs/ux/features/jobs/page.md` (reference: shared virtualized-table UX)
