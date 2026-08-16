# Reprocess Company API

## Purpose

Queues a company for reprocessing through the shared `COMPANY_PROCESSING`
`ProcessingExecution` lifecycle.

This replaces the legacy `POST /api/pending-companies/{id}/process` flow: the
company's `status` is set to `queued`, a new `ProcessingExecution` is created and
dispatched, and the resulting execution id is returned so the frontend can open
the Processing Drawer.

---

# Endpoint

POST /api/companies/{id}/reprocess

`{id}` is a **UUID v7 string**.

---

# Response

```json
{
  "status": "queued",
  "execution_id": "exec-123"
}
```

When the company does not exist the endpoint returns `200` with:

```json
{
  "error": "Not found"
}
```

and no execution is created.

---

# Corrective re-detection

A reprocess re-collects the company's research context (website + links +
notes) and re-persists the queryable fields, including `company_type`. The type
is always stored as one of the fixed vocabulary
(`normalize_company_type`; see `docs/domain/companies/company_type.md`), so a
reprocess with more links/notes can correct an inaccurate type (e.g.
`RECRUITING_AGENCY` detected as `STAFFING_COMPANY`), and anything unrecognized
is stored as `UNKNOWN`.

---

# Errors

500

Internal server error.

---

# Related Documents

- docs/api/companies/add-company.md
- docs/api/companies/company-detail.md
- docs/ux/features/companies/company-row.md
- docs/domain/processing/processing-execution.md
