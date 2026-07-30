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

---

# Processing Execution

Only the latest execution is returned.

Fields:

- id
- status
- started_at
- finished_at

Execution details are retrieved separately.

---

# Processing Status

Supported values

- Created
- Queued
- Starting
- Running
- Completed
- Failed
- Cancelled

---

# Row Actions

The Job List determines available actions from the Processing Status.

Examples

Created

- Process V2
- Legacy Process
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
