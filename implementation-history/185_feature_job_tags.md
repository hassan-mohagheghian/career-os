# Prompt 185 - Job Tags

## Objective

Add user-defined tags to jobs so users can categorize and filter jobs by custom labels. Tags are stored as a JSON array of strings on the job (no separate tag table). The feature includes a Tags column in the jobs list, a multi-select toolbar filter, and tag management (add/remove) per job.

## Current State

- Jobs have no tags infrastructure. The `jobs` table has no `tags` column.
- The closest pattern is `skills.tags` (a JSON `Text` column storing `["tag1", "tag2"]`).
- The `JobModel` has 60+ columns. A `tags` TEXT column is the lightest approach.
- The jobs list uses `search_jobs_cursor` with in-memory post-filters for some fields.
- The frontend `JobListItem` type has no `tags` field.

## Implementation Steps

### 1. Migration (backend)

Create `apps/alembic/job/versions/job_007_add_tags.py`:
- `op.add_column("jobs", sa.Column("tags", sa.Text, server_default="[]", nullable=False), schema="job")`
- revision: `job_007`, down_revision: `job_006`
- Follow the exact pattern of `job_006_add_dismissed.py`

### 2. JobModel (backend)

In `apps/backend/jobs/infrastructure/models/job_model.py`:
- Add: `tags: Mapped[str] = mapped_column("tags", Text, server_default="[]", nullable=False)`

### 3. Mapper (backend)

In `apps/backend/jobs/infrastructure/mappers.py`:
- Add `"tags": model.tags` to `job_model_to_dict` output

### 4. Schema (backend)

In `apps/backend/jobs/presentation/api/schemas/jobs_v2.py`:
- Add `tags: list[str] = Field(default_factory=list)` to `JobListItemSchema`

### 5. ListJobsV2Request (backend)

In `apps/backend/jobs/application/use_cases/list_jobs_v2.py`:
- Add `tags: list[str] | None = None` to `ListJobsV2Request`

### 6. Repository filter (backend)

In `apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`:
- In `search_jobs_cursor`: add tag filter after existing filters. Parse the stored JSON `tags` column and filter jobs that contain ALL specified tags (intersection).
- Add `tags` param to the method signature, pass through from the request.

### 7. Router (backend)

In `apps/backend/jobs/presentation/api/jobs_v2_router.py`:
- Add `tags: str | None = Query(None)` param to `list_jobs_v2` (comma-separated string, e.g. `?tags=python,remote`)
- Parse into list, pass to `ListJobsV2Request`
- In `_v2_job_to_schema`: parse job dict `tags` JSON string into list, include in schema
- Add `PUT /{job_id}/tags` endpoint: `{ tags: ["tag1", "tag2"] }` → update the job's tags column
- In `get_job_detail`: include tags in response
- In `update_job`: handle tags update if provided

### 8. Frontend types

In `apps/frontend/src/entities/job/types.ts`:
- Add `tags: string[]` to `JobListItem`
- Add `tags: string[]` to `JobDetail`
- Add `tags?: string[]` to `JobEditInput`

### 9. Frontend API

In `apps/frontend/src/entities/job/api.ts`:
- Add `tags?: string` to `JobSearchQuery` (comma-separated)
- Add `setTags: (jobId: string, tags: string[]) => api.put(...)` function
- Pass `tags` in `searchInfinite` params

### 10. Hook (frontend)

In `apps/frontend/src/features/jobs-v2/hooks/useJobsInfiniteQuery.ts`:
- Add `filterTags: string[]` state (default `[]`)
- Pass `tags: filterTags.length ? filterTags.join(',') : undefined` to query params
- Add `tagsMutation` for setting tags on a job (optimistic update)

### 11. Table column (frontend)

In `apps/frontend/src/features/jobs-v2/components/jobsColumns.ts`:
- Add `Tags` column (position after Scores or after Rec)
- Set grid template width (e.g. `minmax(120px, 1.5fr)`)

### 12. JobRow (frontend)

In `apps/frontend/src/features/jobs-v2/components/JobRow.tsx`:
- Render tags as compact badges (e.g. `[python] [remote]`)
- Clicking a tag adds it to the filter
- Show an `+` button to add a tag (opens inline input or popover)

### 13. Toolbar filter (frontend)

In `apps/frontend/src/features/jobs-v2/components/JobsToolbar.tsx`:
- Add a multi-select dropdown for tags
- Collect unique tags from loaded items
- Toggle tags in/out of `filterTags`

### 14. Widget adapter (frontend)

In `apps/frontend/src/widgets/jobs-page-v2/index.tsx`:
- Thread `filterTags`/`setFilterTags` and `tagsMutation` through props

### 15. Tests (backend)

- Test tag filter returns only jobs with all specified tags
- Test tag filter with empty tags returns all jobs
- Test PUT /{id}/tags sets tags
- Test tags appear in list response
- Test tags appear in detail response

### 16. Tests (frontend)

- Test JobRow renders tag badges
- Test toolbar multi-select filter

### 17. Docs

- Create `docs/ux/features/jobs/job-tags.md` (wireframe + Mermaid)
- Update `docs/ux/features/jobs/page.md` (Tags column, tag filter)
- Update `docs/ux/README.md` (index)
- Update `docs/ux/DESIGN.md` (wireframe)

## Constraints

- Tags are stored as JSON `Text` column on `jobs` (no separate table).
- Tags are user-defined strings (no predefined set).
- Multi-select filter: intersection logic (job must have ALL selected tags).
- Default sort is newest first.
- No FK to a tags table (tags are free-form strings).
- Follow existing patterns (e.g., `skills.tags` JSON column pattern).
