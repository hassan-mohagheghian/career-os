# Edit Company

## Purpose

The Company Edit drawer edits a company's core profile data. It is the Sheet
successor to the legacy edit flow.

---

# Drawer Layout

```text
┌──────────────────────────────────────────────┐
│ Edit Company                                 │
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
| Company Type | No       | Select (Product/Recruiting/...) |
| Description  | No       | Multiline                      |

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
