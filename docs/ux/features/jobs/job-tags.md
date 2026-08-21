# Job Tags

## Purpose

Tags let the user apply custom labels to jobs for personal categorization.
Jobs can be tagged with any free-form string. The Tags column shows applied
tags, and the toolbar provides a multi-select filter to narrow the list by
one or more tags.

---

# Related Page

Located in:

- `features/jobs/page.md`
- `features/jobs/job-row.md`

Related:

- `api/jobs/list-jobs.md`

---

# User Goals

The user should be able to:

- See which tags are applied to each job
- Filter the job list by one or more tags
- Tags are user-defined strings (no predefined set)

---

# Tags Column

Each job row shows up to 3 tags as compact badges. If a job has more than 3
tags, a `+N` indicator shows the remaining count.

```text
[python] [remote] [senior]
```

or with overflow:

```text
[python] [remote] +2
```

Tags are stored as a JSON array of strings on the job.

---

# Tags Filter

The toolbar includes a multi-select tags dropdown.

```text
Tags (2)
  ☑ python
  ☑ remote
  ☐ java
  ☐ senior
```

Selecting multiple tags applies an **intersection** filter: only jobs that
have ALL selected tags are shown. The filter counts as an active filter and
is cleared by the toolbar's Clear action alongside the others.

---

# Data Model

Tags are stored as a JSON-serialized `Text` column (`tags`) on the `jobs`
table. The column default is `"[]"`.

```json
["python", "remote", "senior"]
```

No separate tags table exists. Tags are free-form user-defined strings.

---

# API

## List with tag filter

```
GET /api/jobs/list?tags=python,remote
```

Returns only jobs that contain all specified tags.

## Set tags

```
PUT /api/jobs/{job_id}/tags
{ "tags": ["python", "remote"] }
```

Replaces the existing tags on the job.

---

# Accessibility

- Tag badges use readable text sizes.
- The multi-select filter uses native checkboxes for keyboard accessibility.

---

# Related Documents

- `features/jobs/page.md`
- `features/jobs/job-row.md`
- `api/jobs/list-jobs.md`
