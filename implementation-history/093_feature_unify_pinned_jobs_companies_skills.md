# Prompt 093 - Unify Pinned Across Jobs, Companies, Skills

## Objective

Unify a single **Pinned** concept (pushpin) across Jobs, Companies, and Skills
with equivalent functionality, replacing the Jobs "favorite" concept. Each
table gets the same UX: a pin column (shown by default, toggleable via a
Columns dropdown), an optimistic pin toggle per row, and a toolbar "Pinned"
filter.

## Current State

- Jobs exposed a `favorite` flag (physical DB column `favorite`, integer
  default 0) with a star `FavoriteButton`, `?favorite=` list filter and
  `PUT /jobs/{id}/favorite`.
- Skills already had a full pinned pipeline (model `pinned`, filter, pin
  column, PinButton component).
- Companies had no pinned support at all.

## Implementation Steps

### Backend

1. **Jobs favorite → pinned (public API rename, physical column preserved)**
   - `JobModel.pinned = mapped_column("favorite", Integer, default=0)` — no data
     migration on the large jobs table.
   - Rename the public contract to `pinned` in: mapper
     (`job_model_to_dict` key `"pinned"`), domain `Job` entity param,
     `PinJobRequest` schema, `PUT /jobs/{id}/pinned` returning `{"pinned"}`,
     list filter `pinned: bool | None`, `ListJobsV2Request`,
     `IJobRepository.set_pinned` + SQLAlchemy impl.
2. **Companies pinned (real new column)**
   - `CompanyModel.pinned` Integer default 0; `company_model_to_dict`
     `"pinned"`; `ICompanyRepository.set_pinned` + SQLAlchemy impl (bumps
     `updated_at`).
   - `CompanyPinRequest` schema, `PUT /companies/{id}/pinned` (404 when
     missing), list filter `pinned: bool | None = Query(None)` (both `true` and
     `false` filter, mirroring jobs) + `_matches` filtering.
   - Alembic migration `5b6c673f3d38` (moved into `apps/alembic/company/versions/`,
     tuned to `op.add_column(..., server_default='0')` only); single head.
3. **Tests** — `TestJobPinnedV2API` (renamed) and `TestCompanyPinnedV2API`
   (default false on list item, `?pinned=true/false` filter, set/toggle,
   404).

### Frontend

4. **Shared `PinButton`** — `shared/components/PinButton.tsx` (pushpin icon,
   optimistic-style ghost button, `aria-label`/`aria-pressed`, tooltip).
   Skills switch to it; jobs and companies use it.
5. **Jobs rename** — `entities/job/types.ts` + `api.ts` (`setPinned`,
   `?pinned=`), `useJobsInfiniteQuery` (`filterPinned`, `pinnedMutation`),
   `JobRow`/`JobsTable` (`showPinnedColumn`, `COLUMN_GRID_TEMPLATE_NO_PIN`),
   `JobsToolbar` (Pinned filter button + Columns dropdown),
   `JobsPage`, `widgets/jobs-page-v2` (`showPinnedColumn` default true).
   Delete `FavoriteButton.tsx/.test.tsx`.
6. **Companies pinned** — `entities/company/types.ts` (`pinned`), `api.ts`
   (`setPinned`, `?pinned=`), `hooks.ts` (`filterPinned`, `pinnedMutation`),
   `CompanyRow`/`CompaniesTable` (`showPinnedColumn`, pin column),
   `CompaniesToolbar` (Pinned filter + Columns dropdown), `CompaniesPage`,
   `widgets/companies-page`.
7. **Pinned column default** — `showPinnedColumn` defaults to `true` for all
   three tables and the widgets' `useState(true)`.

### Docs

8. UX docs (`jobs/page.md`, `jobs/job-row.md`, `jobs/favorite-job.md` →
   `jobs/pinned-job.md`, `companies/page.md`, `skills/page.md`) updated with
   wireframes showing the Pin column and Pinned filter. `API.md`, `DOMAIN.md`,
   `docs/domain/jobs/job-list-item.md`, `docs/api/jobs/list-jobs.md` updated
   for the public rename (physical jobs column stays `favorite`).

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/ -q` — all pass.
- Frontend: `npx vitest run` (450 tests pass); `tsc --noEmit` shows no new
  errors in touched files (pre-existing errors in untouched files remain).
- `npm run lint` is not runnable in this repo (no eslint installed; pre-existing).

## Constraints

- Do not change the physical `favorite` column on `job.jobs` (avoid migration on
  the large table). Keep jobs exposing `pinned` at the API/DTO level.
- All AI calls still go through `LLMService`; ORM only; no raw SQL.
- Version bump `3.7.x → 3.8.0` in `VERSION`, `CHANGELOG.md`, `pyproject.toml`,
  `apps/frontend/package.json` + git tag (per release rules).
