# Company Queue

## Purpose

The Company Queue drawer monitors the **legacy** company processing pipeline
(`pending_companies` rows driven by the LangGraph company graph).

It is a monitoring tool, not a replacement for the Company List.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ Company Queue (7)                            │
├──────────────────────────────────────────────┤
│                                              │
│ ⏱ Created (1)                                │
│   ┌──────────────────────────┐  [▶] [🗑]     │
│   │ Acme GmbH                │               │
│   │ created                  │               │
│   │  • link1.example.com     │               │
│   └──────────────────────────┘               │
│                                              │
│ ◔ Pending (2)                                │
│   (Process + Delete)                         │
│                                              │
│ ≡ Queued (1)                                 │
│   (Delete)                                   │
│                                              │
│ ⚙ Processing (2)                             │
│   (Delete)                                   │
│                                              │
│ ✕ Failed / Cancelled (1)                     │
│   (Process + Delete)                         │
│                                              │
└──────────────────────────────────────────────┘
```

---

# Sections

| Section            | Statuses            | Actions            |
| ------------------ | ------------------- | ------------------ |
| Created            | created             | Process, Delete    |
| Pending            | pending             | Process, Delete    |
| Queued             | queued              | Delete             |
| Processing         | processing, running | Delete             |
| Failed / Cancelled | failed, cancelled   | Process, Delete    |

Each section is collapsed when empty, showing "No companies in this state."

---

# Item

Each item shows:

- Input text or the first parsed note (title)
- Current node or status
- Error (red) when present
- Up to four parsed notes/links (URLs render as links), with a `+N more` hint

---

# Data Source

The drawer polls `GET /api/pending-companies` every 5 seconds via a react-query
query (`usePendingCompaniesQuery`).

This is **polling**, not SSE — the company pipeline does not publish
Processing-Execution events.

---

# Actions

| Action  | Endpoint                                      |
| ------- | --------------------------------------------- |
| Process | `POST /api/pending-companies/{id}/process`    |
| Delete  | `DELETE /api/pending-companies/{id}`          |

Both actions invalidate the pending-companies query so the sections refresh.

---

# Relationship to the List

The Queue button badge in the Companies header shows the total number of
pending companies. Opening the drawer does not block browsing.

---

# Related Documents

- `docs/ux/features/companies/page.md`
- `docs/ux/features/companies/add-company.md`
- `docs/ux/flows/companies/browse-companies.md`
