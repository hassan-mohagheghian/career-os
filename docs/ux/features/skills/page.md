# Skills Page

## Purpose

The Skills page is the workspace for browsing and managing the skill inventory.

Users can:

- Add a new skill
- Browse all skills
- Search skills
- Filter skills by category
- Sort skills
- View skill details (level, roles, path, tags, aliases, roadmap, history)
- Edit skill core data
- Delete a skill
- Generate / Extend / Finegrain learning roadmaps from the detail drawer

The Skills page mirrors the Jobs/Companies v2 UX: virtualized table,
server-side pagination, infinite scroll, and Sheet-based drawers.

---

# Design Principles

- Skills are categorized into the canonical taxonomy: `technical`,
  `engineering`, `professional`, `domain`, `career`.
- Browsing must never be blocked by background roadmap generation.
- The Skills list is optimized for large inventories.
- Users can continue working while roadmaps are generating.

---

# High-Level Layout

```text
Skills Page

├── Header
├── Toolbar
├── Skills List
├── Skill Detail Drawer
├── Skill Edit Drawer
└── Add Skill Drawer
```

---

# Desktop Layout

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ ⛭ Skills (128)                    Loaded 25 of 128          + Add Skill      │
├───────────────────────────────────────────────────────────────────────────────┤
│ Search .........................                                          [Category ▾] [Clear]│
├───────────────────────────────────────────────────────────────────────────────┤
│ Name │ Category │ Level │ Roles │ Demand │ Conf. │ Created │ Mentions │ Act.│
│───────────────────────────────────────────────────────────────────────────────│
│ K8s  │ engineering│ Lv.4 │ DevOps│ 90%   │ 85%   │ 2m      │ 3        │ ⋯  │
│ Kafka│ technical │ Lv.2 │ Data  │ 70%   │ 60%   │ 5m      │ 1        │ ⋯  │
│ DDD  │ domain    │ Lv.3 │ Backend│ —    │ 45%   │ 1h      │ 0        │ ⋯  │
│                                                                               │
│                                        Loading more skills...                 │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

# Primary Sections

## Header

Responsibilities

- Display page title and total count.
- Display loaded-vs-total count.
- Open the Add Skill drawer.

Controls

| Control    | Description                  |
| ---------- | ---------------------------- |
| Add Skill  | Opens the Add Skill drawer.  |

---

## Toolbar

Responsibilities

- Search skills.
- Filter skills by category.
- Clear active filters.

Controls

| Control  | Description                                     |
| -------- | ----------------------------------------------- |
| Search   | Search by name, role, path, or alias.           |
| Category | Filter by one of the five canonical categories. |
| Clear    | Clears all active filters.                      |

Search is debounced (300ms) via the shared `DebouncedInput` primitive.

---

# Skills List

The Skills List is implemented as a virtualized row-based table (mirrors the
Jobs/Companies v2 `JobsTable` / `CompaniesTable`).

The frontend **does not use page numbers**.

Instead it uses **Infinite Loading** via cursor-based pagination.

The backend exposes a cursor-paginated API (`GET /api/skills/list`).

The Skills List preserves:

- Search
- Category filter
- Sorting
- Scroll position

when opening Skill Details.

---

# Infinite Loading

Loading sequence

