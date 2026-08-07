# Prompt 101 - Candidate Processing Workflow

## Objective

Implement Phase 101 of the Candidate Profile Domain (master spec
`098_feature_candidate_profile_domain.md`): the `candidate_processing` two-phase
LangGraph workflow (source preparation + extraction/merge) driven by the
`ProcessingExecutionRunner`, plus the deterministic merge/diff engine and the
`CandidateProfileVersion` timeline. Also wire the Candidates bounded context's
domain events through an in-memory event collector (EDD, incremental — no
pub/sub transport yet) and document them.

## Current State

- Phase 099 delivered the Candidates bounded context (entities, repositories,
  SQLAlchemy + migration `candidate_001`, DI wiring, 52 tests).
- Phase 100 delivered source adapters (`resume`, `linkedin`, stubs) and the
  single-source extraction layer: `CandidateExtractService.process()/
  extract_and_store()` with LLM call + validation + one retry, skill resolution
  via the skills context, child mapping with evidence, and source bookkeeping.
- `CandidateExtractService` currently persists each source independently
  (`update_core` + `replace_children` + record source). No merge, no versions.
- `candidates/domain/events.py` defines 7 events but nothing emits them.
- Processing wiring points confirmed: `processing/domain/enums.py::ExecutionType`,
  `processing/infrastructure/runner/execution_runner.py::_run_workflow`,
  `processing/infrastructure/workflow/assembly.py`,
  `processing/infrastructure/workflow/__init__.py`,
  `processing/application/workflows/progress_ops.py` (target_type dispatch),
  `processing/application/workflows/company_workflow_step_mapper.py` (template).

## Scope (this phase)

### 1. Merge engine (pure domain service)

`candidates/domain/services/profile_merge_service.py` (new; add
`candidates/domain/services/__init__.py`):

- `ProfileDiff` — per-section lists of `added` / `updated` / `removed` items.
- `merge(current: dict, incoming: dict) -> MergeResult` where `MergeResult`
  carries `merged` (full profile dict) and `diff` (ProfileDiff summary).
- Natural-key rules (deterministic, idempotent):
  - Core: incoming non-empty value wins (name/title/headline/summary/location).
  - skills keyed by `skill_id` (fallback: normalized name); keep max level,
    max confidence, max years, union evidence sources, non-empty category/last_used.
  - experiences keyed by `(company, role)`; projects by `name`; educations by
    `(institution, degree)`; certificates by `name`; interests and languages by
    `name`. Incoming item fills empty fields; existing evidence is preserved.
  - Removed = items in current but not in incoming.

### 2. Service refactor (single persistence path)

`CandidateExtractService`:

- `extract(content: SourceContent) -> dict | None` — pure: LLM call (validate +
  retry once), skill resolution, child mapping, version/prompt/schema metadata.
  Returns `None` when the source is skipped (empty / already processed).
- `merge_and_persist(extracted: list[dict]) -> dict` — the only persistence path:
  merge all extracted payloads into the current profile (or create it), persist
  via `update_core` + `replace_children`, create a `CandidateProfileVersion`,
  record each source as processed. Returns summary (profile_id, version,
  source_versions, change_summary, events).
- `process()` / `extract_and_store()` become thin wrappers (kept for compat with
  Phase-100 tests / direct usage).
- **Version rule**: fresh profile (no version yet) → snapshot v1 with
  `profile.version = 1`; every subsequent merge → version + 1, snapshot carries
  `source_versions` map and a `change_summary` derived from `ProfileDiff`.

### 3. EDD — event publisher port (incremental, NO pub/sub)

- `candidates/domain/event_publisher.py`: `CandidateEventPublisher` ABC port with
  `publish(event: DomainEvent)`; default `InMemoryEventCollector` that records
  events (`.events` list, `take_events()`).
- Service emits domain events through the port during operations (best-effort,
  never changes behavior): `CandidateProfileCreated`, `CandidateProfileUpdated`,
  `CandidateSourceAdded`, `CandidateSourceUpdated`, `CandidateMergeCompleted`,
  `CandidateVersionCreated`, `CandidateSkillInferred` (new skill merged in),
  plus new `CandidateSourceSkipped`.
