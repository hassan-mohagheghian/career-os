# Prompt 068 - Job Favorites and Recommendation Tags

## Objective

Add three features to the V2 jobs list:

1. **Favorites**: users can star (favorite) a job from the list and filter the
   list to show only favorited jobs.
2. **Recommendation tags**: show the AI recommendation (`apply` / `consider` /
   `skip`) for each job as a colored badge in the row.
3. **Recommendation filter**: filter the list by recommendation (`apply` /
   `consider` / `skip`).

### UX decisions (confirmed with the user)

- **Recommendation** gets its own **dedicated column** after Scores (colored
  badge; decision-driving status attributes get a clear visual token).
- **Favorite** toggle lives in a **dedicated first column** (pinned, star icon).
- The "favorites only" **filter** is a **star toggle button** in the toolbar.

---

# Read Documentation First

Before making changes read:

- docs/domain/jobs/job-list-item.md
- docs/api/jobs/list-jobs.md
- docs/ux/features/jobs/job-row.md
- docs/ux/features/jobs/page.md
- DOMAIN.md, API.md
- apps/backend/jobs/presentation/api/jobs_v2_router.py
- apps/backend/jobs/application/use_cases/list_jobs_v2.py
- apps/backend/jobs/infrastructure/repositories/sa_job_repository.py
- apps/backend/jobs/infrastructure/repositories/sa_job_analysis_repository.py
- apps/backend/jobs/domain/repositories/job_repository.py
- apps/backend/jobs/domain/repositories/job_analysis_repository.py
- apps/backend/tests/jobs/presentation/api/test_jobs_v2_api.py
- apps/frontend/src/features/jobs-v2/hooks/useJobsInfiniteQuery.ts
- apps/frontend/src/features/jobs-v2/components/JobsToolbar.tsx
- apps/frontend/src/entities/job/api.ts
- apps/frontend/src/entities/job/types.ts

---

# Current State

The V2 list (`GET /api/jobs/list`) returns `JobListItemSchema` rows (title,
company, location, remote, visa, job_status, latest_processing_execution,
scores, updated_at, created_at). The recommendation is persisted on the
`job.job_analysis` row but is **not** exposed on the list item (the docs
explicitly list "Recommendations" under excluded data). There is no favorite
concept anywhere.

The list endpoint already avoids N+1 by fetching latest executions in one batch
(`exec_repo.latest_by_target_ids`). The recommendation lookup must follow the
same pattern (batch query on `job_analysis`, which lives in the jobs context).

---

# Implementation Steps

## 1. Favorites — backend

- **Migration** `apps/alembic/job/versions/job_003_add_job_favorite.py`
  (down_revision `42c200d12fd5`): add `favorite` Integer, NOT NULL,
  `server_default '0'` to `job.jobs`; downgrade drops it.
- **`JobModel`**: add `favorite: Mapped[int] = mapped_column(Integer, default=0)`.
- **`Job` entity**: add `favorite: int = 0` to `__init__`, `to_dict`,
  `from_dict`.
- **`job_model_to_dict`**: emit `"favorite": model.favorite`.
- **`IJobRepository` / `SQLAlchemyJobRepository`**:
  - `search_jobs_cursor(...)`: new `favorite: bool | None = None` param; when
    not None filter `JobModel.favorite == (1 if favorite else 0)`.
  - New `set_favorite(job_id: str, favorite: bool) -> bool`: update `favorite`
    and `updated_at`; return False when the job does not exist.
- **`ListJobsV2Request` / `ListJobsV2UseCase`**: new `favorite` field passed
  through to `search_jobs_cursor`.
- **Schemas** `jobs_v2.py`: `JobListItemSchema.favorite: bool = False`,
  `JobListItemSchema.recommendation: str | None = None`,
  `FavoriteJobRequest {favorite: bool}`.
- **Router** `jobs_v2_router.py`:
  - `list_jobs_v2`: `favorite: bool | None = Query(None)` → request; wire
    `favorite` into `_v2_job_to_schema`.
  - New `PUT /api/jobs/{job_id}/favorite` (body `FavoriteJobRequest`): calls
    `repo.set_favorite`, 404 when the job does not exist, returns
    `{"favorite": bool}`.

## 2. Recommendation tags — backend

- **`IJobAnalysisRepository` / `SQLAlchemyJobAnalysisRepository`**: new
  `recommendations_by_job_ids(job_ids: list[str]) -> dict[str, str]` returning
  `{job_id: recommendation}` for non-null recommendations.
- **`jobs_v2_router`**: inject `get_job_analysis_repo`; after building
  `page_job_ids`, batch-fetch recommendations; pass the map into
  `_v2_job_to_schema` and set `recommendation`. Legacy jobs without an analysis
  row keep `recommendation = null` (consistent with the detail endpoint's
  legacy fallback).

## 3. Recommendation filter — backend + frontend