```text
Open Skills

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

| Column     | Description                                        |
| ---------- | -------------------------------------------------- |
| Name       | Skill name + origin badge (AI/Manual) + alias count badge |
| Category   | Canonical category badge                           |
| Level      | Skill proficiency level (Lv.1 … Lv.10)             |
| Roles      | Relevant roles                                     |
| Demand     | Market demand percentage                           |
| Confidence | AI confidence percentage                           |
| Created    | Relative creation time                             |
| Mentions   | Total job/company mentions referencing this skill (sortable) |
| Actions    | Row actions (Details, Edit, Delete)                |

---

# Column Details

## Name

Displays the skill name and, when aliases exist, an alias count badge. An origin
badge indicates where the skill came from:

| Badge   | `source_type`      | Meaning             |
| ------- | ------------------ | ------------------- |
| AI      | `ai_generated`     | Created by processing (job/company analysis) |
| Manual  | `user_input`       | Created by the user |

```text
Kubernetes  [AI]  2 aliases
```

---

## Category

Displays one of the canonical category badges:

| Category     | Color   |
| ------------ | ------- |
| technical    | Blue    |
| engineering  | Green   |
| professional | Purple  |
| domain       | Orange  |
| career       | Cyan    |

---

## Level

Displays the proficiency level.

```text
Lv.4
```

---

## Demand

Displays `market_relevance` as a percentage. Color thresholds:

| Value | Color   |
| ----- | ------- |
| ≥ 80  | Green   |
| ≥ 50  | Yellow  |
| < 50  | Orange  |
| null  | —       |

---

## Confidence

Displays the AI confidence as a percentage using the same thresholds.

---

## Mentions

Displays the total number of job/company analysis mentions that reference this
skill. A nonzero count is highlighted; zero renders muted. The column is
sortable (see Sorting below).

---

# Row Actions

Each row provides three icon actions (tooltip buttons):

| Action  | Description                        |
| ------- | ---------------------------------- |
| Details | Opens Skill Details drawer.        |
| Edit    | Opens Skill Edit drawer.           |
| Delete  | Deletes the skill (with confirm).  |

All row actions stop propagation so clicking an action never opens the detail
drawer.

---

# Skill Detail Drawer

Selecting a row opens the Skill Detail drawer (Sheet from the right) with three
tabs:

- **Details** — level, confidence, market demand, roles, path, tags, aliases,
  evidence, and a "Generate Roadmap" action.
- **Roadmap** — Generate / Extend / Finegrain actions plus the rendered roadmap
  tree (from `GET /api/skill-roadmaps?skill=<name>`).
- **History** — generation history via the shared `useLocalHistory` hook.

The header has an **Edit** button; the footer has a **Delete** button.

---

# Skill Edit Drawer

The Edit drawer (Sheet) edits:

- Name (required)
- Level (1–10 select)
- Category (canonical select)
- Relevant Roles
- Tags (comma-separated)
- **Aliases** — add/remove alternate names via `POST`/`DELETE
  /api/skills/{id}/aliases`
- **Merge** — "Merge into another skill" opens the Merge Skill dialog
  (`POST /api/skills/merge`)

Saving calls `PUT /api/skills/{id}` and invalidates the list query.

---

# Merge Skill Dialog

The Merge dialog searches visible skills (excluding the current skill), lets the
user pick a target, and merges the current skill into it. Mentions, roadmaps,
and progress re-point to the target; the source skill becomes a hidden alias.
The dialog mirrors the Companies "Relate Company" UX.

---

# Add Skill Drawer

The Add Skill drawer (Sheet) collects:

- Name (required)
- Level (1–10 select)
- Category (canonical select)
- Relevant Roles
- Path

Submitting calls `POST /api/skills` with `{name, level, roles, path, category}`.
After a successful submit the drawer closes and the skill appears in the list.

---

# Sorting

Supported sort fields (backend, NULLS LAST):

- `created_at` (default, desc)
- `name`
- `level`
- `confidence`
- `market_relevance`
- `mention_count`

Sorting is always performed by the backend. Rows where the sort column is empty
sort last in both directions.

---

# Empty States

## No Skills

```text
No skills yet. Add one or run an AI analysis.
```

---

# Loading States

## Initial Loading

- Skeleton rows

## Infinite Loading

```text
Loading more skills...
```

Existing rows remain interactive.

---

# Error States

## Backend Error

```text
Unable to load skills.

Retry
```

---

# Performance Requirements

The page must support

- Large skill inventories
- Virtual scrolling
- Infinite loading
- Stable scroll position

The frontend never renders all rows simultaneously; only visible rows are
mounted.

---

# Related Documents

- `docs/api/skills/list-skills.md`
- `docs/ux/features/skills/skill-row.md`
- `docs/ux/features/skills/skill-detail.md`
- `docs/ux/features/skills/add-skill.md`
- `docs/ux/features/skills/edit-skill.md`
- `docs/ux/flows/skills/browse-skills.md`
- `docs/ux/features/companies/page.md` (reference: shared virtualized-table UX)
