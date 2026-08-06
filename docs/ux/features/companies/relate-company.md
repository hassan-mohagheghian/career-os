# Related Companies

## Purpose

Companies extracted from jobs can end up as near-duplicates under slightly
different names (legal suffixes, typos, local subsidiaries). The Related
Companies feature gives each company a **main** company it belongs to. An
alias company is related to a main; jobs linked to the alias (and its own
aliases) are re-pointed to the main, so intelligence and score data are
consolidated on a single reference record.

Users manage relations from the Company Detail drawer via a searchable
dialog. This feature is the manual complement to the automatic
company auto-creation/linking during job processing.

---

# Relation Rules

- A company with a `parent_company_id` is an **alias**; it may not be chosen
  as anyone else's main.
- Relating a company to a main re-points all non-deleted jobs of that company
  and of every descendant alias onto the main.
- Removing a relation clears `parent_company_id`; previously re-pointed jobs
  are **not** moved back (they stay on the main).
- A company cannot relate to itself, and cycles are rejected (409).

---

# Related Companies Section (Company Detail drawer)

Sits below the header badges and above the Recommendation section.

```text
┌────────────────────────────────────────────────────────┐
│ ◈ Related Companies                          [ Manage ]│
│ Acme Inc  →  Part of Acme GmbH                         │
└────────────────────────────────────────────────────────┘
```

| State                    | Rendered text                                        |
| ------------------------ | ---------------------------------------------------- |
| Company is an alias      | `Part of <main name>` (main name emphasized)          |
| Company is a main with N aliases | `N related companies`                        |
| No relation              | `No related companies`                               |

The `Manage` button opens the Relate Company dialog.

---

# Relate Company Dialog

Opened via `Manage` in the Company Detail drawer.

```text
┌──────────────────────────────────────────────┐
│ Related Companies                       Close │
├──────────────────────────────────────────────┤
│ Relate <current company> to a main company.  │
│ Jobs linked to an alias are re-pointed to    │
│ the main company.                            │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ [alias of] Acme GmbH             [Remove]│ │   ← only when already an alias
│ └──────────────────────────────────────────┘ │
│ Search companies...                          │
│ ┌──────────────────────────────────────────┐ │
│ │ ◉ Acme GmbH                     2 alias  │ │
│ │ ◉ Beta GmbH                              │ │
│ │ ◉ Nova SE                                │ │
│ └──────────────────────────────────────────┘ │
│                              [Cancel] [Set as Main] │
└──────────────────────────────────────────────┘
```

## Behavior

- **Search**: filters candidates by name (server-side, `page_size 20`,
  name-ascending). Only non-alias, non-self companies are selectable.
- **Select**: clicking a candidate highlights it (primary tint); selecting a
  different candidate moves the highlight.
- **Set as Main**: disabled until a candidate is selected. Submits
  `PUT /api/companies/{id}/main` with the chosen main; success shows a
  success toast and closes the dialog; the drawer and list refresh.
- **Remove** (alias only): submits the same endpoint with `main_company_id:
  null`; success toast "Company relation removed".
- **Errors** (409/404 from the API) surface via an error toast; the dialog
  stays open.
- **Loading**: candidate list shows a spinner; mutation shows a pending state
  on the submit button.

---

# Alias Badge (Company Row)

Alias companies render a small `alias` badge next to their name in the list:

```text
│ ◉ Acme Inc [alias] │  Industry │ ... │ Actions │
```

The badge is purely informational; selecting the row still opens the detail
drawer where the relation can be changed.

---

# Job Detail Drawer — Linked Company Chip

When a job has a `company_id`, the company name in the job detail header is a
primary-colored link instead of plain muted text:

```text
Backend Engineer
Acme GmbH                    ← primary link
```

Clicking it deep-links to the Companies page and opens that company's detail
drawer (`/companies?company=<id>`).
