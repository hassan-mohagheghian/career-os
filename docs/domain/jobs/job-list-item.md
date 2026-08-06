# Job List Item

## Purpose

Defines the lightweight Job representation returned by the Jobs List API.

This object is optimized for browsing.

It is intentionally different from the complete Job entity.

---

# Responsibilities

A Job List Item should contain only the information required to render one row in the Jobs List.

It must not include:

- Raw HTML
- Markdown
- Prompt history
- Processing logs
- Timeline
- AI output
- Parsed documents

Those are loaded through dedicated APIs.

---

# Structure

JobListItem

- id
- title
- company
- location
- remote
- visa_sponsorship
- pinned
- recommendation
- processing_status
- latest_processing_execution
- scores
- updated_at
- created_at

---

# Company

Company information contains only:

- id
- name
- logo (optional)

---

# Scores

Scores displayed in the Jobs List

- Overall
- Fit
- Success

All scores are normalized to 0–100.

Scores are produced by the deterministic Job Analysis scoring rules
(`processing/application/services/job_analysis_scoring.py`):
`overall = round(fit * 0.6 + success * 0.4)`, clamped to 0-100.

---

# Pinned

A boolean flag (`pinned`, default `false`) marking the job as pinned by the
user.

It is independent of the analysis pipeline and is toggled exclusively through
`PUT /api/jobs/{job_id}/pinned`. The Jobs List can be filtered to show only
pinned jobs (`GET /api/jobs/list?pinned=true`).

---

# Recommendation

The analysis recommendation (`apply` / `consider` / `skip`), derived
deterministically from the overall score: `apply` ≥ 80 / `consider` ≥ 60 /
else `skip`.

Exposed as a single read-only field on the list item (batch-loaded per page,
not N+1). Jobs without a completed analysis have `recommendation = null` and
render no badge in the row. The full `analysis` block (with `apply_reason`,
`scores_explanation`, etc.) is still only exposed on the job detail endpoint
(`GET /api/jobs/{job_id}`).

The Jobs List can additionally be filtered by recommendation
(`GET /api/jobs/list?recommendation=apply`); jobs without an analysis row never
match that filter.

---

# Processing Execution

Only the latest execution is returned.

Fields:

- id
- status
- started_at
- finished_at

Execution details are retrieved separately.

A job that has never been processed has `latest_processing_execution = null`
and `job_status = null` — there is no fallback to the legacy `jobs.status`.

---

# Processing Status

Supported values

- Queued
- Starting
- Running
- Completed
- Failed
- Cancelled

The status comes from the job's **latest** `processing_execution` row
(`created_at` desc), not from the legacy `jobs.status` column. When the list
is filtered by processing status, only the latest execution per job is
considered.

The special filter value `none` matches jobs that have **no** processing
execution at all. When the list is sorted by `status`, rows are grouped by this
same latest-execution status and jobs with no execution always sort last, in
both ascending and descending order.

---

# Row Actions

The Job List determines available actions from the Processing Status.

Examples

No execution (never processed)

- Process
- View Details

Running

- View Progress
- View Details

Completed

- View Results
- Reprocess

Failed

- Retry
- View Error

---

# Design Rules

Job List Items must remain lightweight.

The backend should never return nested domain aggregates.

The object is a read model optimized for UI rendering.

---

# Related Documents

- docs/api/jobs/list-jobs.md
- docs/ux/features/jobs/job-row.md
