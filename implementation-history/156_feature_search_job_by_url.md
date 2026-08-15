# Prompt 156 - Search jobs by their link

## Objective

Let a user find a job by pasting its posting URL (or any unique URL fragment)
into the jobs list search box.

## Current State

- `GET /api/jobs/list` accepts `query` and searches via
  `search_jobs_cursor` (`sa_job_repository.py`). The `query` filter only
  matches title, company, location and role — the job `url` column is never
  searched, so pasting a link returns no results.
- The non-cursor `search_jobs` (legacy list) has the same four-field search.

## Changes

- `apps/backend/jobs/infrastructure/repositories/sa_job_repository.py`: add
  `JobModel.url.ilike(like)` to the `query` search in both `search_jobs` and
  `search_jobs_cursor`.

## Testing Requirements

- Add `TestSearchJobs.test_query_filter_matches_url` and
  `TestSearchJobsCursor.test_query_matches_url` in
  `apps/backend/tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py`.
- Run:
  `uv run pytest apps/backend/tests/jobs/infrastructure/repositories/test_sa_job_repository_extra.py -q`
- Manual check against dev DB: `search_jobs_cursor(query="https://www.linkedin.com/jobs/view/4446195950")`
  returns the stored job (verified live: matched `019fb524-eb16-70ee-a5c5-e23c75946e42`).

## Docs

- `docs/api/jobs/list-jobs.md`: note URL in the Search section.
- `docs/ux/features/jobs/page.md`: Search control description mentions job link.

## Constraints

- No schema/migration change; pure query filter change. Respect AGENTS.md 2
  (implementation history first), 13 (UX docs), 16 (no new event needed).