- Events are collected in-memory and returned in results for observability and
  tests. Redis/SSE/outbox transport is explicitly deferred (documented).

### 4. Workflows

New processing application files:

- `processing/domain/workflow/candidate_processing_state.py`:
  `CandidateProcessingState` — `execution_id`, `profile_id`, `profile` (dict),
  `pending_sources` (list of source-type/version dicts), `extracted_sources`,
  `merge_result`, `errors`, `workflow_progress`, `status`.
- `processing/application/workflows/candidate_source_preparation/` — graph +
  nodes `load_profile`, `prepare_sources`, `sources_ready`, `execution_failed`.
  NO LLM. `load_profile` loads via `ICandidateProfileRepository.get_or_create_current`,
  `prepare_sources` lists sources via `ICandidateSourceRepository.list_for_profile`
  and filters `status == "pending"` into `pending_sources` (latest version per
  source type).
- `processing/application/workflows/candidate_processing/` — graph + nodes
  `extract`, `merge`, `analysis_ready`, `execution_failed`. `extract` runs one
  `CandidateExtractService.extract()` per pending source (fake-friendly);
  `merge` calls `merge_and_persist` once. Per the approved decision: a source
  extraction failure **fails the whole run**.
- `processing/application/workflows/candidate_workflow_step_mapper.py` —
  `CandidateWorkflowStepMapper` with `WORKFLOW_ID = "candidate_processing"`,
  same `(step_id, step_title, displayable)` contract as
  `CompanyWorkflowStepMapper`.

### 5. Processing wiring

- `processing/domain/enums.py`: add `ExecutionType.CANDIDATE_PROCESSING =
  "candidate_processing"`.
- `processing/application/workflows/progress_ops.py`: dispatch
  `target_type == "candidate"` to `CandidateWorkflowStepMapper`.
- `processing/infrastructure/workflow/assembly.py`: add
  `build_candidate_source_preparation_graph(session)` and
  `build_candidate_processing_graph(session)` (SA repos + `CandidateExtractService`
  + `InMemoryEventCollector`).
- `processing/infrastructure/workflow/__init__.py`: export both builders.
- `execution_runner.py::_run_workflow`: add `CANDIDATE_PROCESSING` branch
  (mirror company branch; `target_type="candidate"`, `target_id=profile_id`).
- `dependencies.py`: no changes required for this phase (workflow uses its own
  assembly). Keep `get_candidate_extract_service` as-is.

### 6. Tests (TDD)

- Merge engine unit tests: natural-key rules, diff classification,
  idempotency, empty-current and empty-incoming.
- Service tests: `extract()` purity; `merge_and_persist()` single-path
  persistence; version bump (v1 → v2); `source_versions` map; `change_summary`;
  event emission via collector (created/updated/merge/source/version/skill/skipped);
  existing Phase-100 tests stay green.
- Integration: real DB round-trip — resume + linkedin merge, version snapshot
  persisted, sources `processed`.
- Graph E2E: `candidate_source_preparation` + `candidate_processing` with fake
  repos + fake LLM → `processed` sources, profile version bumped, workflow
  completed; failure path → `execution_failed` + `ExecutionStatus.FAILED`.
- Runner wiring: `_run_workflow` candidate branch dispatches both graphs
  (mock-based, like `test_dispatch_and_runner.py`).
- Step mapper + `progress_ops` dispatch tests.

### 7. Docs

- `docs/domain/candidates/events.md` (EDD catalog — trigger, payload, when it
  fires, consumers; pub/sub transport deferred note).
- `DOMAIN.md` (merge/versioning rules), `ARCHITECTURE.md` (processing row).
- `docs/README.md` / `docs/domain/README.md` index entry if one exists.

## Constraints

- No API routes in this phase (trigger/API deferred to Phase 103).
- Fail whole run on extraction failure (approved decision).
- No pub/sub / Redis / SSE / outbox for candidate events (approved EDD scope).
- No new DB migration needed (candidate schema already exists).
- Follow AGENTS.md rules 1, 2, 10, 11, 13 (mermaid where helpful), 15, 16.
