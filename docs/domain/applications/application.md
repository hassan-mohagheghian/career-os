# Application (bounded context)

## Purpose

This document describes the **Applications** bounded context: the application record
for a job and its related artifacts. It is the backend behind the Job Application
Workspace (`/jobs/{job_id}/application`).

## Concepts

| Concept | Entity | Description |
| ------- | ------ | ----------- |
| Application | `Application` | The aggregate root. Represents a user's application for a single job. |
| Follow-up | `ApplicationFollowUp` | A scheduled/recorded touch-point (date, note, completion). Minimal, not a CRM. |
| Document | `ApplicationDocument` | A versioned generated artifact (tailored resume, cover letter) stored as markdown. |
| Preparation | `ApplicationPreparation` | A versioned generated plan: hard/soft skill recommendations. |

## Application Status

`ApplicationStatus` is a closed set of strings:

| Value | Meaning |
| ----- | ------- |
| `recommended` | Default on creation; the job is worth applying to. |
| `preparing` | The user is preparing (generating plan/documents). |
| `ready_to_apply` | Artifacts are ready. |
| `applied` | The user applied (may set `applied_at`). |
| `rejected` | Outcome rejected. |
| `withdrawn` | The user withdrew. |

## Document Types

`DocumentType`:

| Value | Execution type |
| ----- | -------------- |
| `tailored_resume` | `application_resume` |
| `cover_letter` | `application_cover_letter` |

The preparation plan maps to `application_preparation`. Generation artifacts are
produced by the Processing bounded context (`docs/ai/application-intelligence.md`) and
persisted here by its workflow persist node.

## Aggregates and Cross-Context References

- The `Application` is the aggregate root; it **owns** its follow-ups, documents and
  preparation plan.
- `job_id` is a **logical reference** to the Jobs context — a plain column, **no
  FK**, no `ondelete` cascade (AGENTS.md rule 15). Referential integrity is enforced
  by the application layer / repositories.
- Database schema: `application` with tables `applications`,
  `application_follow_ups`, `application_documents`, `application_preparations`.

## Business Rules

- An application is created explicitly for a job (`POST /api/applications {job_id}`),
  defaulting to status `recommended`. There is at most one application per job
  (`get_by_job_id`).
- Documents are **versioned**: each successful generation writes a new row (higher
  `version`); edits bump `version`. Preparation likewise stores one row per generated
  version; `get_latest` returns the newest.
- Hard delete: deleting an application removes its follow-ups, documents, preparations
  and its generation executions.
- Deleting a **job** cascades to its application and children (job-delete flow, rule 8).

## Domain Events

See `docs/domain/applications/events.md` for the full EDD catalog.

# Related Documents

- `docs/api/applications/` — API reference.
- `docs/ai/application-intelligence.md` — generation workflow.
- `docs/ux/features/applications/` — UI specs.
