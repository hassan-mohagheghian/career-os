# Company Type

`companies.company_type` is a **fixed vocabulary** — a company is always one of:

| Value               | Display (list badge) |
| ------------------- | -------------------- |
| `PRODUCT_COMPANY`   | Product              |
| `RECRUITING_AGENCY` | Recruiting Agency    |
| `STAFFING_COMPANY`  | Staffing             |
| `CONSULTING_COMPANY`| Consulting           |
| `UNKNOWN`           | Unknown              |

No other value is ever stored. `UNKNOWN` is the catch-all for anything the
classifier cannot determine with confidence.

## Normalization

`companies.domain.company_type.normalize_company_type(value)` is the single
authority:

- `None` / empty / whitespace → `None` (not classified yet)
- a recognized value (case-insensitive, underscores) → uppercased fixed value
- anything else → `UNKNOWN`

It is applied at every storage boundary so a company's stored type can never
drift outside the vocabulary:

- `CompanyService.persist_analysis` — every processing / reprocessing persist
- `PUT /api/companies/{id}` (`update_company`) — manual edits from the edit
  drawer's constrained Select

## Corrective reprocessing

The type is derived from the company's research context (website + links +
notes). When job processing mis-classifies a company (e.g. detects
`RECRUITING_AGENCY` but it is actually `STAFFING_COMPANY`), the user can:

1. add more links / notes for the company (company detail → edit → Notes &
   Links), and
2. reprocess the company (`POST /api/companies/{id}/reprocess`).

The fresh analysis re-collects those sources and persists a **fixed** type.
Manual correction is also possible via the edit drawer's Company Type Select.