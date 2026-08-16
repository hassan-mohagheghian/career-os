# Prompt 169 - Company Type Fixed Vocabulary + Edit Select

## Objective

Guarantee a company's `company_type` is **always one of the fixed vocabulary**
(`PRODUCT_COMPANY`, `RECRUITING_AGENCY`, `STAFFING_COMPANY`, `CONSULTING_COMPANY`,
`UNKNOWN`); any other/inaccurate value is coerced to `UNKNOWN`. This makes
reprocessing corrective: when job processing mis-classifies a company (e.g.
detects `RECRUITING_AGENCY` but it is actually `STAFFING_COMPANY`), a company
reprocess with more links/resources re-detects and persists a **fixed** type.
Also make `company_type` editable via a constrained **Select** in the edit
drawer (fallback when detection is wrong), instead of free text.

## Current State

- `company_service.persist_analysis` (`company_service.py:103`) writes
  `extraction.get("company_type", "")` raw. The LLM extraction is already
  normalized by processing's `CompanyExtraction.validate_company_type`
  (`company_analysis_validation.py:115`), but the storage layer does not itself
  enforce the vocabulary, and a missing type persists as `""` (not `None`).
- `companies_v2_router.update_company` (`companies_v2_router.py:581`) writes
  `CompanyUpdateRequest.company_type` raw with **no validation** — any string is
  stored. Schema at `schemas/companies_v2.py:242`.
- `CompanyEditDrawer.tsx:201-207` renders Company Type as a free-text `Input`
  (placeholder `PRODUCT_COMPANY`), but `docs/ux/features/companies/edit-company.md:55`
  already specifies it should be a **Select** (Product/Recruiting/...).
- Canonical vocabulary duplicated across contexts:
  `company_analysis_validation.py:16`, `company_analysis_scoring.py:54`,
  `company_analysis_inputs.py:10`. Frontend labels in
  `entities/company/lib.ts:15` (`COMPANY_TYPE_LABELS`).
- Radix `Select` UI exists at `shared/ui/select.tsx`; used in
  `ApplicationTracker.tsx:64`.

## Changes

### Backend — canonical vocabulary (`companies/domain/company_type.py` new)

- `VALID_COMPANY_TYPES: tuple[str, ...]` = the 5 fixed types (companies owns the
  storage vocabulary).
- `normalize_company_type(v: str | None) -> str | None`: empty/whitespace/None →
  `None`; strip+upper; return value if in `VALID_COMPANY_TYPES`, else `UNKNOWN`.

### Backend — enforce at the storage layer

- `company_service.persist_analysis`: write `normalize_company_type(
extraction.get("company_type"))` so reprocess always stores a fixed type or
  `None` (never a stray string / `""`).
- `companies_v2_router.update_company`: when `company_type` is in the payload,
  normalize it (`None` clears the column, invalid → `UNKNOWN`).

### Frontend — edit drawer select (`CompanyEditDrawer.tsx`)

- Replace the free-text Company Type `Input` with a Radix `Select` offering the
  5 fixed types (labelled via `COMPANY_TYPE_LABELS`) plus a `Not set` (empty)
  option. On save, send the selected value or `null`.

### Frontend — list type label (`lib.ts` + `CompanyRow.tsx`)

- Add `formatCompanyTypeShort` (drops a trailing " Company" word) and use it in
  the company list type column so it shows `Product` / `Recruiting Agency` /
  `Staffing` / `Consulting` / `Unknown` — never `Product Company`, etc.

### Docs

- `docs/api/API.md`: document that `PUT /api/companies/{id}` and processing both
  store `company_type` as one of the fixed vocabulary (invalid → `UNKNOWN`,
  empty → cleared/None).
- `docs/ux/features/companies/edit-company.md`: note the Company Type select
  only offers the fixed types + `Not set`, and that reprocess re-detects it.
- `docs/domain/companies/` (create if missing): record the `company_type`
  vocabulary.

## Testing

- Backend (TDD): `normalize_company_type` (valid uppercase pass-through, lowercase
  uppercased, invalid → `UNKNOWN`, empty/None → `None`); `persist_analysis`
  stores a fixed type / `None` for invalid & missing; `PUT /api/companies/{id}`
  normalizes invalid → `UNKNOWN`, valid stays, empty → `null`.
- Frontend: `CompanyEditDrawer.test.tsx` — select renders the 5 fixed options
  (+ Not set), reflects the company's current type, and submits the chosen type
  on save.

## Constraints

- Cross-context FKs: none touched.
- Keep the change focused on the **companies** context storage layer; do not
  refactor the processing context's duplicated vocabulary (out of scope, low
  risk to leave as-is since storage now enforces the vocabulary regardless).
