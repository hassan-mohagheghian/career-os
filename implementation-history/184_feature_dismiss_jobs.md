# Prompt 184 - Feature: Dismiss recommended jobs (job-level ignore)

## Objective

Let the user **dismiss a recommended job** they decided to skip after reading
the details (nuances that clash with their preferences). Dismissed jobs are
**hidden from the Jobs list by default** and can be reviewed/restored through
a **"Show dismissed"** toolbar toggle. This is intentionally NOT the
application `withdrawn` status: dismissal happens before any application
exists and must not pollute application-funnel metrics.

## Current State

- Analysis produces a recommendation per job (`apply | consider | skip`);
  surfaced as badges + `filterRecommendation` on the Jobs page.
- Exact precedent to mirror — **pinned**: `JobModel.pinned` (column
  `favorite`, Integer), `SQLAlchemyJobRepository.set_pinned`,
  `PUT /jobs/{id}/pinned`, list query param `pinned: bool | None`
  (`== 1/0` filter), frontend `jobApi.setPinned`, `pinnedMutation`
  (optimistic in-memory list update), toolbar toggle button, `PinButton`.
- Tracking statuses are *derived* from applications (`TRACKING_STATUSES`),
  so a job-level flag is the right place for dismissal.

## Implementation Steps

1. **Model**: `JobModel.dismissed` Integer default 0 (column `dismissed`,
   jobs schema).
2. **Repo**: `set_dismissed(job_id, dismissed) -> bool` (mirror
   `set_pinned`, bump `updated_at`); list-method param
   `dismissed: bool | None = None` → when not None filter
   `dismissed == (1 if dismissed else 0)`; None = no filtering (other
   callers unaffected).
3. **Use case**: `ListJobsV2Request.dismissed: bool | None = None`,
   passed through.
4. **Router** (`jobs_v2_router.py`):
   - list param `dismissed: bool | None`; effective value passed to the use
     case is `True` when the filter is on else `False` — i.e. the v2 list
     **excludes dismissed by default**, `dismissed=true` shows only
     dismissed.
   - `PUT /{job_id}/dismissed` (body `{dismissed: bool}`) → 404 when missing;
   - `JobListItemSchema.dismissed: bool` filled from the dict.
5. **Migration**: alembic autogenerate scoped to the job schema → tune →
   rename `job_0XX_add_dismissed.py`; verify single head + round-trip.
6. **Frontend entity**: `JobListItem.dismissed: boolean`;
   `jobApi.setDismissed`.
7. **Hook** `useJobsInfiniteQuery`: `filterDismissed` state (default false);
   params `dismissed: filterDismissed || undefined`; `dismissedMutation`
   mirroring `pinnedMutation` (optimistic `item.dismissed` flip); exposed in
   the returned bag.
8. **Toolbar**: toggle next to the Pinned one — "Show dismissed only"
   (`EyeSlash` icon, pressed state) wired to `onFilterDismissedChange`.
9. **Row action**: Dismiss button on each job row (next to PinButton,
   `Prohibit`/`XCircle` icon, title "Dismiss job — hidden from list") calling
   `onToggleDismissed(job.id, !job.dismissed)`; threaded through JobsTable →
   JobsPage → widget. Dismissing from the default view removes the row from
   the optimistic list (consistent with server-side exclusion).
10. No change to recommendation logic itself — dismissal is user curation on
    top.

## Testing

- Backend: extend `tests/jobs/presentation/api/test_jobs_v2_api.py` —
  PUT endpoint sets/clears the flag (404 unknown id); default list excludes
  dismissed jobs; `dismissed=true` returns only dismissed ones; schema carries
  `dismissed`.
- Frontend: `JobsToolbar.test.tsx` — dismissed toggle fires
  `onFilterDismissedChange`; `entities/job/api.test.ts` — `setDismissed`
  hits `PUT /jobs/{id}/dismissed`.
- Run `uv run pytest apps/backend/tests/jobs -v`, targeted vitest files,
  typecheck.

## Constraints

- Default Jobs list hides dismissed jobs (product decision); recommendation
  scores untouched; reversible (undismiss via the dismissed-only view or the
  row toggle state).
- ORM only; structlog; jobs-schema-local column (no cross-context FK);
  default sort unchanged (rule 7).
- Docs: `docs/ux/features/jobs/dismissed-jobs.md` (wireframe + Mermaid),
  update `docs/ux/features/jobs/page.md`, `docs/ux/README.md`,
  `docs/ux/DESIGN.md`; this prompt. One prompt = one commit (with this file).
