# Job Search

## Purpose

Defines the search capabilities of the Job domain.

Searching is a read-only query operation.

It does not modify Jobs.

It is independent from ProcessingExecution.

Searching is optimized for the Jobs page.

---

# Responsibilities

The Job Search service is responsible for:

- Searching jobs
- Filtering jobs
- Sorting jobs
- Pagination
- Returning lightweight DTOs

It is not responsible for:

- Job processing
- AI generation
- Score calculation
- ProcessingExecution
- Recommendations

---

# Searchable Fields

The following fields participate in free-text search.

## Job Title

Highest priority.

---

## Company Name

Medium priority.

---

## Location

Medium priority.

---

## Keywords

Matches extracted job keywords.

---

## Notes

Optional.

May be enabled later.

---

# Filterable Fields

## Processing Status

```text
created

queued

starting

running

completed

failed

cancelled
```

---

## Job Status

```text
imported

processed

archived
```

---

## Company

Filter by Company.

---

## Location

Filter by location.

---

## Remote

```text
true

false
```

---

## Visa Sponsorship

```text
true

false
```

---

## Score Filters

Supported score filters:

- Overall Score
- Fit Score
- Success Score

Each supports:

- minimum
- maximum

Scores follow the deterministic Job Analysis scoring rules
(`processing/application/services/job_analysis_scoring.py`): clamped 0-100,
`overall = round(fit * 0.6 + success * 0.4)`. Search does not compute scores —
it only filters and sorts on stored values.

---

# Sorting

Supported sorting fields:

- Updated Time
- Created Time
- Company Name
- Job Title
- Overall Score
- Fit Score
- Success Score

### Updated Time

`updated_at` reflects the last time the job changed, including processing
writes. The jobs repository (`sa_job_repository.py`) auto-stamps `updated_at`
on every `update_fields` / `update_status` mutation and on the queued →
processing transition, so a freshly processed job sorts to the top of the
"Updated Time" ordering.

Sorting direction:

```text
ascending

descending
```

NULL handling: every sort follows a **NULLS LAST** policy. Rows where the
sort column has no value (for example a job that has not been scored yet)
sort after all valued rows, in both ascending and descending order.

---

# Pagination

Offset pagination is currently used.

Parameters:

- page
- page_size

Future migration to cursor pagination is supported.

---

# Search Result

A search result returns lightweight Job summaries.

The following large objects are intentionally excluded:

- HTML
- Markdown
- AI output
- Prompt history
- Processing logs
- Timeline
- Recommendations

Those are retrieved through dedicated APIs.

---

# Search Ranking

Search ranking priority:

1. Job title
2. Company name
3. Keywords
4. Location

Future versions may introduce weighted full-text search.

---

# Query Model

The search service receives a single immutable query object.

Example:

```text
JobSearchQuery

page

page_size

query

company_id

processing_status

job_status

location

remote

visa

overall_score_min

overall_score_max

fit_score_min

fit_score_max

success_score_min

success_score_max

sort

order
```

---

# Output Model

The search service returns:

```text
JobSearchResult

items

pagination
```

Each item represents one Job summary suitable for display in the Jobs List.

---

# Future Extensions

Potential future capabilities include:

- Saved searches
- Recent searches
- Advanced boolean search
- Skill filtering
- Salary filtering
- Company type filtering
- Semantic search
- AI-assisted search

These are intentionally out of scope for the current implementation.

---

# Related Documents

- docs/api/jobs/list-jobs.md
- docs/ux/features/jobs/page.md
- docs/workflows/job-processing.md
