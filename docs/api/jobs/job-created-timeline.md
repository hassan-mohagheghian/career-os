# Jobs Created Timeline

`GET /api/jobs/timeline`

Returns the number of **non-deleted** jobs created per calendar day, newest
first. Grouped by the day portion of `created_at` (a `Text` ISO column via
`substr(created_at, 1, 10)`). Display-only; independent of list filters.

```json
{
  "days": [ { "date": "2026-08-19", "count": 3 }, { "date": "2026-08-18", "count": 5 } ],
  "total": 8
}
```

- `days` — newest first; `date` is `YYYY-MM-DD`, `count` is that day's jobs.
- `total` — sum of all `count`s.
- Deleted jobs (`deleted == 1`) are excluded. Jobs with `NULL` `created_at` are
  excluded.

## Repository

`SQLAlchemyJobRepository.count_created_by_day()` groups by
`func.substr(JobModel.created_at, 1, 10)` and orders by the **same** SQL
expression object (`day.desc()`), reusing it for both `GROUP BY` and `ORDER BY`
— required by PostgreSQL to avoid a `GroupingError`.

## Related

- `docs/api/API.md` — endpoint overview.
- `docs/ux/features/jobs/job-created-timeline.md` — the frontend side panel.