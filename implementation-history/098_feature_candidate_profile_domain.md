# Prompt — Design & Implement Canonical Candidate Profile Domain

## Objective

Design and implement a complete Candidate Profile domain.

Do NOT treat this as a Resume Parser.

Do NOT treat this as a LinkedIn Importer.

The objective is to create a canonical representation of a candidate that can continuously evolve as new sources become available.

The implementation should be architecture-first.

If the scope is too large, split the work into multiple implementation histories.

The implementation order should maximize long-term maintainability.

You may create multiple implementation phases if necessary.

---

# Read Documentation First

Read all existing documentation related to:

- Jobs
- Companies
- Skills
- ProcessingExecution
- LangGraph workflows
- AI Analysis
- Architecture
- Context Boundaries

Also inspect existing implementation.

Avoid introducing duplicated concepts.

---

# Core Vision

The system must never depend directly on a Resume.

The system must never depend directly on LinkedIn.

Instead, everything should converge into a single canonical Candidate Profile.

Example

Resume

↓

LinkedIn

↓

GitHub

↓

Portfolio

↓

Future Sources

↓

Canonical Candidate Profile

All future AI analysis must operate on the Candidate Profile.

Never on individual sources.

---

# Candidate Profile

Design a rich domain model.

Possible entities include (adjust if necessary):

Candidate

CandidateProfile

CandidateSkill

CandidateExperience

CandidateProject

CandidateEducation

CandidateCertificate

CandidateInterest

CandidateLanguage

CandidateSource

CandidateProfileVersion

You are free to improve this model.

---

# Candidate Sources

The architecture must support multiple independent sources.

Initial supported sources:

- Resume
- LinkedIn (raw exported text)

Future sources:

- GitHub
- Portfolio
- StackOverflow
- Kaggle
- Behance
- Dribbble
- Personal Website

The architecture must support adding new sources without modifying the Candidate Profile model.

---

# Source Adapters

Design source adapters.

Example

CandidateSourceAdapter

↓

ResumeAdapter

LinkedInAdapter

GitHubAdapter

PortfolioAdapter

Only Resume and LinkedIn should be implemented now.

The others should exist as extension points.

---

# Extraction Pipeline

Implement an extraction workflow.

Resume

↓

Raw Extraction

↓

Structured Extraction

↓

Skill Extraction

↓

Experience Extraction

↓

Project Extraction

↓

Inference

↓

Merge

↓

Candidate Profile

This workflow should use LangGraph if appropriate.

Reuse existing architecture whenever possible.

---

# Explicit vs Inferred Data

The profile should distinguish between:

Explicit

Information directly present in a source.

Example

Python

FastAPI

Docker

---

Inferred

Information inferred from experience.

Example

Dependency Injection

REST API Design

Microservices

Distributed Systems

Confidence scores should be stored.

---

# Candidate Skills

Each skill should include metadata.

Example

Skill

Level

Confidence

Evidence

Years of Experience

Last Used

Source References

Do not store only a skill name.

---

# Evidence Model

Every extracted entity should preserve provenance.

Example

Python

Sources

✔ Resume

✔ LinkedIn

✔ GitHub

Confidence

0.96

---

# Candidate Profile Merge

This is a merge system.

Never recreate the profile from scratch if a new source is added.

Instead:

New Source

↓

Extract

↓

Compare

↓

Diff

↓

Merge

↓

New Candidate Profile Version

---

# Versioning

Support profile versioning.

Example

Resume V1

↓

Candidate Profile V1

Resume V2

↓

Candidate Profile V2

Profile changes should be traceable.

---

# Source Versioning

Each source should have independent versions.

Example

Resume

Version 4

LinkedIn

Version 3

GitHub

Version 2

Updating Resume must not require reprocessing GitHub.

Updating GitHub must not require reprocessing Resume.

---

# Candidate Timeline

Support historical growth.

Example

2025

Python

FastAPI

2026

Docker

Redis

2027

Kubernetes

The architecture should allow future visualization.

---

# Matching Preparation

Although matching is NOT implemented now,

the Candidate Profile should be designed so it can later support:

