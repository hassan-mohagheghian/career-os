# Prompt 099 — Candidate Profile Domain: Domain Skeleton + Persistence

## Objective

Phase 1 of the Canonical Candidate Profile Domain (master spec:
`098_feature_candidate_profile_domain.md`). Create the greenfield `candidates`
bounded context with a rich domain model, persistence layer (`candidate` DB
schema), repository interfaces, and domain events. This phase is architecture
only — no source adapters, no extraction, no API routes yet.

## Current State

No `Candidate` / `CandidateProfile` / `UserProfile` concept exists anywhere in
the backend or frontend. Skills are a flat global list (`skill.skills`) with no
owner; the analysis pipeline's "profile" is just raw concatenated resume +
LinkedIn text. See the investigation findings in the 098 appendix.

## Scope

- New `apps/backend/candidates/` DDD bounded context (mirrors `skills/`):
  - `domain/value_objects/evidence.py` — `Evidence` (sources + confidence +
    notes), `Confidence` (0–1 clamp).
  - `domain/entities/` — `Candidate`, `CandidateProfile`, `CandidateSource`,
    `CandidateSkill`, `CandidateExperience`, `CandidateProject`,
    `CandidateEducation`, `CandidateCertificate`, `CandidateInterest`,
    `CandidateLanguage`, `CandidateProfileVersion`. All extend `BaseEntity`
    with `to_dict` / `from_dict` (convention matches
    `skills/domain/entities/skill.py`).
  - `domain/repositories/` — `ICandidateRepository`,
    `ICandidateProfileRepository`, `ICandidateSourceRepository`.
  - `domain/events.py` — `CandidateProfileCreated`, `CandidateProfileUpdated`,
    `CandidateSourceAdded`, `CandidateSourceUpdated`, `CandidateMergeCompleted`,
    `CandidateVersionCreated`, `CandidateSkillInferred` (extend
    `shared/domain/domain_event.py::DomainEvent`).
  - `infrastructure/models/candidate_model.py` — ORM models in the `candidate`
    schema.
  - `infrastructure/repositories/` — SQLAlchemy impls.
  - `infrastructure/mappers.py` — model ↔ dict mapping.
- Persistence wiring:
  - `candidate` schema added to `SCHEMAS` in
    `apps/backend/shared/infrastructure/database/sqlalchemy_config.py`.
  - `apps/alembic/candidate/versions/` added to `version_locations` in
    `alembic.ini`; models imported in `apps/alembic/env.py` and
    `shared/infrastructure/config/db.py::init_db`.
  - **Generate the migration with Alembic autogenerate FIRST** (so the
    revision-graph references `revision`/`down_revision`/`branch_labels` are
    computed by Alembic, never hand-guessed), then tune the content (indexes,
    FKs, naming, `CREATE SCHEMA`) and verify `alembic history` + `alembic heads`
    (single head) + `alembic upgrade head` + a downgrade/upgrade round-trip
    against a dev DB. Full convention: `docs/database/alembic-guide.md`.
- DI factories in `apps/backend/dependencies.py`.

## Domain Model

### Tables (schema `candidate`)

- `candidates` — the person: `id` (str uuid), `name`, `headline`, `summary`,
  `location`, `created_at`, `updated_at`.
- `candidate_profiles` — the canonical profile header: `id`, `candidate_id`
  (FK → `candidate.candidates.id`, within-context FK), `version` (int, current),
  `name`, `title`, `headline`, `summary`, `location`, `created_at`, `updated_at`.
