# Prompt 143 - Recruiter detection helper + purple row tint

## Objective

Replace the two duplicated inline `isRecruiterType` checks with one shared
recruiter-detection helper and give recruiter companies a light purple row tint
in the companies list so they are visually distinguishable from product
companies.

## Current State

- `CompanyRow.tsx` and `CompanyDetailDrawer.tsx` each define their own
  `RECRUITER_TYPES` + `isRecruiterType` (type-only check on
  `RECRUITING_AGENCY` / `STAFFING_COMPANY`).
- The row already switches the Jobs column between `job_count` and
  `recruiter_job_count` based on that type check.

## Changes

- Add `entities/company/lib.ts` with `RECRUITER_TYPES` and
  `isRecruiterCompany(company)`:
  `company_type in RECRUITER_TYPES` **or** `recruiter_job_count > 0`.
- `CompanyRow.tsx`: use `isRecruiterCompany`, add the purple tint classes
  (`bg-purple-500/5`, stronger on hover / focus) and a
  `data-recruiter="true"` attribute.
- `CompanyDetailDrawer.tsx`: swap its local `isRecruiterType` for the shared
  helper.
- Document the tint and detection rule in
  `docs/ux/features/companies/company-row.md` (ASCII wireframe).

## Testing Requirements

- New `entities/company/lib.test.ts` covering type-based, count-based, missing,
  and null inputs.
- New `CompanyRow` tests asserting the `data-recruiter` attribute for type- and
  count-detected recruiters and its absence for product companies.
- Run `npx vitest run` and `npm run typecheck`.

## Constraints

- Recruiter detection must stay pure (no hooks, no API calls).
- The Jobs-column behavior (recruiter shows `recruiter_job_count` "listed for
  clients") is preserved.
