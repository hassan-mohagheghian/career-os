# Prompt 100 — Candidate Profile Domain: Source Adapters + Structured Extraction

## Objective

Phase 2 of the Canonical Candidate Profile Domain (master spec:
`098_feature_candidate_profile_domain.md`). Add source adapters that read raw
profile documents (resume / LinkedIn) from `job.resumes`, and a single
`candidate.extract` LLM call that turns raw text into a structured profile via
`LLMService.generate_structured` (versioned prompt/schema + strict validation),
resolving skills through the skills context `resolve_skill` and persisting
explicit-vs-inferred, confidence, and evidence. No processing workflow, no merge
engine, no API routes yet (Phases 101–103).

## Current State

Phase 099 shipped the `candidates` context with domain entities, value objects,
repositories (interfaces + SQLAlchemy impls), ORM models in the `candidate`
schema (`candidate_001` migration), DI factories, and domain events. There is no
adapter layer, no extraction logic, and nothing calls `LLMService` for the
candidate profile. `CandidateProfileUpdated` etc. are defined but unwired.

## Scope

- New `apps/backend/candidates/application/` layer:
  - `adapters/base.py` — `SourceContent` (source_type, raw_text, version) +
    `CandidateSourceAdapter` ABC (`source_type` class attr + `fetch()`).
  - `adapters/resume_adapter.py` — `ResumeAdapter(IResumeRepository)` reads the
    latest `original_*` row from `job.resumes`.
  - `adapters/linkedin_adapter.py` — `LinkedInAdapter(IResumeRepository)` reads
    the latest `linkedin_*` row.
  - `adapters/github_adapter.py`, `adapters/portfolio_adapter.py` — stubs
    (implement the ABC, return `None` — not wired to a provider yet).
  - `adapters/__init__.py` — `build_adapter(source_type, resume_repo)` registry.
  - `services/candidate_extract_prompt.py` — versioned constants +
    `build_candidate_extract_output_schema()` + `build_candidate_extract_prompt()`.
  - `services/candidate_extract_validation.py` — strict pydantic model mirroring
    the schema (coercing validators, clamped confidence).
  - `services/candidate_extract_service.py` — `CandidateExtractService`
    orchestrating adapter fetch → LLM call (validate + retry once) → skill
    resolution → mapping → persistence (core + children + source row).
- No schema changes (no new migration — `candidate` schema already has all
  tables Phase 100 needs). If a migration is ever needed, follow the
  autogenerate-first convention in `docs/database/alembic-guide.md`.

## Design

### Adapters

```python
@dataclass(frozen=True)
class SourceContent:
    source_type: str
    raw_text: str
    version: int

class CandidateSourceAdapter(ABC):
    source_type: str = ""
    @abstractmethod
    def fetch(self) -> SourceContent | None:
        """Return the latest raw content + version, or None when unavailable."""
```

`ResumeAdapter` / `LinkedInAdapter` wrap `IResumeRepository` (from the jobs
context — cross-context read, same `job.resumes` table the `/api/resumes` and
`/api/linkedin` endpoints use). They derive raw text + version from the latest
row whose id starts with `original_` / `linkedin_`. `GitHubAdapter` /
`PortfolioAdapter` are stubs returning `None`.

### Extraction prompt (versioned)

Mirror `job_analysis_prompt.py`:

- `CANDIDATE_EXTRACT_PROMPT_VERSION = "1.0.0"`,
  `CANDIDATE_EXTRACT_SCHEMA_VERSION = "1.0.0"`.
- `build_candidate_extract_output_schema()` — JSON schema with `profile`
  (name/title/headline/summary/location), `skills[]` (name, level 1–5, category,
  years_of_experience, last_used, confidence), `experiences[]` (company, role,
  start_date, end_date, duration_months, summary, highlights[], skills[],
  confidence), `projects[]` (name, description, url, role, skills[],
  start_date, end_date, confidence), `educations[]` (institution, degree, field,
  start_date, end_date, confidence), `certificates[]` (name, issuer, issue_date,
  credential_url, confidence), `interests[]` (name), `languages[]` (name,
  proficiency). Required top-level: `profile`, `skills`, `experiences`,
  `projects`, `educations`, `certificates`, `interests`, `languages` — all
  arrays default to `[]`.