- Job Matching
- Skill Gap Analysis
- Resume Optimization
- Learning Recommendation
- AI Career Coach

Do not implement those features.

Only prepare the architecture.

---

# Workflow Events

Emit domain events.

Examples

candidate.profile.created

candidate.profile.updated

candidate.source.added

candidate.source.updated

candidate.merge.completed

candidate.version.created

candidate.skill.inferred

candidate.skill.updated

---

# Tests

Implement comprehensive tests.

Cover:

Extraction

Merge

Diff

Source updates

Versioning

Evidence tracking

Skill inference

Profile integrity

Future extensibility

---

# Architecture Review

Before implementation,

review the existing project architecture.

If improvements are needed,

propose them first.

Avoid introducing duplicated concepts.

---

# Refactoring

If existing Resume or Candidate logic conflicts with this design,

refactor it.

The Candidate Profile domain becomes the single source of truth.

---

# Implementation Planning

Before writing code,

estimate the scope.

If necessary,

split the implementation into multiple Implementation Histories.

For each history provide:

- Goal
- Scope
- Files
- Risks
- Dependencies

Only then begin implementation.

Prioritize architectural correctness over implementation speed.

---

# Appendix — Approved Implementation Plan (reference note)

> Added 2026-08-07. This file is the master spec for the Candidate Profile
> domain. The phased plan below is the agreed roadmap; each phase ships its own
> implementation-history file (099–103), Alembic migration, tests, and docs.
>
> Note: this file was originally named `098_chatgpt_assisted_user_skills.md`
> (stale name); the content is the Canonical Candidate Profile Domain spec.

## Approved decisions (from planning Q&A)

1. Full 5-phase plan (099–103), each a separate implementation history.
2. `CandidateSkill.skill_id` → FK to existing `skill.skills` table — reuse the
   skills vocabulary, aliases, `resolve_skill`, and `skill_mentions`. The
   `candidates` context depends on `skills` (one-directional; candidates must
   never be imported by skills).
3. Wire through the **existing processing pipeline** — new
   `ExecutionType.CANDIDATE_PROCESSING`, two-phase LangGraph, run via
   `ProcessingExecutionRunner`, `RedisProcessingEventPublisher`, SSE progress.
4. Keep `/api/resumes` and `/api/linkedin` endpoints as-is for now; adapters
   read the same `job.resumes` table.

## Investigation findings (greenfield domain)

- **No existing candidate/profile concept** anywhere in backend or frontend —
  this domain is greenfield.
- **Closest templates:** `skills/` bounded context (full DDD: entity → repo →
  service → router) and the `job_analysis` two-phase LangGraph workflow
  (`processing/application/workflows/job_analysis/`).
- **Resume sources live in `job.resumes`** (`apps/backend/jobs/infrastructure/models/misc_models.py`)
  as rows `original_N` (master resume) and `linkedin_N` (LinkedIn), versioned
  by id-prefix via `IResumeRepository.get_next_version(prefix)` and read via
  `get_latest_original_raw_text()` / `get_latest_linkedin_raw_text()`.
  **Caution:** `resumes.raw_text` is overloaded — it also holds JSON generation
  state for queued tailored docs (`resume_<job>` / `cover_<job>` rows).
- **AI pattern to copy:** `LLMService.generate_structured` +
  `processing/application/services/job_analysis_prompt.py` (versioned
  `JOB_ANALYSIS_PROMPT_VERSION` / `JOB_ANALYSIS_SCHEMA_VERSION` constants +
  strict Pydantic validation in `job_analysis_validation.py`). Never call
  providers directly.
- **Profile input today is raw text** — `PrepareProfileNode` +
  `processing/application/services/job_analysis_inputs.py` concatenate resume +
  LinkedIn (truncated to 6000 chars each) into `analysis_context`.
- **Domain events:** base `DomainEvent` in `shared/domain/domain_event.py`;
  per-context `events.py` modules; no generic EventBus — transport is Redis
  pub/sub via `ProcessingEventPublisher` + SSE (`/events/processing`).
