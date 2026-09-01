# Prompt 201 - LinkedIn Easy Apply detection and display

## Objective

Detect LinkedIn Easy Apply jobs during processing and display a visible "Easy Apply" tag in the job list and detail drawer so users can quickly identify jobs they can apply to directly on LinkedIn without leaving the platform.

## Current State

- **Job model** (`apps/backend/jobs/infrastructure/models/job_model.py`): no `easy_apply` field. Has boolean-style Integer columns: `deleted`, `pinned`, `dismissed`.
- **Job entity** (`apps/backend/jobs/domain/entities/job.py`): no `easy_apply` parameter.
- **Mappers** (`apps/backend/jobs/infrastructure/mappers.py`): `job_model_to_dict` maps all model fields.
- **Alembic** (`apps/alembic/job/versions/`): latest job migration is `job_007_add_tags`. New migration must be `job_008_add_easy_apply`.
- **Context builder** (`apps/backend/processing/application/services/job_context_builder.py:21-49`): builds `combined_text` from extracted content. The extracted clean text from LinkedIn pages may contain "Easy Apply" when the job offers LinkedIn's built-in apply flow.
- **PersistContextNode** (`apps/backend/processing/application/workflows/job_context_preparation/nodes/persist_context_node.py`): calls `job_service.persist_prepared_context(job_id, combined_text)`.
- **JobService** (`apps/backend/jobs/application/services/job_service.py:30-41`): `persist_prepared_context` writes `raw_description` and `description`.
- **API schemas** (`apps/backend/jobs/presentation/api/schemas/jobs_v2.py`): `JobListItemSchema` (line 90) and `JobDetailResponseSchema` (line 250) have no `easy_apply`.
- **Router** (`apps/backend/jobs/presentation/api/jobs_v2_router.py`): `_v2_job_to_schema` (line 257) and `_job_detail_payload` (line 518) build responses.
- **Frontend types** (`apps/frontend/src/entities/job/types.ts`): `JobListItem` (line 111) and `JobDetail` (line 264) have no `easy_apply`.
- **JobRow** (`apps/frontend/src/features/jobs-v2/components/JobRow.tsx`): renders Remote/Visa chips inline in the location column (lines 82-91).
- **JobDetailDrawer** (`apps/frontend/src/features/jobs-v2/components/JobDetailDrawer.tsx`): `JobDetailContent` renders a 2-column grid with DetailRow items (lines 594-637).

## Changes

### 1. Domain + ORM model

- `job_model.py`: add `easy_apply: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True, default=None)` after `session_id`.
- `job.py` entity: add `easy_apply: int | None = None` param, assign in `__init__`, include in `to_dict()` and `from_dict()`.
- `mappers.py`: add `"easy_apply": model.easy_apply` to `job_model_to_dict`.

### 2. Alembic migration

- Create `apps/alembic/job/versions/job_008_add_easy_apply.py` via `uv run alembic revision --autogenerate -m "add easy_apply" --version-path apps/alembic/job/versions --branch-label job` (with `ALEMBIC_TARGET_SCHEMA=job`). Then tune: add `CREATE SCHEMA IF NOT EXISTS job`, guard with `has_table`/`get_columns`.

### 3. Detection in processing pipeline

- `job_context_builder.py`: after building `combined_text`, scan extracted content texts for "easy apply" (case-insensitive regex `r'\beasy\s+apply\b'`). Store result as `easy_apply` in `metadata`.
- `persist_context_node.py`: read `context.metadata.get("easy_apply")` and pass to `job_service.persist_prepared_context(job_id, combined_text, easy_apply=...)`.
- `job_service.py`: `persist_prepared_context` accepts `easy_apply: bool | None = None` and passes it to `update_fields`.

### 4. API schemas

- `jobs_v2.py`: add `easy_apply: bool | None = None` to `JobListItemSchema` and `JobDetailResponseSchema`.

### 5. Router mapping

- `_v2_job_to_schema`: map `easy_apply=bool(job_dict.get("easy_apply"))`.
- `_job_detail_payload`: map `easy_apply=bool(job_dict.get("easy_apply"))`.
- `get_job_detail`: map `easy_apply=bool(job_dict.get("easy_apply"))`.

### 6. Frontend types

- `types.ts`: add `easy_apply: boolean | null` to `JobListItem` and `JobDetail`.

### 7. Job list UI

- `JobRow.tsx`: add Easy Apply chip in the location column (after Visa chip), using `bg-sky-500/10 text-sky-500 border border-sky-500/20` styling, text "Easy Apply".

### 8. Job detail drawer

- `JobDetailDrawer.tsx`: add `easy_apply` DetailRow in the left column grid (after Visa), showing a styled "Easy Apply" badge when true.

### 9. Docs

- `docs/ux/features/jobs/job-row.md`: add "Easy Apply badge" to Displayed Information section.
- `docs/ux/features/jobs/page.md`: add Easy Apply to the Job Details Drawer wireframe section.

## Testing Requirements

- Backend: `uv run pytest apps/backend/tests/processing/application/ -v` and `uv run pytest apps/backend/tests/jobs/ -v`.
- Frontend: `cd apps/frontend && npx vitest run && npm run lint && npm run typecheck`.
- Alembic: `uv run alembic history -r base:heads` and `uv run alembic heads` (single head).

## Constraints

- Respect AGENTS.md rules: no raw SQL, no cross-context FKs, frontend TS only, docs in sync.
- Boolean column uses Integer (0/1/NULL) matching existing convention (`deleted`, `pinned`, `dismissed`).
- Detection uses case-insensitive regex on extracted content text only (not notes).
- Migration must be in `apps/alembic/job/versions/` with `CREATE SCHEMA IF NOT EXISTS job`.
