# Company Detail

## Purpose

The Company Detail drawer shows a company's intelligence, scores, notes, and
linked jobs. It is the successor to the legacy `CompanyDrawer`, migrated from
the legacy `AppDrawer` to the shared `Sheet` and driven by react-query.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ Company Details                              │
├──────────────────────────────────────────────┤
│                                              │
│ [A+]  Fit 85  Success 90  Overall 88         │
│ ◉ Acme GmbH                                  │
│ Software Development                         │
│ 📍 Berlin, Germany  👥 51-200  Product Co.   │
│ 💼 12 jobs                                   │
│                                              │
│              [View All Jobs]                 │
│              [Website]                       │
│              [Reprocess]                     │
│              [Delete]                        │
│                                              │
│ [Original Notes] [Intelligence] [Scores] [Jobs (12)] │
│                                              │
│ <tab content>                                │
│                                              │
└──────────────────────────────────────────────┘
```

---

# Header

- Overall grade badge
- Fit / Success / Overall score cards
- Company name + logo
- Industry
- Badges: location, company size, company type, linked-job count
- Actions: View All Jobs, Website, Reprocess, Delete

---

# Tabs

## Original Notes

`CompanyNotesTab` — notes and links CRUD against the legacy company endpoints
(`/api/companies/{id}/notes`, `/api/companies/{id}/links`). Notes and links
are read from the detail payload (`company.notes`, `company.links`), no
separate initial fetch.

## Intelligence

Company intelligence sections from the detail payload (`company.intelligence`).
Renders the **product-company** variant for normal companies and the
**recruiter** variant for `RECRUITING_AGENCY` / `STAFFING_COMPANY` types.

Sections:

- Company Overview
- Engineering Culture
- Technology Stack
- Work Environment
- Visa & Relocation Signals
- Growth Opportunities

## Scores

Full score breakdown:

- Overall grade card
- Fit score (with positive / negative factors)
- Success score (with positive / negative factors)
- Score calculation (Overall = Fit × 0.5 + Success × 0.5)

## Jobs

`CompanyJobsTab` — lists `company.jobs` from the detail payload. Clicking a job
or "View All Jobs" navigates to the Jobs page.

---

# Data Source

The drawer loads the company once via `useCompanyQuery(id)`, which calls
`GET /api/companies/list/{id}` and returns all company data (base fields,
status, notes, links, intelligence, scores, jobs) in a single payload. Each tab
reads from that payload; no `/links`, `/jobs` or local-history requests are
made by the drawer.

---

# Related Documents

- `docs/ux/features/companies/page.md`
- `docs/ux/features/companies/company-row.md`
- `docs/ux/features/companies/edit-company.md`
