# Edit Company

## Purpose

The Company Edit drawer edits a company's core profile data and its notes and
links. Notes and links CRUD
moved here from the Company Detail drawer so the detail drawer can stay
read-only.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ ✏️ Edit Company                              │
├──────────────────────────────────────────────┤
│                                              │
│ Name *        [ Acme GmbH              ]     │
│ Industry      [ Software Development   ]     │
│ City          [ Berlin                 ]     │
│ Country       [ Germany                ]     │
│ Website       [ https://acme.example   ]     │
│ Company Size  [ 51-200                 ]     │
│ Company Type  [ Product Company        ]     │
│ Description   [ ...................... ]     │
│               [ ...................... ]     │
│                                              │
│ ── Company Notes ──────────────────────────  │
│ [ add a note ...                   ] [Add]   │
│ • Test note                    ✏️ 🗑          │
│ • Research note                 ✏️ 🗑          │
│                                              │
│ ── Company Links ──────────────────────────  │
│ [+ Add Link]                                 │
│ 🔗 https://example.com        ↩ ✏️ 🗑          │
│                                              │
│                [ Save ]                      │
│                                              │
└──────────────────────────────────────────────┘
```

---

# Fields

| Field        | Required | Notes                          |
| ------------ | -------- | ------------------------------ |
| Name         | Yes      |                                |
| Industry     | No       |                                |
| City         | No       |                                |
| Country      | No       |                                |
| Website      | No       |                                |
| Company Size | No       | Select of size bands           |
| Company Type | No       | Select of the fixed vocabulary (`Product`, `Recruiting Agency`, `Staffing`, `Consulting`, `Unknown`) + `Not set` |
| Description  | No       | Multiline                      |

### Company Type select

- Only offers the **fixed vocabulary** values (`PRODUCT_COMPANY`,
  `RECRUITING_AGENCY`, `STAFFING_COMPANY`, `CONSULTING_COMPANY`, `UNKNOWN`) plus
  `Not set` (clears the field). Selecting `Not set` saves `company_type: null`.
- The backend (`normalize_company_type`) enforces the same vocabulary on `PUT
  /api/companies/{id}` and on every processing persist, so any value outside the
  fixed set is coerced to `UNKNOWN`. This is the manual fallback when processing
  mis-classifies a company (e.g. detected `Recruiting Agency` but it is actually
  `Staffing`).

---

# Notes & Links

- `CompanyNotesTab` renders below the profile fields with full CRUD for notes
  (`/api/companies/{id}/notes`) and links (`/api/companies/{id}/links`).
- Notes and links are saved immediately on add/update/delete (not on the
  drawer's Save button); the Save button persists the profile fields via
  `PUT /api/companies/{id}`.

---

# Behavior

- Save calls `PUT /api/companies/{id}`.
- On success: toast shown, edit drawer closes, list query
  (`companies-v2-infinite`) and detail query (`company-detail`) are invalidated
  so the table and open detail drawer refresh.
- Validation errors from the API are surfaced inline.

---

# Related Documents

- `docs/ux/features/companies/page.md`
- `docs/ux/features/companies/company-detail.md`
- `docs/api/companies/list-companies.md`
