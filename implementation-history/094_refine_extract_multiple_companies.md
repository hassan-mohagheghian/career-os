# Prompt 094 - Refine Company Extraction for Multiple Companies

## Objective

Refine company extraction during job processing so a job posting can reference
multiple companies (a hiring company + zero or more recruiting / staffing /
consulting companies) and classify each one correctly instead of collapsing the
posting into a single flat company name.

- The `job.analyze` LLM call extracts a nullable `hiring_company` and a
  `related_companies` list, each entry carrying `name`, `normalized_name`,
  `company_type`, `confidence` (0.0–1.0) and `reason`.
- Do **not** assume the publishing company is the hiring company; weak evidence
  (recruiter logo / contact info / recruiter website) must not promote a
  recruiter to hiring company. When the hiring company cannot be determined with
  reasonable evidence, `hiring_company` is `null` (never guess).
- Normalize names only (e.g. "Google LLC" → "Google"); never merge companies.
  Matching against existing DB companies and creating recruiter relationships is
  the backend's job.
- Recruiter relationships are persisted per job in a new `job_companies`
  association table and surfaced in the Job detail drawer ("Published by …") and
  the Company detail drawer ("Recruiter for …").

## Current State

- `job.analyze` (`processing/application/services/job_analysis_prompt.py`,
  schema `build_job_analysis_output_schema()`, validated by
  `processing/application/services/job_analysis_validation.py`) extracts only
  flat `company` + `company_url` strings. The `LinkCompanyNode`
  (`processing/application/workflows/job_analysis/nodes/link_company_node.py`)
  matches/creates a single company and sets `job.company_id`.
- A job has no way to record that it was published by a recruiter while the
  hiring company is a different entity.
- `CompanyMatchingService.find_or_create(name, website)` never sets
  `company_type`; the companies table already has a `company_type` column using
  the vocabulary `PRODUCT_COMPANY / RECRUITING_AGENCY / STAFFING_COMPANY /
  CONSULTING_COMPANY / UNKNOWN`.
- Legacy extraction prompt `jobs/infrastructure/ai/prompts/step3_extract_raw.txt`
  also returns a single `company` field.

## Extraction Spec (LLM prompt content)

The extraction behavior the analyze prompt must follow is defined inline below.
This text is embedded into the job analysis prompt and mirrored in the legacy
`step3_extract_raw.txt` prompt.

---

### Company Extraction Task

You are responsible for identifying every company mentioned in a job posting.

A job may reference multiple companies.

Your task is to classify them correctly.

#### Goal

Extract all companies mentioned in the job and classify their relationship to
the job.

There are two major categories:

1. Hiring Company (the company actually hiring)
2. Recruiting / Staffing / Agency Companies

A job may have:

- one hiring company
- zero or more recruiting companies

Examples:

Direct hiring

```
Google
```

→ Hiring Company: Google

Recruiter-published

```
Google
published by Hays
```

→ Hiring Company: Google, Recruiting Company: Hays

Multiple recruiters

```
Google
published by Hays
also published by Michael Page
```

→ Hiring Company: Google, Recruiting Companies: Hays, Michael Page

Unknown hiring company

```
Confidential company
published by Hays
```

→ Hiring Company: null, Recruiting Companies: Hays

#### Important Rules

Do NOT assume the publishing company is the hiring company.

Only classify a company as Hiring Company when there is reasonable evidence.

Strong evidence:

- "Join Google"
- "Google is hiring"
- "At Google..."
- Company benefits described as internal
- Company culture described as internal
- Official company domain
- Company career page

Weak evidence:

- Job posted on recruiter website
- Recruiter contact information
- Recruiter logo

Weak evidence should NOT make a recruiter become the hiring company.

#### Company Types

Possible company_type values:

- hiring
- recruiter
- staffing
- consulting
- outsourcing
- unknown

#### Confidence

Each extracted company must contain a confidence score.

0.0 - 1.0