- **`IJobRepository` / `SQLAlchemyJobRepository`**: `search_jobs_cursor(...)` new
  `recommendation: str | None = None` param; when set, filter jobs that have a
  `job_analysis` row with that recommendation
  (`JobModel.id.in_(select(JobAnalysisModel.job_id).where(...))`). Jobs without
  an analysis row never match.
- **`ListJobsV2Request` / `ListJobsV2UseCase`**: new `recommendation` field
  passed through.
- **Router** `list_jobs_v2`: `recommendation: str | None = Query(None, pattern="^(apply|consider|skip)$")`
  → request (invalid values → 422).
- **types** (`entities/job/types.ts`): `RecommendationFilter = 'apply' |
  'consider' | 'skip' | ''`, `JobSearchQuery.recommendation?: RecommendationFilter`.
- **api** (`entities/job/api.ts`): send `recommendation` in `search` and
  `searchInfinite`.
- **`useJobsInfiniteQuery`**: `filterRecommendation` state in `filterKey`,
  `activeFilterCount`, `clearFilters`, and the API call.
- **`JobsToolbar.tsx` + `JobsPage.tsx` + widget**: a "Recommendation" select
  (All / Apply / Consider / Skip) placed after the Visa filter, wired end to
  end.

## 4. Favorites + recommendation — frontend
- **types** (`entities/job/types.ts`): `JobListItem.favorite: boolean`,
  `JobListItem.recommendation: string | null`, `JobSearchQuery.favorite?: boolean`.
- **api** (`entities/job/api.ts`): send `favorite` in `searchInfinite`; add
  `setFavorite(jobId, favorite)` → `api.put<{favorite: boolean}>`.
- **`useJobsInfiniteQuery`**: `filterFavorite` state included in `filterKey`,
  `activeFilterCount`, `clearFilters`, and the API call; `favoriteMutation`
  with an optimistic row update (mirror `processMutation`) that toggles
  `favorite` on the row and invalidates the query on settle.
- **`RecommendationBadge`** (new): `apply` → emerald/green, `consider` → amber,
  `skip` → gray, `null` → "—". Styled like `StatusBadge` (text-2xs, rounded,
  bordered).
- **`FavoriteButton`** (new): star icon toggle with tooltip; must
  `stopPropagation` so row-click (open drawer) is not triggered.
- **`jobsColumns.ts`**: extend `COLUMN_GRID_TEMPLATE` with a narrow first
  `Favorite` column (~44px) and a narrow `Recommendation` column (~80px) after
  Scores.
- **`JobsTable.tsx`**: add the two column defs; pass `onToggleFavorite` through.
- **`JobRow.tsx`**: render `FavoriteButton` in the first cell and
  `RecommendationBadge` in the recommendation cell.
- **`JobsToolbar.tsx` + `JobsPage.tsx`**: star toggle button ("Show favorites
  only", `aria-label`, filled when active) wired end to end.

---

# Testing Requirements

Backend (`apps/backend/tests/jobs/presentation/api/test_jobs_v2_api.py`):

- `favorite=true` returns only favorited jobs; omitted returns all.
- List item carries `favorite` and `recommendation` keys.
- Recommendation is populated from a `job_analysis` row; jobs without analysis
  carry `recommendation = null`.
- `PUT /api/jobs/{id}/favorite` sets/toggles the flag and persists it across
  list calls; 404 for a missing job.
- `recommendation=apply|consider|skip` returns only matching jobs; jobs without
  an analysis never match; invalid values → 422; combines with `favorite`.

Frontend:

- `JobsToolbar.test.tsx`: favorite toggle renders, reports changes, and is
  cleared by "Clear"; recommendation select renders, reports the selection,
  and shows the active label.
- `useJobsInfiniteQuery.test.tsx`: favorite filter flows into the query and
  the active filter count; recommendation filter sends the param, omits it when
  empty, and is cleared alongside the others.
- `JobRow` / `RecommendationBadge` / `FavoriteButton` tests: badge renders for
  apply/consider/skip/null; star toggle calls the callback and stops
  propagation.

Run: `uv run pytest apps/backend/tests/ -v` and
`cd apps/frontend && npx vitest run && npm run lint && npm run typecheck`.

---

# Important Constraints

- Follow AGENTS.md: no raw SQL, no `print()`, no routes in `entrypoints/api.py`,
  contexts must not cross-import (the recommendation batch query stays in the
  jobs context — `job_analysis` is already there).
- `favorite` is managed only by its dedicated endpoint, **not** exposed through
  the Edit Job drawer (`EDITABLE_FIELDS` unchanged).
- Keep the list endpoint N+1-free: batch lookups for recommendations.
- Docs and tests must be updated in the same change (no drift).
- All version references stay in sync (VERSION, CHANGELOG, pyproject.toml,
  package.json) and `./scripts/check-version.sh` must pass.
