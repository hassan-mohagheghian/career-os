# Prompt 133 - Remove Resume / Cover Letter Generation

## Objective

Remove the **Resume Generation** feature (AI-tailored resumes, cover letter
generation, and the legacy "real-time progress with WebSocket updates" and
"LinkedIn profile integration" bullets) from the README, and ensure no
resume/cover letter **generation** remains anywhere in the code or docs.

Resume / LinkedIn as **input** is untouched and remains a first-class feature:
`candidate.candidate_sources` rows (`source_type` `resume` / `linkedin`),
uploaded via `POST /api/candidates/sources`, PII-masked at save time, extracted
into the canonical candidate profile, and fed into job analysis as labeled
context.

## Current State

- README advertised "AI-powered resume tailoring and cover letter generation",
  "real-time progress with WebSocket updates", "LinkedIn profile integration",
  a `Resume` nav entry and a `### Resume Generation` section, plus a stale
  "Legacy Socket.IO events" line and a `FastAPI app + SocketIO + CLI` comment.
- `apps/backend/ai/infrastructure/parsers.py` still defined a dead
  `ResumeGenerationOutput` class (no callers left) and imported `Any` only for
  it.
- Docs referenced `/api/resumes` and `/api/linkedin` endpoints (removed long
  ago) as the current profile-document API, and described resume/cover
  generation graphs, workers, entities and pipelines as if they still existed.
- `apps/frontend/src/shared/components/WorkflowTerminal.tsx` mapped the `save`
  step to the long-gone `step_resume` column (the current column is `step_db`).

## Implementation Steps

## 1. README.md

- Removed "resume generation" from the intro description.
- Removed the `Resume` box from the architecture diagram.
- Removed the "Resume — Resume/cover letter generation" nav entry.
- Deleted the `### Resume Generation` section (3 bullets).
- Removed the stale "Legacy Socket.IO events" line.
- Changed `entrypoints/` "FastAPI app + SocketIO + CLI" → "FastAPI app + CLI".

## 2. Backend

- `apps/backend/ai/infrastructure/parsers.py`: deleted the dead
  `ResumeGenerationOutput` class and the now-unused `Any` import. No behavior
  change (no callers).
- Verified: no `step_resume` / `step_cover` columns or references remain in
  code. `processing_executions.workflow_progress` + the re-purposed Generation
  History feature (`generation_history` table, `GenerationHistoryRepository`,
  `dashboard_router.get_generation_history`) read Job/Company models only and
  are **kept**.

## 3. Frontend

- `apps/frontend/src/shared/components/WorkflowTerminal.tsx`: `save` step now
  maps to `step_db` (was the removed `step_resume` column).

## 4. Docs

- `API.md`: replaced the stale `Resumes /api/resumes` and `LinkedIn Profiles
  /api/linkedin` endpoint rows with `Candidate Profile /api/candidates/sources`
  (Resume / LinkedIn upload as analysis input); rewrote the "Profile Documents
  (Resume + LinkedIn)" section → "Candidate Profile Sources (Resume + LinkedIn)"
  documenting `GET/POST /api/candidates/sources`, `versions`, `analyze`.
- `docs/api/api-design.md`: removed `resumes_router` from the router
  organization and the entire `### Resumes` endpoint table (incl.
  `/api/resumes/{id}/generate-cover`).
- `docs/api/jobs/delete-job.md` (+ `docs/ux/features/jobs/delete-job.md`,
  `docs/ux/flows/jobs/delete-job.md`): dropped the stale "resume" related-data
  mention (job delete removes `job_analysis` + summary + executions).
- `CONTEXT.md`: removed resume-generation references from intro, target users,
  core concepts, and scope; added the Candidate Profile input concept.
- `DOMAIN.md`: replaced the `Resume` / `Generation` entity sections with a
  `CandidateSource` section; rewrote the Resume/Cover Generation Pipeline and
  Flow into the Candidate Source Upload Flow; updated the extraction description
  to read `candidate.candidate_sources` (not `job.resumes`).
- `ARCHITECTURE.md` (root): `Skills/Resume` → `Skills/CandProfile`; added
  `candidates` to the bounded-context list.
- `docs/architecture/ARCHITECTURE.md`: `resumes` entity row → `candidate_sources`;
  nav + diagram updates; `candidates/` context in the backend structure;
  Resume/Cover Generation section marked removed; dropped the
  `generation:update` WebSocket event and python-socketio mention.
- `docs/architecture/backend-structure.md`, `folder-structure.md`,
  `code-ownership-map.md`, `context-boundaries.md`,
  `bounded-context-analysis.md`, `workflow-state.md`,
  `microservice-evolution.md`: replaced the Resume context / `resumes_router` /
  `resume_service` / `resume_worker` / `generate_resume` references with the
  Candidates context and `candidate_sources`.
- `docs/ai/graphs.md`: replaced the Resume Generation / Cover Letter Generation
  graph specs with a "(removed)" note.
- `docs/ai/prompts.md`, `docs/ai/prompt-registry.md`: legacy resume/cover
  letter `.txt` prompt files marked removed (they no longer exist on disk).
- `docs/adr/004-code-ownership-refactoring.md`,
  `docs/adr/017-langgraph-platform.md`: the Resume context and the
  resume/cover-letter LangGraph graphs marked removed.
- This file.

## 5. Verification

Backend:

    uv run pytest apps/backend/tests/ai/ apps/backend/tests/jobs/ -q
    uv run pytest apps/backend/tests/ -v -k "parsers or ai or generation"

Frontend:

    cd apps/frontend && npx vitest run

## Testing Requirements

- All frontend tests pass (`513 passed`).
- Backend AI + jobs suites pass (`398 passed`); full targeted
  parsers/ai/generation selection passes (`377 passed`).
- `tsc --noEmit` has no errors for the changed `WorkflowTerminal.tsx`.

## Important Constraints

- Resume / LinkedIn as **input** (candidate sources, adapters, extraction,
  job-analysis context) is preserved — only **generation** is removed.
- The re-purposed Generation **History** feature (processing history read from
  Job/Company models) is kept; only resume/cover generation references were
  removed around it.
- No DB migration, no version bump (batched at release, per repo convention).
