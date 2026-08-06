# Company Row

## Purpose

A single row in the virtualized Company List. Provides a compact overview of a
company's identity, AI evaluation, processing state, and available actions.

Rows are never expandable. Selecting a row opens the Company Detail drawer.

---

# Row Columns

| Column    | Description                               |
| --------- | ----------------------------------------- |
| Name      | Company logo, name, and `alias` badge when the company is related to a main |
| Industry  | Industry classification                   |
| Location  | City, Country                             |
| Size      | Company size band                         |
| Jobs      | Number of linked, non-deleted jobs        |
| Scores    | Grade badge + Fit / Success / Overall score values |
| Status    | Processing status from the latest processing execution |
| Updated   | Relative update time                      |
| Created   | Relative creation time                    |
| Actions   | Details, Reprocess, Edit, Delete          |

---

# Scores

```text
[A+]  F 85   S 90   O 88
```

The Fit / Success / Overall values and the grade badge are exactly the scores
**calculated by company processing** (fit / success → weighted overall, stored
in `company.intelligence.scores` and surfaced as the normalized `scores` field
by `GET /api/companies/list`). The row prefers the processing-computed
`scores.overall_grade` and only falls back to deriving the grade from the
overall score via the shared grade helper (`A++` ≥ 90, `A+` ≥ 80, `A` ≥ 70,
`B` ≥ 50, `C` ≥ 30, `D` ≥ 0). Null scores render `—` and no grade renders `—`.
Color matches the shared grade tokens (A++/A+ green, A lime, B blue, C orange,
D red).

---

# Status

Rendered from the company's `latest_processing_execution` using the shared
`JobStatus` vocabulary:

```text
Queued
Processing
Completed
Failed
Cancelled
```

Processing renders a pulsing dot.

---

# Actions

Icon buttons with tooltips. All actions stop propagation:

- Details — opens the detail drawer
- Reprocess — re-enqueues for processing
- Edit — opens the edit drawer
- Delete — deletes with confirmation

---

# Related Documents

- `docs/ux/features/companies/page.md`
