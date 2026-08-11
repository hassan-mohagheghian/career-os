# Prompt 140 - Job Application Workspace

## Objective

Implement the Job Application Workspace (spec: `implementation-history/139_feature_job_application.md`): a dedicated full page at `/jobs/{job_id}/application` that reuses existing Job / Company / User / Skill intelligence to support applying to a job.

Core principle: the workspace is a **consumer of existing Career Intelligence** — never a second analysis pipeline. Preparation, tailored resume and cover letter generation read the persisted job analysis, company intelligence, candidate profile and skill evidence already produced by the existing pipeline.

## Decisions

- **Async AI generation** via the existing processing pipeline: new `ExecutionType`s, LangGraph workflows, TaskIQ dispatch, SSE progress (consistent with job/company/candidate processing).
- **Explicit application creation**: the workspace shows an empty state with a "Create Application" button; the record defaults to status `recommended`.
- **New bounded context `applications`** (PostgreSQL schema `application`): `applications`, `application_follow_ups`, `application_documents`, `application_preparations`. Cross-context refs (`job_id`) are plain columns — no FKs (AGENTS.md rule 15).
- Three generation artifacts, each its own `ExecutionType`: `application_preparation` (hard/soft skill plan), `application_resume`, `application_cover_letter`.

## Current State (after investigation)

- Job intelligence: `jobs` row + canonical `job_analysis` row (`payload` JSON: fields, scores, scores_explanation, recommendation, apply_reason, summary{summary,resume_fit,note}, skills[{name,category,level,status matched|missing|low,evidence}], insights). Served by `GET /api/jobs/{job_id}`.
- Company intelligence: `companies` + `company_intelligence` (overview, technology_analysis, culture_analysis, ...) served by `GET /api/companies/{id}`.
- User intelligence: `GET /api/candidates/profile` (name, title, headline, summary, skills[level,confidence,years,evidence], experiences, projects, educations, certificates, interests, languages) + `candidate_sources.raw_text` (resume/linkedin).
- AI infra: `LLMService` (the only entry point), prompt builders under `processing/application/services/`, LangGraph workflows under `processing/application/workflows/`, graphs wired in `processing/infrastructure/workflow/assembly.py`, execution runner dispatches by `ExecutionType`.
- Frontend: FSD (`src/entities`, `src/features/jobs-v2`, `src/widgets/jobs-page-v2`), App Router pages at root `app/`, no dynamic routes yet, shadcn ui kit, React Query, `useProcessingEvents` SSE.
- Nothing application-related exists yet (no cover letter / follow-up / applied_at code anywhere).

## Changes

### Backend — applications bounded context

- `applications/domain/`: entities (`Application`, `ApplicationFollowUp`, `ApplicationDocument`, `ApplicationPreparation`), events, `ApplicationEventPublisher` + `InMemoryEventCollector`, repository interfaces.
- `applications/application/services/`: `ApplicationService` (get-by-job, create, update status/applied_at), `FollowUpService` (add/complete/delete), `DocumentService` (update content, delete version). Emit domain events (best-effort).
- `applications/infrastructure/`: ORM models (schema `application`), SA repositories, mappers, lazy `__init__` exports.
- `applications/presentation/api/applications_router.py` + schemas, registered in `root_router.py` under `/api/applications`.

### Backend — AI generation

- New `ExecutionType`s: `APPLICATION_PREPARATION`, `APPLICATION_RESUME`, `APPLICATION_COVER_LETTER`.
- `processing/application/workflows/application_intelligence/`: shared state, nodes (load_context → generate → persist → ready|failed), graph parametrized by intent.
- `processing/application/services/application_intelligence_inputs.py` (grounded context assembly reusing `job_analysis_inputs.py` builders) and `application_intelligence_prompts.py` (preparation / resume / cover letter prompt + JSON output schemas).
- Wire graphs in `assembly.py`, dispatch in `execution_runner.py`.

### Backend — API + integration

- `GET /api/applications/by-job/{job_id}` (404 when none), `POST /api/applications` {job_id} (201, default status `recommended`), `PATCH /api/applications/{id}` {status?, applied_at?}, follow-ups CRUD, `POST .../preparation/generate`, `POST .../documents/{type}/generate` (202 + execution_id), `PATCH/DELETE .../documents/{id}`.
- Job hard-delete cascade: `delete_job` also deletes the application + children + application generation executions (rule 8).
- `dependencies.py` DI + `SCHEMAS` registration in `sqlalchemy_config.py`.

### DB migration

Autogenerate the `application` schema (`ALEMBIC_TARGET_SCHEMA=application`, `--version-path apps/alembic/application/versions`, `--branch-label application`), tune the generated file, then a merge migration to restore a single head. Verify `history` / `heads` / upgrade + downgrade round-trip.

### Frontend

- Route `app/jobs/[job_id]/application/page.tsx` (first dynamic route) → `src/widgets/job-application-workspace` → `src/features/job-application/` components + `src/entities/application/` (types + api).
- Application entry points: `JobActions.tsx` row action + `JobDetailDrawer.tsx` header button → `router.push('/jobs/{id}/application')`. Header "← Back to Job" → `/jobs?job={id}`.
- Workspace sections: header (job identity + scores/recommendation + status), tracker (status select, applied date, follow-ups), preparation (hard/soft cards), documents (view/edit/regenerate/download/copy). Generation progress via `useProcessingEvents` + SSE; refetch application on execution completion.

### Docs (rule 13 — mandatory)

- `docs/ux/features/applications/workspace.md`, `application-tracker.md`, `preparation-plan.md`, `application-documents.md` (ASCII wireframes + Mermaid), `docs/ux/flows/applications/prepare-and-apply.md` + `generate-application-artifacts.md` (Mermaid), update `docs/ux/README.md` + `DESIGN.md`.
- `docs/domain/applications/application.md` + `events.md`, `docs/api/applications/*`, `docs/ai/application-intelligence.md`, architecture docs + root `API.md`/`ARCHITECTURE.md`.

## Testing Requirements

- Backend: pytest for domain/services/repositories, API endpoints, prompt builders (grounding, no re-analysis), workflow persist nodes (mock LLM), job-delete cascade.
- Frontend: vitest for workspace components and hooks; run `npm run lint` + `npm run typecheck`.
- Full: `uv run pytest apps/backend/tests/ -v` and `cd apps/frontend && npx vitest run`.

## Constraints

- All AI calls through `LLMService` (rule 1); SQLAlchemy ORM only (rule 2); per-context router (rule 10); structlog, no `print` (rule 11); no cross-context FKs (rule 15); domain events defined/emitted/documented, in-memory collector only (rule 16); version bump in all five places (rule 12).
- No re-analysis of job/company/user — only application-specific reasoning on top of existing structured intelligence.
- Do not add Interview functionality; do not build a CRM (follow-ups stay minimal).
