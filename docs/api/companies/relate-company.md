# Relate Company to Main API

## Purpose

Sets or removes the **main** company for a company. A company related to a
main is an **alias**; jobs linked to it (and to its own aliases) are re-pointed
onto the main, consolidating scores and intelligence on a single reference
record.

This is the manual counterpart to the automatic company linking that runs
during job processing (the job analysis `link_company` step).

---

# Endpoint

PUT /api/companies/{id}/main

The route is registered on the companies v2 router. `{id}` is a **UUID v7
string**.

Request body:

```json
{
  "main_company_id": "019fd121-eac7-7537-aa3a-ddded8bb0cc8"
}
```

- `main_company_id` is nullable. `null` removes the relation (the company
  stops being an alias; already re-pointed jobs are not moved back).

---

# Response

200

Returns the updated company detail (same shape as `GET /api/companies/{id}`),
with `is_alias` / `parent_company_id` / `main_company` reflecting the new
state.

---

# Validation

| Condition                                  | Result |
| ------------------------------------------ | ------ |
| Relating a company to itself               | 409    |
| Main company does not exist                | 404    |
| Main company is itself an alias            | 409    |
| Relating would create a cycle              | 409    |
| Company id does not exist                  | 404    |

---

# Side Effects

When a relation is set, all non-deleted jobs whose `company_id` belongs to the
alias or any descendant alias are re-pointed to the main company
(`job.jobs.company_id = main`).

---

# Related Documents

- docs/api/companies/company-detail.md
- docs/api/companies/list-companies.md
- docs/ux/features/companies/relate-company.md
