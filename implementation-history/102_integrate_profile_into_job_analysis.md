# Prompt 102 - Integrate Candidate Profile Into Job Analysis

## Objective

Implement Phase 102 of the Candidate Profile Domain (master spec
`098_feature_candidate_profile_domain.md`): make the Job Analysis workflow read
the structured Candidate Profile when one exists, falling back to raw
resume/LinkedIn text otherwise. Keep the single combined `job.analyze` LLM call.

## Decisions (approved in planning Q&A)

1. **Structured profile only** — when a Candidate Profile exists, its formatted
   text replaces the raw resume/LinkedIn documents section; raw text is used only
   when no profile exists (no duplication, no token bloat, no contradictions).
2. **Profile skills win** — when a profile exists, the `USER PROFILE (skills)`
   section is built from the profile's skills (level/confidence/evidence/years
   metadata) instead of `skill_repo.list_visible()`.
3. **Reword + bump prompt** — the prompt text is updated to state the structured
   profile is the primary source for fit scoring; bump
   `JOB_ANALYSIS_PROMPT_VERSION` to `1.4.0`. Schema version unchanged.

## Current State

- `PrepareProfileNode`
  (`apps/backend/processing/application/workflows/job_analysis/nodes/prepare_profile_node.py`)
  writes `analysis_context` keys `job_text`, `profile_text`
  (`build_profile_text(skills)`), `scoring_rules`, `resume_text`, and
  `profile_documents` (`build_profile_documents_text(resume_raw, linkedin_raw)`).
- Builders live in
  `apps/backend/processing/application/services/job_analysis_inputs.py`.
- `JobAnalysisGraph.__init__` takes `skill_repo`, `resume_repo`, `rule_repo`, ...
  (`graph.py`); wired in
  `processing/infrastructure/workflow/assembly.py::build_job_analysis_graph`.
- Prompt: `job_analysis_prompt.py`, `JOB_ANALYSIS_PROMPT_VERSION = "1.3.0"`,
  fit scored "primarily on the RESUME text".
- Profile dict shape (`ICandidateProfileRepository.get_current_profile`):
  core fields (name/title/headline/summary/location/version) + children
  `skills` (name, level, category, confidence, origin, years_of_experience,
  last_used, evidence), `experiences` (company, role, start_date, end_date,
  description), `projects`, `educations`, `certificates`, `interests`,
  `languages`. Candidates context is already wired into processing assembly for
  the candidate graphs (precedent at `assembly.py`).

## Scope (this phase)

### 1. Builder: `build_candidate_profile_text(profile: dict) -> str`

Add to `job_analysis_inputs.py`. Formats the canonical nested profile into a
labeled, truncated text block:

- Header: name, title, headline, summary, location, profile version.
- `SKILLS:` — each skill with level, confidence, years, evidence source names.
- `EXPERIENCE:` — company, role, dates, description (truncated).
- `PROJECTS:` / `EDUCATION:` / `CERTIFICATES:` / `INTERESTS:` / `LANGUAGES:`
  with the key fields.
- Cap total length to `MAX_PROFILE_DOC_CHARS` (6000) to bound prompt size.
- Pure, no I/O; tests assert formatting and truncation.

### 2. `PrepareProfileNode` gains optional `candidate_profile_repo`

- New optional constructor arg `candidate_profile_repo: Any = None` (backward
  compatible — existing call sites/tests keep working).
- On call: try `candidate_profile_repo.get_current_profile()`.
  - If a profile exists (non-None): build `profile_text` from
    `build_profile_text(profile["skills"])` and set `profile_documents` =
    `build_candidate_profile_text(profile)`; keep `resume_text` as today (raw,
    for fallback/context) or set from profile? — decision: keep `resume_text`
    populated from raw resume as today; it is not used when profile_documents is
    non-empty by the prompt. Simplest correct behavior: still fill
    `resume_text` from raw resume; `profile_documents` carries the structured
    profile. No raw resume duplication inside profile_documents.
  - If no profile (None) or no candidate_profile_repo: current behavior
    unchanged.
- Exception handling: wrap the profile read in the same try/except so a DB
  failure degrades to the raw-text path and records an error, matching the
  existing `test_profile_failure_degrades` pattern.

### 3. Prompt reword + version bump

- Update the `build_job_analysis_prompt` instruction block: state that when a
  structured profile is provided, fit scoring is based primarily on it (with the
  raw resume as a supplement/fallback); reword the "primarily on the RESUME
  text" instruction to reference the structured profile first.
- `JOB_ANALYSIS_PROMPT_VERSION` → `"1.4.0"`. Schema version stays `"1.1.0"`.

### 4. Assembly wiring

- `build_job_analysis_graph(session)`: pass
  `candidate_profile_repo=SQLAlchemyCandidateProfileRepository(session)` into
  `JobAnalysisGraph`; add the constructor arg to `JobAnalysisGraph.__init__`
  (default `None`) and forward to `PrepareProfileNode`.

### 5. Tests (TDD, write before code)

In `apps/backend/tests/processing/application/test_job_analysis.py`:

- `build_candidate_profile_text`: header fields, skills w/ metadata,
  experiences, truncation at 6000, empty-profile handling.
- `PrepareProfileNode` with a fake profile repo:
  - profile exists → `profile_documents` is structured profile text and does not
    contain the raw resume label; `profile_text` from profile skills.
  - no profile → falls back to raw resume/LinkedIn (`RESUME TEXT (latest):`).
  - profile repo raises → degrades to raw path + error recorded.
- Version test: `JOB_ANALYSIS_PROMPT_VERSION == "1.4.0"`.

### 6. Docs

- Update `docs/` job-analysis related docs if they mention the prompt version or
  input composition (check `docs/ai/`, `docs/processing/`, `DOMAIN.md`). No UX
  page changes in this phase (no frontend/API).

## Testing Requirements

- `uv run pytest apps/backend/tests/processing/application/test_job_analysis.py -v`
- Full suite: `uv run pytest apps/backend/tests/ -v` (must stay green, >= prior
  count).
- Ruff clean on changed files.

## Constraints

- Single combined `job.analyze` call — no new LLM calls, no workflow changes.
- No API/frontend/UX changes (Phase 103).
- No DB changes, no migrations.
- Keep raw-text fallback fully intact; new behavior is additive.
