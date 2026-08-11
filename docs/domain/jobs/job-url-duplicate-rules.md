# Job URL Duplicate Rules

## Purpose

Detects, at job creation (`POST /api/jobs`), whether a posting URL refers to a
job that already exists in the system — even when the URL differs from the
stored one (tracking parameters, subdomains, redirects).

Duplicate detection is **rule-based**: every job board gets its own rule. A
board with no rule yet is **not** restricted.

---

# Rule Contract

A `JobUrlDuplicateRule` (`jobs/domain/services/job_url_rules.py`):

- has a stable `name`;
- returns a `duplicate_fragment(url)` — a stable substring that any URL for
  the same posting must contain — or `None` when the rule does not apply to the
  URL.

The registry `JOB_URL_DUPLICATE_RULES` is evaluated in order. For each rule
that applies, `find_duplicate_job(repo, url)` looks up the first **non-deleted**
job whose URL contains the fragment via `IJobRepository.get_by_url_fragment`.
The first hit raises `JobAlreadyExistsError` (409) with the existing job id.

---

# Rules

## LinkedIn

- **Fragment key:** the job id in the URL path — `linkedin.com/jobs/view/{job_id}`.
- **Applies when:** the host is `linkedin.com` (any subdomain) and the path
  contains `/jobs/view/<numeric id>`.
- **Query parameters** (`trackingId`, `refId`, `eBP`, `alternateChannel`, ...)
  are ignored — they change per visit and do not identify the posting.

Example pair treated as a duplicate:

```
https://www.linkedin.com/jobs/view/4333938709/?trackingId=AAA
https://www.linkedin.com/jobs/view/4333938709/?trackingId=CCC%3D%3D&refId=DDD
```

---

# Adding a Rule for a New Job Board

1. Add a subclass of `JobUrlDuplicateRule` in
   `jobs/domain/services/job_url_rules.py` implementing `duplicate_fragment`.
2. Register it in `JOB_URL_DUPLICATE_RULES` (order matters — first match wins).
3. Add unit tests in `apps/backend/tests/jobs/domain/test_job_url_rules.py`.
4. Add API tests in
   `apps/backend/tests/jobs/presentation/api/test_create_job.py`.
5. Document the rule in this file and in `docs/api/jobs/create-job.md`.

---

# Related Documents

- `docs/api/jobs/create-job.md`
- `apps/backend/jobs/domain/services/job_url_rules.py`