Examples:

- 1.0 — Official company career page
- 0.95 — Clearly stated employer
- 0.70 — Likely employer
- 0.40 — Mentioned without enough evidence

#### Existing Companies

The system already contains companies. You are NOT responsible for matching
database IDs. Only normalize names.

Example:

- "Google LLC" → Google
- "Google Inc." → Google

#### Unknown Hiring Company

If the hiring company cannot be confidently determined, return
`"hiring_company": null`. Do NOT guess.

#### Output Schema

Return JSON only.

```json
{
  "hiring_company": {
    "name": "...",
    "normalized_name": "...",
    "company_type": "hiring",
    "confidence": 0.98,
    "reason": "..."
  },
  "related_companies": [
    {
      "name": "...",
      "normalized_name": "...",
      "company_type": "recruiter",
      "confidence": 0.96,
      "reason": "..."
    }
  ]
}
```

#### Additional Notes

- A recruiter may publish hundreds of jobs.
- The same hiring company may appear through multiple recruiters.
- Do NOT merge companies. Simply extract every company and classify it correctly.
- The backend will later: search existing companies, match nearest company,
  create new companies when necessary, create recruiter relationships.
- Return only valid JSON.

---

## Implementation Steps

### Backend — extraction schema/prompt/validation

1. `processing/application/services/job_analysis_prompt.py`:
   - Add a `companies` object to `build_job_analysis_output_schema()`:
     `hiring_company` (nullable) + `related_companies` (array), each company ref
     `{name, normalized_name, company_type ∈ {hiring, recruiter, staffing,
     consulting, outsourcing, unknown}, confidence (0–1), reason}`.
   - Prompt: keep flat `company` / `company_url` as backward-compat projections
     (`company` = hiring company name, else highest-confidence related company).
     Add the extraction rules above.
   - Bump `JOB_ANALYSIS_PROMPT_VERSION → 1.3.0`, `JOB_ANALYSIS_SCHEMA_VERSION →
     1.1.0`.
2. `processing/application/services/job_analysis_validation.py`: add
   `CompanyReference` (name required, confidence clamped 0–1, company_type
   enum) + `Companies` (`hiring_company: CompanyReference | None`,
   `related_companies: list[CompanyReference]`); attach `companies` to
   `JobAnalysisOutput`.
3. `processing/application/services/job_analysis_scoring.py`: project
   `fields.company` from `companies.hiring_company.name` (fallback to
   highest-confidence related company) so the existing job projection stays
   populated.
4. Legacy `jobs/infrastructure/ai/prompts/step3_extract_raw.txt`: add the same
   `companies` block to the output schema.

### Backend — persistence (job_companies table)

5. New migration `apps/alembic/job/versions/job_005_add_job_companies.py` (job
   context): `id` PK, `job_id` FK → `job.jobs.id` (indexed), `company_id` FK →
   `company.companies.id` (indexed), `role` (`hiring`/`recruiter`), `company_type`,
   `confidence` float, `reason` text, `created_at`. Verify `alembic upgrade head`.
6. New `JobCompanyModel` (`jobs/infrastructure/models/job_company_model.py`) +
   domain entity + repository interface +
   `SQLAlchemyJobCompanyRepository` (replace-for-job: delete rows for a job,
   then bulk insert — reprocessing overwrites cleanly).

### Backend — matching + linking

7. `companies/application/services/company_matching_service.py`: extend
   `find_or_create(name, website, company_type=None)` to set `company_type` on
   new inserts only; add spec→vocabulary mapping
   (`hiring→PRODUCT_COMPANY`, `recruiter→RECRUITING_AGENCY`,
   `staffing→STAFFING_COMPANY`, `consulting→CONSULTING_COMPANY`, else `UNKNOWN`).
