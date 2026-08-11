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

The **Jobs** column value depends on company type. A **recruiter company**
(company type `RECRUITING_AGENCY` / `STAFFING_COMPANY` **or** a positive
`recruiter_job_count`) shows its `recruiter_job_count` labeled
"listed for clients"; all other companies show `job_count`. The tooltip
reflects the label (`N jobs listed for clients` for recruiters).

---

# Recruiter Tint

Recruiter rows get a light purple background tint
(`bg-purple-500/5`, stronger on hover / focus) and a
`data-recruiter="true"` attribute so they are visually distinguishable from
product companies at a glance. Detection uses the shared `isRecruiterCompany`
helper (`entities/company/lib.ts`):

```text
recruiter = company_type in {RECRUITING_AGENCY, STAFFING_COMPANY}
            OR recruiter_job_count > 0
```

```text
+------------------------------------------------------------------------------+
|  [logo] Acme Staffing            | Recruiting Agency | Berlin, DE | 50-200 | 12 listed |
|  [purple tint spans the whole row]                               F 82 S 90 O 87 |
+------------------------------------------------------------------------------+
```

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

Rendered with the shared `StatusBadge` (the exact badge the Jobs list uses)
from the company's latest processing execution. The status vocabulary matches
the job execution statuses:

```text
Created
Queued
Starting
Running
Completed
Failed
Cancelled
```

Running renders a pulsing dot. A company with no processing execution renders
`—`.

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
