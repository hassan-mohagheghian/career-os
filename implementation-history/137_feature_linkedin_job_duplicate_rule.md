# Prompt 137 - LinkedIn job duplication rule + rule drawer placement

## Objective

Two changes batched into 137:

1. Replace the exact primary-URL match used by `POST /api/jobs` with a
   **rule-based duplicate detector**. The first rule targets LinkedIn job links:
   the LinkedIn job id lives in the URL path (`/jobs/view/{job_id}/`), so the same
   posting reached via different tracking/query strings must be caught as a
   duplicate. Other job boards get their own rule later; until a rule exists, a
   posting URL is **not** restricted (per product decision).
2. Open the **Add / Edit Rule drawer from the right side** (placement `right`),
   consistent with every other drawer in the app (it previously used
   `placement="bottom"`).

## Current State

- `apps/backend/jobs/presentation/api/jobs_router.py` `create_job` calls
  `repo.get_by_url(body.job_post_url)` — an **exact** URL match.
- LinkedIn links carry a stable `job_id` in the path
  (`https://www.linkedin.com/jobs/view/4333938709/?trackingId=...`), so the
  same posting pasted with different tracking params slips past the exact
  match and creates a duplicate.
- The CLI `add` command already normalizes (strips query) via `normalize_url`,
  so CLI-side LinkedIn dedup already works; the gap is the API create flow used
  by the Add Job drawer.
- `JobAlreadyExistsError` (`shared/application/exceptions.py`) already exists
  with code `JOB_ALREADY_EXISTS` and a `details.job_id` payload the UI links to.

## Changes

- New domain service `apps/backend/jobs/domain/services/job_url_rules.py`:
  - `JobUrlDuplicateRule` ABC with `duplicate_fragment(url) -> str | None`.
  - `LinkedInJobUrlRule` — applies only when the host is `linkedin.com` (any
    subdomain) and the path matches `/jobs/view/<numeric id>`; returns the
    fragment `linkedin.com/jobs/view/{job_id}`.
  - `JOB_URL_DUPLICATE_RULES` registry (currently only the LinkedIn rule) and
    `find_duplicate_job(repo, url)` helper that runs the rules and returns the
    first existing (non-deleted) job or `None`.
- `apps/backend/jobs/domain/repositories/job_repository.py`: add
  `get_by_url_fragment(fragment)` to the interface.
- `apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`:
  implement `get_by_url_fragment` as a non-deleted `url` LIKE lookup.
- `apps/backend/jobs/presentation/api/jobs_router.py`: `create_job` uses
  `find_duplicate_job` instead of `get_by_url`. Non-LinkedIn URLs now have **no**
  duplicate restriction (their rule comes later).
- CLI `add` unchanged — already handles the LinkedIn case via `normalize_url`.
- `apps/frontend/src/features/rules/components/RuleFormDrawer.tsx`: changed the
  shared `Drawer` placement from `bottom` to `right` so the Add / Edit Rule
  drawer slides in from the right like the other drawers.
- `apps/frontend/src/features/rules/components/RulesTab.test.tsx`: updated the
  drawer test description to "from the right".
- `docs/ux/features/rules/rule-form-drawer.md`, `docs/ux/README.md`,
  `DESIGN.md`: documented the right-side placement + updated wireframe.

## Follow-Up (done in 138)

- Remove the legacy jobs module:
  `apps/backend/jobs/application/use_cases/list_jobs.py`,
  `apps/backend/jobs/presentation/api/jobs_router.py` — verify the app is fully
  on the V2 jobs list / create endpoints first.
  → Completed in `138_chore_remove_legacy_jobs_router.md`.

## Testing Requirements

- Unit tests for the rule (`apps/backend/tests/jobs/domain/`): LinkedIn URL with
  query/tracking params produces the fragment; non-LinkedIn and non-job URLs
  return `None`; `find_duplicate_job` returns the existing job or `None`.
- Repository test for `get_by_url_fragment` (non-deleted filter, LIKE match).
- API tests in `apps/backend/tests/jobs/presentation/api/test_create_job.py`:
  - Replacing `test_create_duplicate_url_returns_409`: creating the **same
    non-LinkedIn URL twice now succeeds twice** (no restriction).
  - New: two LinkedIn URLs with the **same** job id but different tracking
    params → second returns `409` with `details.job_id`.
  - New: LinkedIn URLs with **different** job ids → both `201`.
- Run `uv run pytest apps/backend/tests/jobs/ -v`.

## Constraints

- Only LinkedIn links are restricted for now; every future board adds its own
  rule to the registry — no `if`-chains in the endpoint.
- Keep `JobAlreadyExistsError` code/message unchanged (frontend asserts the
  message and links to `details.job_id`).
- Rule drawer uses the shared `Drawer` `right` placement (default) and the
  `lg` variant, matching the other drawers.
- No version bump (feature batched at release).
- No schema change, no migration, no new domain events.
