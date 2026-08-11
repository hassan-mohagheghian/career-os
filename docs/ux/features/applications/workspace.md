# Job Application Workspace Page

## Purpose

The Job Application Workspace is a dedicated full page at `/jobs/{job_id}/application`
that turns a job into an **application** and supports the "prepare and apply" journey.
It is a **consumer of existing Career Intelligence** — it reads the persisted job
analysis, company intelligence, candidate profile and skill evidence produced by the
existing pipeline and adds application-specific reasoning on top (preparation plan,
tailored resume, cover letter, follow-ups). It never re-runs job/company/candidate
analysis.

## Entry Points

- **Jobs page row action**: an airplane icon button (tooltip "Application") in every
  job row's action cell navigates to `/jobs/{id}/application`.
- **Job Detail drawer**: an "Application" button in the drawer header navigates to
  `/jobs/{id}/application`.

Both are available regardless of processing status.

## Core Principle

The workspace reads intelligence but never duplicates analysis:

| Data | Source endpoint | Used for |
| ---- | --------------- | -------- |
| Job identity + scores + recommendation | `GET /api/jobs/{id}` | Header |
| Job analysis (skills, summary, resume_fit) | `GET /api/jobs/{id}` (analysis) | AI generation context |
| Application record + follow-ups + documents + preparation | `GET /api/applications/by-job/{id}` | All sections |

Application generation (`preparation`, `tailored_resume`, `cover_letter`) is queued via
`POST /api/applications/.../generate` (202) and runs asynchronously through the existing
processing pipeline with live SSE progress.

## High-Level Layout

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Back to Job                                          [Open job posting]│
│ Staff Engineer · Acme GmbH · Berlin                                      │
│ [Recommended] [Apply]             [A+] [Fit 85] [Success 88] [Overall 90]│
├──────────────────────────────────────────────────────────────────────────┤
│ ▸ AI generation in progress ▸ 42% · "Generating tailored resume"        │  ← SSE card (while running)
│                                                                            (completed → "Generated successfully" + Dismiss)
├──────────────────────────────────────────────────────────────────────────┤
│ APPLICATION                                                            │
│  Status [Recommended ▾]    Applied at [ 2026-08-11 ]                     │
│  FOLLOW-UPS                                                              │
│  ☑ Follow up after interview · Sep 1, 2026                        [🗑]   │
│  [ Note (e.g. follow up after interview) ][ date ] [Add]                 │
├──────────────────────────────────────────────────────────────────────────┤
│ PREPARATION                                                        [⚡ Gen]│
│  Hard skills                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐                      │
│  │ Kubernetes · Missing │  │ Kafka · Low   [high] │                      │
│  │ Why / What to learn  │  │ Why / How to practice│                      │
│  │ / How to practice /  │  │ ...                  │                      │
│  │ resources / effort   │  └──────────────────────┘                      │
│  └──────────────────────┘                                                │
│  Soft skills  (same card grid)                                           │
├──────────────────────────────────────────────────────────────────────────┤
│ DOCUMENTS                                                                │
│ ┌────────────────────────────┐  ┌────────────────────────────┐           │
│ │ TAILORED RESUME v2  [copy] │  │ COVER LETTER v1    [copy]  │           │
│ │ [download][edit][🗑][Regen]│  │ [download][edit][🗑][Regen] │           │
│ │ │ markdown preview │       │  │ │ markdown preview │       │           │
│ └────────────────────────────┘  └────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```text
app/jobs/[job_id]/application/page.tsx        (dynamic route, first dynamic route)
└── widgets/job-application-workspace
    └── features/job-application
        ├── ApplicationWorkspace        → job + application queries, layout, sections
        │   ├── WorkspaceHeader         → back link, identity, status/recommendation badges, scores
        │   ├── GenerationProgress      → SSE generation status card
        │   ├── ApplicationSection      → titled card wrapper
        │   ├── ApplicationTracker      → status select, applied date, follow-ups
        │   ├── PreparationPlan         → hard/soft skill cards + generate button
        │   └── ApplicationDocuments    → resume / cover letter cards
        └── hooks/useApplicationGeneration → SSE subscription for the application
```

## States

### No application yet (empty state)

```text
┌──────────────────────────────────────────────────────────────┐
│                        [✈]                                   │
│                     No application yet                       │
│  Track this job as an application to prepare, generate a     │
│  tailored resume and cover letter, and schedule follow-ups.  │
│                     [Create Application]                     │
└──────────────────────────────────────────────────────────────┘
```

Clicking **Create Application** calls `POST /api/applications { job_id }` (201, status
`recommended`) and the workspace renders the three sections.

### Generation running

An in-place progress card (see `GenerationProgress`) appears above the sections while an
application execution is `queued`/`running` (driven by SSE), showing the current workflow
step title and percent. On `completed`/`failed` the application query is refetched so the
new document/preparation appears; the card shows the result and a **Dismiss** button.

## Behaviors

| Element | Behavior |
| ------- | -------- |
| Back to Job | `router.push('/jobs?job={id}')`; the Jobs page opens the detail drawer for that job. |
| Status select | `PATCH /api/applications/{id}` with the chosen status; list: recommended, preparing, ready_to_apply, applied, rejected, withdrawn. |
| Applied at | Native date input; `PATCH` with `applied_at` (or `null` to clear). |
| Follow-ups | Add (note + optional date), toggle done, delete — see `application-tracker.md`. |
| Preparation Generate | `POST /api/applications/{id}/preparation/generate` → 202, SSE progress, refetch on completion. Label becomes **Regenerate** once a plan exists. |
| Document Generate | `POST /api/applications/{id}/documents/{tailored_resume\|cover_letter}/generate` → 202, SSE progress, refetch on completion. Label becomes **Regenerate** once the document exists. |
| Document actions | Copy, download as `.md`, edit in place (textarea + Save/Cancel), delete. |

## Loading States

- Job + application queries in flight → centered spinner.
- Generate buttons show a spinner and are disabled while queuing.
- Missing job (404) → "Unable to load the job."

## Error States

- Job fetch failure → "Unable to load the job."
- Generation failure → the `GenerationProgress` card shows the error message from the
  SSE `execution.failed` event; toast "Failed to queue …" on dispatch errors.
- Creating an application that already exists → backend 409/400 → error toast.

## Responsive Behavior

- Scores and status row wrap; the document grid collapses to one column below `xl`.
- `max-w-5xl` centered container.

# Related Documents

- `docs/ux/features/applications/application-tracker.md`
- `docs/ux/features/applications/preparation-plan.md`
- `docs/ux/features/applications/application-documents.md`
- `docs/ux/flows/applications/prepare-and-apply.md`
- `docs/ux/flows/applications/generate-application-artifacts.md`
