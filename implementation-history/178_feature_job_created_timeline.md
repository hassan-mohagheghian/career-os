# Prompt 178 - Jobs created-per-day timeline panel

## Objective

Add a narrow, independently-scrollable panel alongside the Jobs list that shows the
number of jobs created per day, newest first, with month separators ("Month Year" +
a line). The timeline is display-only and independent of the current list
filters/pagination.

## Current State

- `apps/backend/jobs/.../sa_job_repository.py`: `JobModel.created_at` is a `Text`
  column holding ISO datetimes. No per-day aggregation exists.
- `apps/backend/jobs/presentation/api/jobs_v2_router.py` is mounted at `/api/jobs`
  (`root_router.py:35`) and has `GET /list`, `GET /{job_id}`, etc. A static
  `GET /timeline` route is safe (no conflicting path).
- Frontend: `apps/frontend/src/entities/job/api.ts` (`jobApi`), Jobs list page is
  `apps/frontend/src/features/jobs-v2/components/JobsPage.tsx` (flex-col: header →
  toolbar → table). The page widget is `apps/frontend/src/widgets/jobs-page-v2/index.tsx`.

## Changes

Backend:
- Add `count_created_by_day()` to `SQLAlchemyJobRepository` (+ interface) that
  returns `[{date: "YYYY-MM-DD", count}]` for non-deleted jobs, grouped by
  `func.substr(JobModel.created_at, 1, 10)`, ordered date desc.
- Add `JobTimelineResponse` schema and `GET /api/jobs/timeline` in `jobs_v2_router.py`
  returning `{days: [...], total}` (total = sum of counts).

Frontend:
- Add `jobApi.timeline()` and `useJobTimeline()` (react-query) to
  `apps/frontend/src/entities/job/`.
- New `apps/frontend/src/features/jobs-v2/components/JobTimeline.tsx`: a narrow
  (~200px) vertical panel, `overflow-y-auto`, one row per day (date left, count
  right), a month divider (line + "Month Year") whenever the month changes.
- In `JobsPage.tsx` wrap the toolbar+table region in a flex-row and render
  `<JobTimeline/>` beside the table (right side, own scroll).

## Testing Requirements

- Backend: extend the jobs router/repo tests to seed jobs on different dates and
  assert `GET /api/jobs/timeline` returns grouped per-day counts, desc, with total.
- Frontend: unit test `JobTimeline` (renders days + counts, inserts month divider,
  groups months) and `jobApi.timeline()`.
- Run `uv run pytest apps/backend/tests/jobs/ -v` and
  `cd apps/frontend && npx vitest run` + `npm run typecheck`.

## Constraints

- Respect AGENTS.md rule 13: add wireframe
  `docs/ux/features/jobs/job-created-timeline.md` and update `docs/ux/README.md`,
  `docs/ux/DESIGN.md`; document the endpoint in `docs/api/API.md` (and jobs API doc
  if present).
- No raw SQL (rule 2); use SQLAlchemy ORM. `created_at` is Text — group by
  `func.substr` (consistent with existing text-date handling in the repo).
- Keep the timeline display-only (no filtering on click).
- Commit this prompt file together with the change.