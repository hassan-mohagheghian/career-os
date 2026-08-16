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
| Type      | Company type badge (Product / Recruiting Agency / Staffing / Consulting / Unknown) |
| Location  | City, Country                             |
| Size      | Company size band                         |
| Jobs      | Number of linked, non-deleted jobs        |
| Scores    | Grade badge + Overall / Success / Fit score values |
| Status    | Processing status from the latest processing execution |
| Updated   | Relative update time                      |
| Created   | Relative creation time                    |

There is no `Actions` column — row actions (Details, Reprocess, Edit, Delete)
are revealed on hover (see `# Actions` below).

The **Jobs** column value depends on company type. A **recruiter company**
(company type `RECRUITING_AGENCY` / `STAFFING_COMPANY` **or** a positive
`recruiter_job_count`) shows its `recruiter_job_count` labeled
"listed for clients"; all other companies show `job_count`. The tooltip
reflects the label (`N jobs listed for clients` for recruiters).

---

# Company Type Column

A compact badge showing the company type without the trailing word "Company"
(via the shared `formatCompanyTypeShort` helper, `entities/company/lib.ts`):

| Type               | Badge label        |
| ------------------ | ------------------ |
| `PRODUCT_COMPANY`  | Product            |
| `RECRUITING_AGENCY`| Recruiting Agency  |
| `STAFFING_COMPANY` | Staffing           |
| `CONSULTING_COMPANY`| Consulting         |
| `UNKNOWN` / null   | Unknown            |

The type is always one of the fixed vocabulary above (`normalize_company_type`),
so the badge never shows a free-text string.

---

# Company Type Row Colors

Rows are tinted by company type so the list is scannable at a glance. The
tint uses the shared `companyTypeRowClasses` helper
(`entities/company/lib.ts`) and applies a light background that intensifies on
hover / focus (`/5` → `/10`).

| Type                | Row tint                 |
| ------------------- | ------------------------ |
| `PRODUCT_COMPANY`   | **white** (no tint)      |
| `RECRUITING_AGENCY` | purple (`bg-purple-500`) |
| `STAFFING_COMPANY`  | orange (`bg-orange-500`) |
| `CONSULTING_COMPANY`| teal (`bg-teal-500`)     |
| `UNKNOWN`           | muted (`bg-muted`)       |

Product companies intentionally receive **no tint** (white) so they read as
the neutral default. Every other type has its **own unique color**.

When no type is set (`null`), the row falls back to the recruiter purple tint
if `isRecruiterCompany` is true (`recruiter_job_count > 0`), preserving the
previous recruiter-at-a-glance behavior. Rows also carry a
`data-recruiter="true"/"false"` attribute. Detection uses the shared
`isRecruiterCompany` helper:

```text
recruiter = company_type in {RECRUITING_AGENCY, STAFFING_COMPANY}
            OR recruiter_job_count > 0
```

```text
+--------------------------------------------------------------------------------+
|  [logo] Acme Staffing            | Recruiting Agency | Berlin, DE | 50-200 | 12 listed |
|  [purple tint spans the whole row]                               F 82 S 90 O 87 |
+--------------------------------------------------------------------------------+
```

---

# Scores

```text
[A+]  F 85   S 90   O 88
```

The Overall / Success / Fit values and the grade badge are exactly the scores
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

There is no fixed Actions column. Hovering a row reveals a floating toolbar of
icon buttons at the row's right edge (using a `group`/`group-hover` pattern,
overlaid on the row). All actions stop propagation:

- Details — opens the detail drawer
- Reprocess — re-enqueues for processing
- Edit — opens the edit drawer
- Delete — deletes with confirmation

---

# Related Documents

- `docs/ux/features/companies/page.md`