- **Migrations:** Alembic multi-schema. `alembic.ini` `version_locations` lists
  job/company/skill/shared; the root `apps/alembic/versions/` dir holds legacy
  processing migrations. A new `candidate` context needs: add
  `apps/alembic/candidate/versions` to `version_locations`, add
  `"candidate": [...]` to `SCHEMAS` in
  `apps/backend/shared/infrastructure/database/sqlalchemy_config.py`, import
  models in `apps/alembic/env.py` + `shared/infrastructure/config/db.py::init_db`.
- **DI + routers:** repo factories in `apps/backend/dependencies.py`; routers
  registered in `shared/presentation/api/root_router.py` (never in
  `entrypoints/api.py`).
- **Tests:** PostgreSQL test DB (`<db>_test`), fixtures in
  `apps/backend/tests/conftest.py` (`sa_session`, `client`); per-context
  conftests override DI. `.env`: `DATABASE_URL=postgresql+psycopg://jobsearch:jobsearch@localhost:5432/jobsearch`.
- **Existing convention:** entities extend `BaseEntity` with `to_dict` /
  `from_dict`; repos return dicts; ORM models in per-context `candidate`
  schema; `created_at` stored as ISO `Text` (matching skills models).

## Roadmap

### 099 — Candidate domain skeleton + persistence
New `apps/backend/candidates/` bounded context. Entities: `Candidate`,
`CandidateProfile`, `CandidateSource`, `CandidateSkill`, `CandidateExperience`,
`CandidateProject`, `CandidateEducation`, `CandidateCertificate`,
`CandidateInterest`, `CandidateLanguage`, `CandidateProfileVersion`. Value
objects: `Evidence` (sources + confidence), `Confidence`. Repo interfaces +
SQLAlchemy impls. `candidate` schema migration (autogenerate + tune). Domain
events module. DI factories. No API routes yet.

### 100 — Source adapters + structured extraction
`CandidateSourceAdapter` ABC → `ResumeAdapter`, `LinkedInAdapter` (read
`job.resumes`); GitHub/Portfolio stubs. One `candidate.extract` LLM call via
`LLMService.generate_structured` (versioned prompt/schema + strict validation).
Skills resolved through skills context `resolve_skill`; explicit-vs-inferred +
confidence + evidence stored.

### 101 — Processing workflow + merge/diff/versioning
`ExecutionType.CANDIDATE_PROCESSING`; two-phase LangGraph (source prep no-LLM;
extraction + merge one-LLM) under `processing/application/workflows/candidate_processing/`;
wired via `processing/infrastructure/workflow/assembly.py` + `WorkflowStepMapper`
+ SSE. Merge engine (compare → diff → merge), per-source version independence,
`CandidateProfileVersion`, timeline growth.

### 102 — Integrate profile into job analysis
`PrepareProfileNode` / `job_analysis_inputs.py` read the structured Candidate
Profile when present, falling back to raw resume/LinkedIn text. Keep the single
combined `job.analyze` call; bump prompt version if prompt text changes.

### 103 — API + Frontend + UX docs
`candidates/presentation/api/candidates_router.py` under `/api/candidates`
(profile, sources, versions, re-process). FSD frontend Candidate Profile page.
ASCII wireframes in `docs/ux/features/` + `docs/ux/flows/`, update
`docs/ux/README.md` index + `DESIGN.md`.

## Cross-cutting constraints

- Per-context Alembic migration — **generate via autogenerate FIRST** (so the
  revision-graph references `revision`/`down_revision`/`branch_labels` are
  computed by Alembic, never hand-guessed), then tune content (schema creation,
  indexes, FKs, naming to repo convention). Verify `alembic history` +
  `alembic upgrade head` + a downgrade/upgrade round-trip against a dev DB.
  This applies to every phase before any migration is written; see
  `docs/database/alembic-guide.md`.
- TDD: tests + docs before code (red → green); keep code/tests/docs in sync.
- Contexts must not cross-import; candidates → skills dependency allowed.
- Backend checks: `uv run pytest apps/backend/tests/ -v`; frontend (phase 103):
  `npx vitest run` + `npm run lint` + `npm run typecheck`.
- No `print()` — use structlog; all AI calls through `LLMService`.
