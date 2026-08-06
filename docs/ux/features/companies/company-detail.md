# Company Detail

## Purpose

The Company Detail drawer shows a company's intelligence, scores, notes, and
linked jobs in a single scrollable page — the same pattern as the Job Detail
drawer. It is the successor to the legacy `CompanyDrawer`, migrated from the
legacy `AppDrawer` to the shared `Sheet` and driven by react-query. There are
no tabs; company-exclusive sections are ordered by importance for a
visa-seeking software engineer.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ Company Details                              │
├──────────────────────────────────────────────┤
│ [A+]  Fit 85  Success 90  Overall 88         │
│ ◉ Acme GmbH                                  │
│ Software Development                         │
│ 📍 Berlin, Germany  👥 51-200  Product Co.   │
│ 💼 12 jobs                                   │
│ ◈ Related Companies                 [Manage] │
│                                              │
│ <Recommendation>                             │
│ <Company Overview / description>             │
│ <Intelligence sections, importance order>    │
│ <Scores breakdown>                           │
│ <Linked jobs>                                │
│ <Notes — read only>                          │
│ <Links — read only>                          │
│                                              │
│ [View All Jobs]  [Website]  ... [Reprocess]  │
│                               [Delete]       │
└──────────────────────────────────────────────┘
```

---

# Header

- Overall grade badge (derived from the overall score, A++ … D)
- Fit / Success / Overall score cards
- Company name + logo
- Industry
- Badges: location, company size, company type, linked-job count

The header mirrors the Job Detail drawer's first section: no action buttons in
the header. Actions are grouped in a footer at the bottom of the page.

---

# Page Sections (single page, no tabs)

## Related Companies

Sits between the header badges and the Recommendation section. Shows the
main/alias relationship (see `relate-company.md`):

- Alias: `Part of <main name>`
- Main with aliases: `N related companies`
- Otherwise: `No related companies`

A `Manage` button opens the Relate Company dialog.

## Recommendation

`company.intelligence.recommendation`, prioritized to the top of the drawer.
Rendered as a highlighted card: priority badge, observation, action, evidence,
impact, ideal role, timing.

## Company Overview

`company.description` plus the intelligence "Company Overview" section
(products, founded, headquarters, size, countries, market position, funding,
growth trajectory).

## Intelligence

Rendered from the detail payload (`company.intelligence`). The **product-company**
variant orders sections by importance for the user's visa-sponsorship goal:

1. Company Overview
2. Visa & Relocation Signals
3. Work Environment
4. Engineering Culture
5. Technology Stack
6. Growth Opportunities

The **recruiter** variant (for `RECRUITING_AGENCY` / `STAFFING_COMPANY`)
keeps its own ordering:

1. Recruiter Overview
2. International Hiring
3. Work Environment

## Scores

Full score breakdown:

- Overall grade card (derived from the overall score via the shared grade helper)
- Fit score (with positive / negative factors)
- Success score (with positive / negative factors)
- Score calculation (Overall = Fit × 0.5 + Success × 0.5)

## Linked Jobs

`CompanyJobsTab` — lists `company.jobs` from the detail payload. Clicking a job
or "View All Jobs" navigates to the Jobs page.

## Notes (read only)

Read-only list of `company.notes` from the detail payload. Notes are added and
edited in the **Edit Company** drawer, not here.

## Links (read only)

Read-only list of `company.links` from the detail payload. Links are added and
edited in the **Edit Company** drawer, not here.

## Footer Actions

A footer row at the bottom of the page groups the actions that used to live in
the drawer header:

- View All Jobs (navigates to the Jobs page) — only when the company has jobs
- Website (opens `company.website` in a new tab) — only when a website exists
- Reprocess (re-enqueues the company for processing)
- Delete (deletes with confirmation)

---

# Data Source

The drawer loads the company once via `useCompanyQuery(id)`, which calls
`GET /api/companies/list/{id}` and returns all company data (base fields,
status, notes, links, intelligence, scores, jobs) in a single payload. Each
section reads from that payload; no `/links`, `/jobs` or local-history
requests are made by the drawer.

---

# Related Documents

- `docs/ux/features/companies/page.md`
- `docs/ux/features/companies/company-row.md`
- `docs/ux/features/companies/edit-company.md`
