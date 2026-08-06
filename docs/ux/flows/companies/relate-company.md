# Relate a Company to a Main

## Purpose

How a user consolidates near-duplicate companies by relating an alias to a
main company, and how they later remove or change that relation. Relating
re-points the alias's jobs onto the main so scoring and intelligence live on
one reference record.

---

# Flow

```text
Open Companies page
        │
        ▼
Find duplicate company (search / sort)
        │
        ▼
Open Company Detail drawer (row click / deep link)
        │
        ▼
Click [ Manage ] in the Related Companies section
        │
        ▼
┌──────────────────────────────────────────────┐
│  Relate Company Dialog                       │
│  • search candidate main companies           │
│  • select a candidate (highlight)            │
│  • Set as Main                               │
│  • (alias only) Remove relation              │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
PUT /api/companies/{id}/main  { main_company_id }
                   │
                   ├─ 200 → success toast; drawer + list refresh
                   │        alias jobs re-pointed to main
                   └─ 409/404 → error toast; dialog stays open
```

---

# Steps

## 1. Find the duplicate

The Companies list shows an `alias` badge next to companies already related to
a main. Search by name to locate a suspected duplicate that has no relation
yet.

## 2. Open details

Clicking a row (or arriving via a job's company link) opens the Company Detail
drawer. The Related Companies section shows the current state: "Part of …",
"N related companies", or "No related companies".

## 3. Manage relations

`Manage` opens the Relate Company dialog.

- **Set as Main**: search and select a non-alias candidate, then `Set as Main`.
  Confirmation closes the dialog with a success toast. All non-deleted jobs of
  the alias (and of its own aliases) are re-pointed to the main.
- **Remove** (alias only): instantly clears the relation; the alias's already
  re-pointed jobs stay on the main.

## 4. Verify

The list refresh shows the alias badge on the related company; opening the
main shows "N related companies". Jobs previously linked to the alias now point
to the main (visible from the job detail drawer's company link).

---

# Edge Cases

| Case | Behavior |
| ---- | -------- |
| Relating a company to itself | Rejected by the API (409), error toast |
| Main is itself an alias | Not selectable in the dialog; rejected (409) if attempted |
| Cycle (b → a where a → b) | Rejected by the API (409) |
| Company / main missing | 404 error toast |
| Removing a relation | Jobs stay on the main (not moved back) |

---

# Related Documents

- `docs/ux/features/companies/relate-company.md`
- `docs/ux/features/companies/company-detail.md`
- `docs/ux/features/companies/company-row.md`
- `docs/ux/flows/companies/browse-companies.md`