- `build_candidate_extract_prompt(source_type, raw_text)` — instructs the LLM to
  extract the complete factual profile from the labeled raw document, marking
  per-item confidence and keeping output short/untruncated, ending with
  "Respond ONLY with valid JSON matching exactly this schema".

### Validation

`CandidateExtractOutput` (pydantic) mirroring `job_analysis_validation.py`:
coerce ints/floats, clamp `confidence` to [0,1], `level` to [0,5], `proficiency`
to the entity vocab, string lists from comma strings, required non-empty names.
`dump_payload()` returns the validated dict.

### Extraction service

`CandidateExtractService(profile_repo, source_repo, skill_repo, llm=None)`:

1. `process(adapter)` → `adapter.fetch()`; `None` → `{"status": "skipped",
   "reason": "no_content"}`.
2. `extract_and_store(content)`:
   - `profile = profile_repo.get_or_create_current()`.
   - Skip if `source_repo.get_by_type_and_version(profile_id, source_type,
     version)` has status `processed` → return `{"status": "skipped",
     "reason": "already_processed"}`.
   - Build prompt + schema; `_obtain_valid_payload(llm, prompt, schema)` using
     the analyze-node validate-retry-once pattern (`_coerce_payload` /
     `_is_json_parse_error` / `_format_validation_error`). On failure mark the
     source row `failed` with the error and raise a clean error.
   - Resolve skills: dedupe by name, `skill_repo.resolve_skill({"name": ...,
     "source_type": "ai_generated"})` → int `skill_id`. Skills from the document
     are `origin="explicit"` with `Evidence(sources=[f"{source_type} v{version}"],
     confidence=...)`.
   - Map validated output to child dicts (skills / experiences / projects /
     educations / certificates / interests / languages) — each carrying
     `evidence: {"sources": [...], "confidence": ..., "notes": ""}`.
   - `profile_repo.update_core(profile_id, {...name/title/headline/summary/location})`;
     `profile_repo.replace_children(profile_id, kind, items)` for every kind.
   - Create or update the source row (`status="processed"`, `processed_at`).
   - Return summary `{"source_type", "version", "status": "processed",
     "profile_id", "skill_count", "prompt_version", "schema_version"}`.

Skill `origin`: Phase 100 stores everything the document mentions as
`explicit`. `inferred` is reserved for later merge/inference phases; the enum
and storage already support it.

## Files

- New: `apps/backend/candidates/application/adapters/*.py`,
  `apps/backend/candidates/application/services/*.py`,
  `apps/backend/candidates/application/__init__.py`.
- New: `apps/backend/tests/candidates/application/` — `test_source_adapters.py`,
  `test_candidate_extract_validation.py`, `test_candidate_extract_prompt.py`,
  `test_candidate_extract_service.py`.
- New: `implementation-history/100_candidate_source_adapters_extraction.md`.
- Modified: `DOMAIN.md` (extraction/adapters note), `ARCHITECTURE.md` if needed.
- No migration, no API routes, no frontend.

## Testing Requirements

TDD (red → green):

- Adapters: fake `IResumeRepository`; `ResumeAdapter` returns latest
  `original_*` (text + version), `None` when absent; `LinkedInAdapter` mirrors;
  GitHub/Portfolio stubs return `None`.
- Prompt: schema contains all required sections; prompt embeds the schema JSON
  and labels the source type; version constants exist.
- Validation: valid payload passes and clamps; bad level/confidence/proficiency
  coerced or rejected; missing `skills` rejected; `dump_payload()` round-trips.
- Service (fakes, no DB): happy path persists core + children via fake profile
  repo, records source row, resolves skills (dedupe), stamps versions; empty
  adapter → skipped; already-processed version → skipped; LLM returning garbage
  → retried once then failed with source row `failed`; `origin="explicit"` +
  `Evidence` present on skills.
- Run `uv run pytest apps/backend/tests/ -v`; `uv run ruff check` on changed
  dirs.

## Constraints

- All AI calls through `LLMService` (AGENTS.md rule 1); never call providers
  directly.
- Do not add API routes, no processing workflow / merge engine / `ExecutionType`
  (Phases 101+).
- Cross-context reads only: resume rows come from the jobs context via
  `IResumeRepository`; `skill_id` remains a logical reference (rule 15),
  resolved via skills `resolve_skill`.
- No `print()` — structlog where needed.
- Keep code/tests/docs in sync; follow `docs/database/alembic-guide.md` for any
  future migration (generate first via autogenerate, then tune).
