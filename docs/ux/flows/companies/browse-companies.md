# Browse Companies

## Purpose

How a user discovers, filters, and opens companies in the Companies workspace.

---

# Flow

```text
Open Companies page
        │
        ▼
Load first page (GET /api/companies/list, page_size=25)
        │
        ▼
┌─────────────────────────┐
│  Browse / Manage        │
│                         │
│  Search / Filter / Sort │
│  Scroll (infinite)      │
│  Open row → Detail      │
└────────────┬────────────┘
             │
             ▼
   ┌──────────────────┐   ┌──────────────────┐
   │  Detail Drawer   │   │  Queue Drawer    │
   │  (Sheet)         │   │  (Sheet, poll)   │
   │  Edit / Reprocess│   │  Process / Delete│
   │  Delete / Jobs   │   └──────────────────┘
   └──────────────────┘
```

---

# Steps

## 1. Open the Companies page

The page mounts, calls `GET /api/companies/list` for the first page, and
renders the virtualized table.

## 2. Search

Typing in the search box (debounced 300ms) refetches the list with the `query`
parameter. Supported fields: name, industry, city, country, description.

## 3. Filter by industry

Selecting an industry in the toolbar refetches the list with the `industry`
parameter.

## 4. Sort

Clicking a sortable header (Name, Updated) or the Scores popover (Overall /
Fit / Success) refetches with the chosen `sort` and `order`.

## 5. Scroll

Reaching the sentinel fetches the next page with the cursor. Rows append until
`has_more` is false.

## 6. Open company details

Clicking a row opens the Company Detail drawer. The `?company=` URL parameter
is set, so the drawer survives a reload (deep-link).

## 7. Manage

From the drawer or row actions the user can edit, reprocess, or delete the
company. Deletion requires confirmation.

---

# Edge Cases

## Deep link

Opening `/companies?company=42` opens the detail drawer for company 42 on mount.

## Deleting the open company

The detail and edit drawers close; the `?company=` parameter is cleared.

## No results

An empty list shows the "No companies have been processed yet." empty state.

## Search with no matches

Rows disappear and the empty state shows; the Clear button in the toolbar
restores the full list.

---

# Related Documents

- `docs/ux/features/companies/page.md`
- `docs/api/companies/list-companies.md`