- `candidate_sources` — a raw source linked to a profile: `id`, `profile_id`
  (FK → `candidate.candidate_profiles.id`), `source_type`
  (`resume`/`linkedin`/…), `version` (the source's own version), `status`,
  `error`, `processed_at`, `created_at`, `updated_at`.
- `candidate_skills` — `id`, `profile_id` (FK → `candidate.candidate_profiles.id`),
  `skill_id` (logical ref → `skill.skills.id`, plain Integer column, nullable,
  **no FK** — cross-context), `name` (snapshot), `level` (1–5), `category`,
  `confidence` (float), `origin` (`explicit`/`inferred`), `years_of_experience`,
  `last_used`, `evidence` (Text JSON: `{"sources": [...], "notes": ""}`),
  `created_at`, `updated_at`.
- `candidate_experiences` — `id`, `profile_id` (FK), `company`, `role`,
  `start_date`, `end_date`, `duration_months`, `summary`, `highlights` (Text
  JSON list), `skills` (Text JSON list), `evidence` (Text JSON), `created_at`,
  `updated_at`.
- `candidate_projects` — `id`, `profile_id` (FK), `name`, `description`, `url`,
  `role`, `skills` (Text JSON), `evidence` (Text JSON), `created_at`,
  `updated_at`.
- `candidate_educations` — `id`, `profile_id` (FK), `institution`, `degree`,
  `field`, `start_date`, `end_date`, `evidence` (Text JSON), `created_at`,
  `updated_at`.
- `candidate_certificates` — `id`, `profile_id` (FK), `name`, `issuer`,
  `issue_date`, `credential_url`, `evidence` (Text JSON), `created_at`,
  `updated_at`.
- `candidate_interests` — `id`, `profile_id` (FK), `name`, `created_at`.
- `candidate_languages` — `id`, `profile_id` (FK), `name`, `proficiency`,
  `created_at`.
- `candidate_profile_versions` — `id`, `profile_id` (FK →
  `candidate.candidate_profiles.id`), `version`, `snapshot` (Text JSON of full
  profile), `source_versions` (Text JSON mapping source_type → version),
  `change_summary`, `created_at`.

FKs are allowed **within** the `candidate` schema (aggregate + children). The
only cross-context link — `candidate_skills.skill_id` → `skill.skills` — is a
**logical reference** with no FK (AGENTS.md rule 15), enforced at the repository
layer.

### Repository primitives

- `ICandidateRepository` — `get_candidate()` (the singleton candidate or None),
  `create_candidate(data)`, `update_candidate(id, data)`.
- `ICandidateProfileRepository` — `get_or_create_current()` (returns candidate
  + current profile, creating the singleton on first call),
  `get_current_profile()` (nested: profile + all children), `update_core(id,
  data)`, `replace_children(profile_id, kind, items)` (kind in skills /
  experiences / projects / educations / certificates / interests / languages;
  delete-all-then-insert), `create_version(profile_id, version, snapshot,
  source_versions, change_summary)`, `list_versions(profile_id)`.
- `ICandidateSourceRepository` — `create(data)`, `list_for_profile(profile_id)`,
  `get_by_type_and_version(profile_id, source_type, version)`,
  `update(id, data)`.

## Files

- New: `apps/backend/candidates/**` (entities, VOs, repos, models, mappers,
  events, `__init__.py` files)
- New: `apps/alembic/candidate/versions/candidate_001_*.py`
- New: `apps/backend/tests/candidates/**` (domain + infrastructure tests)
- New: `implementation-history/099_candidate_profile_domain.md`
- Modified: `alembic.ini`, `apps/alembic/env.py`,
  `apps/backend/shared/infrastructure/database/sqlalchemy_config.py`,
  `apps/backend/shared/infrastructure/config/db.py`, `apps/backend/dependencies.py`,
  `apps/backend/tests/conftest.py`, `DOMAIN.md`, `ARCHITECTURE.md`

## Testing Requirements

TDD (red → green). Backend tests under `apps/backend/tests/candidates/`:

- Domain: entity `to_dict`/`from_dict` round-trips; `Evidence`/`Confidence`
  invariants (confidence clamped to [0, 1]); default origins/statuses.
- Events: each event type carries the right `event_type` and `aggregate_id`.
- Infrastructure: repo CRUD against the test Postgres DB — create candidate +
  profile, persist a `CandidateSkill` with FK to a real `skill.skills` row,
  nested `get_current_profile()`, `replace_children`, version snapshot
  round-trip, source repo lookups.
- Run `uv run pytest apps/backend/tests/ -v`; verify `alembic history` shows the
  new head and `alembic upgrade head` succeeds.

## Constraints

- Do not add API routes (no `candidates` router yet — that is Phase 103).
- Do not implement extraction / adapters / merge yet (Phases 100–101).
- `candidates` context may import `skills` (for the logical `skill_id` link and
  later `resolve_skill`); `skills` must never import `candidates`.
- FKs allowed **within** the `candidate` schema (DDD aggregate + children); the
  only cross-context link (`candidate_skills.skill_id` → `skill.skills`) is a
  logical reference with no FK (AGENTS.md rule 15) — integrity enforced at the
  repository layer.
- Use structlog, SQLAlchemy ORM only, Alembic autogenerate + tune.
