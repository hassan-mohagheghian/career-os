# Prompt 077 - Company Processing Through ProcessingExecution

## Objective

Remove the legacy `/api/pending-companies` endpoints and the legacy company
processing graph. Process companies through the same `ProcessingExecution`
lifecycle and per-node SSE streaming used by jobs, with a two-phase workflow
that mirrors the job processing workflow:

- **Context preparation** (no LLM): `load_company → collect_sources →
  fetch_sources → extract_content → build_context → validate_context →
  persist_context → context_ready | execution_failed`
- **Analysis** (exactly one LLM call): `load_context → prepare_company →
  analyze_company → score_company → recommend_company → summarize_company →
  persist_company → analysis_ready | execution_failed`

`CompanyModel.status` moves to the `JobStatus` vocabulary
(created/pending/queued/processing/processed/failed/cancelled) and the
companies list exposes `latest_processing_execution` like the jobs list.

## Current State

- `root_router.py` holds an inline compat block: `reprocess_company`
  (lines 199-210) and `/api/pending-companies*` (lines 213-324) backed by the
  legacy `SQLAlchemyPendingCompanyRepository` + `CompanyWorker` LangGraph graph
  (`ai/infrastructure/graphs/company/graph.py`).
- `ExecutionRunner` has a `COMPANY_PROCESSING` branch that calls
  `process_company(company_id)` — no workflow_progress, no per-node events.
- `ProcessingQueueService` resolves titles/urls only for `target_type == "job"`.
- The companies list (`companies_v2_router`) exposes a `processing` block from
  `CompanyModel.status` but no `latest_processing_execution`.
- Frontend renders the legacy `CompanyQueueDrawer` and computes `pendingTotal`
  from `usePendingCompaniesQuery`.
- `ExecutionType.COMPANY_PROCESSING = "company_processing"` already exists.

## Implementation Steps

1. Alembic migration `026_add_companies_raw_content.py`: add
   `company.companies.raw_content` (TEXT, nullable) — mirror of jobs
   `raw_description`, used to persist the prepared context between phases.
2. Processing domain company workflow models:
   `CompanyProcessingState`, `CompanyData`, `CompanySource`/`SourceType`,
   `CompanyProcessingContext` (reuse `FetchedContent`, `ExtractedContent`,
   `ContextValidationResult`, `WorkflowProgress`, `WorkflowStep`).
3. Company context preparation workflow (no LLM):
   `company_context_preparation/graph.py` + nodes, mirroring the job prep
   phase. `persist_context` writes `companies.raw_content`.
4. Company analysis workflow (single combined LLM call):
   `company_analysis/graph.py` + nodes, mirroring the job analysis phase.
   `analyze_company` validates against `CompanyCombinedAnalysisOutput`
   (extraction + intelligence + scores). `persist_company` writes the company
   row, `company_intelligence` and sets `status = processed`.
5. `company_workflow_step_mapper.py`: user-facing company step titles; make
   `progress_ops` state-generic (target id via getattr, emit `target_type` /
   `target_id` on step events).
6. Services: `company_context_builder`, `company_context_validator`,
   `company_analysis_prompt`, `company_analysis_validation`,
   `company_analysis_scoring`, `company_analysis_inputs`.
7. Combined prompt `companies/infrastructure/ai/prompts/company/company_combined_analyze.txt`;
   remove legacy `company_extract.txt` / `company_analyze.txt` + duplicate
   copies (loader must resolve one canonical file).
8. Intake: `POST /api/companies` gains `queue` flag → `create_from_intake` +
   create/dispatch `COMPANY_PROCESSING` execution. Rewrite `reprocess_company`
   to create a new execution; delete the `/api/pending-companies*` block.
9. `ExecutionRunner` company branch runs both graphs with workflow_progress;
   company model status synced (`processing` / `processed` / `failed` /
   `cancelled`) via a company status service.
10. `ProcessingQueueService` resolves companies (name, url, links/notes) and
    exposes `target_type` on queue entries.
11. Companies list: attach `latest_processing_execution` (mirror jobs list).
12. Remove legacy company taskiq helpers + `CompanyWorker` usage.
13. Frontend: move `ProcessingDrawer` to `shared/components` with a
    `targetType` prop; delete `CompanyQueueDrawer`; route SSE company events
    to the companies cache; drop `pending*` API/hooks.
14. Docs + tests.

## Testing Requirements

- Backend: state/node/graph tests for both company workflows, mapper, company
  status transitions, `POST /api/companies` queue, reprocess, companies list
  `latest_processing_execution`, queue resolution. Rewrite pending-company
  compat tests in `test_root_router_compat.py`.
- Frontend: shared ProcessingDrawer tests, companies page queue wiring.
- `uv run pytest apps/backend/tests/ -v`; `cd apps/frontend && npx vitest run`.

## Constraints

- All AI calls through `LLMService`. All DB access through SQLAlchemy ORM.
- No new API routes in `entrypoints/api.py`. No `print()`.
- Keep `SQLAlchemyPendingCompanyRepository` (still read by generation history).
- MINOR release (`X.Y+1.0`) with all five version locations in sync.

## Post-Implementation Fixes

- **Alembic chain** — the flat `apps/alembic/versions/026_add_companies_raw_content.py`
  is dead code (not in `version_locations`). The real migration is the per-context
  chain `apps/alembic/company/versions/company_003_add_companies_raw_content.py`,
  which adds `company.companies.raw_content`. `alembic_version.version_num` was
  widened to `varchar(64)` because revision ids can exceed 32 chars.
- **Sequence desync bug** — existing `company_intelligence` / `company_links`
  rows were seeded with explicit ids, so their SERIAL sequences never advanced
  and `autoincrement` inserts collided (`UniqueViolation pk_company_intelligence
  id=2` on `persist_company`). Fixed by migration
  `company_004_sync_sequences`, which re-aligns each sequence to `max(id)+1`.