8. `processing/application/workflows/job_analysis/nodes/link_company_node.py`:
   resolve the hiring company (existing behavior → `job.company_id` /
   `job.company`), then resolve every related company, `find_or_create` it, and
   write `job_companies` rows with `role="recruiter"`. Best-effort — never fails
   the execution. When `hiring_company` is null, fall back `job.company` to the
   highest-confidence related company.
9. `processing/infrastructure/workflow/assembly.py`: build the job-company
   repository and inject it into `JobAnalysisGraph` → `LinkCompanyNode`.

### Backend — APIs

10. `jobs/presentation/api/schemas/jobs_v2.py` + `jobs_v2_router.py`: job detail
    gains `related_companies: [{company_id, name, role, company_type,
    confidence, reason}]`.
11. `companies/presentation/api/` : company detail gains `recruiter_for`
    (distinct hiring companies, each with name/id + job count) and
    `recruiter_job_count`.

### Frontend

12. `entities/job/types.ts` + `api.ts`: `related_companies` on `JobDetail`.
13. `features/jobs-v2/components/JobDetailDrawer.tsx`: "Published by …" section
    listing recruiter companies (link to `/companies?company=<id>`, type badge,
    confidence).
14. `entities/company/types.ts` + `api.ts`: `recruiter_for` + `recruiter_job_count`.
15. `features/companies-v2/components/CompanyDetailDrawer.tsx`: "Recruiter for"
    section (hiring companies + job counts, clickable).

### Docs (AGENTS.md rule 13 — wireframes required)

16. `docs/ux/features/jobs/job-detail.md` ("Published by" block),
    `docs/ux/features/companies/company-detail.md` ("Recruiter for" block),
    `docs/ux/flows/jobs/process-job.md`; `docs/workflows/job-processing.md`;
    `docs/api/jobs/*`, `docs/api/companies/*`; `DOMAIN.md` (hiring vs recruiter
    rule); `docs/ux/README.md` index; `DESIGN.md`.

### Tests (TDD)

17. Backend: validation models, schema/prompt version, `build_analysis_result`
    company projection, `find_or_create(company_type)`, `link_company_node`
    (hiring + recruiters, null hiring, best-effort), job-company repo replace
    semantics, API tests (job detail `related_companies`, company detail
    `recruiter_for`).
18. Frontend: vitest for new drawer sections + types.

### Release

19. MINOR bump → `3.9.0`: `VERSION`, `CHANGELOG.md`, `pyproject.toml`,
    `apps/frontend/package.json`; `./scripts/check-version.sh`; commit + tag.

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/ -v` (new tests + no regressions).
- Frontend: `cd apps/frontend && npx vitest run` + `npm run lint` + `npm run typecheck`.
- Migration applies cleanly: `uv run alembic upgrade head`.

## Constraints

- All AI calls via `LLMService`. No raw SQL outside migrations.
- `link_company` stays best-effort — never fails the job execution.
- Contexts must not cross-import: the processing context wires the companies
  matching service and the jobs job-company repository via `assembly.py`.
- The combined `job.analyze` call remains the single LLM call per job.
- `job_companies` rows are replaced on re-processing.

## Implementation Status — DONE

Implemented in full (2026-08-06):

- **Backend**: `companies` block (hiring_company + related_companies) on the
  analyze schema/prompt/validation (prompt 1.3.0 / schema 1.1.0); flat
  `company` projected from `hiring_company.name`; legacy `step3_extract_raw`
  prompt updated; `job_companies` table + model + repo (replace-for-job);
  `find_or_create(company_type)` mapping; `LinkCompanyNode` resolves hiring +
  recruiters best-effort; job detail `related_companies`; company detail
  `recruiter_for` + `recruiter_job_count`.
- **Frontend**: "Published by …" in the Job detail drawer; "Recruiter for …" in
  the Company detail drawer; types + API clients.
- **Docs**: UX wireframes, workflow/API/domain docs, `docs/ux/README.md`,
  `DESIGN.md`.
- **Release**: bumped to `3.9.0`; `./scripts/check-version.sh` passes.
