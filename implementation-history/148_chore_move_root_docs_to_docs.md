# Prompt 145 - Move Root Overview Docs Into docs/

## Objective

The repository root carries five overview documents that are **not
conventional** for AI-assisted repos (root should stay lean: README.md +
AGENTS.md + config) and are **redundant** with the established `docs/`
structure:

- `API.md` — API overview (duplicates `docs/api/api-design.md` + per-context specs)
- `ARCHITECTURE.md` — architecture overview (there is a `docs/architecture/` directory)
- `CONTEXT.md` — project context (overlaps AGENTS.md Project Overview/Key Rules)
- `DESIGN.md` — product/UX design (the UX home is `docs/ux/`)
- `DOMAIN.md` — domain entities/business rules (the domain home is `docs/domain/`)

Each is moved (not deleted) into the matching `docs/` location, with all
current-facing cross-references updated. No content is lost.

## Current State

- Root files to move: `CONTEXT.md` (41 lines), `API.md` (168),
  `ARCHITECTURE.md` (151), `DOMAIN.md` (180), `DESIGN.md` (648).
- Target locations with no filename collision:
  - `CONTEXT.md` → `docs/context.md`
  - `API.md` → `docs/api/API.md`
  - `ARCHITECTURE.md` → `docs/architecture/overview.md`
    (`docs/architecture/ARCHITECTURE.md` already exists — an older full-design
    doc, out of scope here)
  - `DOMAIN.md` → `docs/domain/overview.md`
  - `DESIGN.md` → `docs/ux/DESIGN.md`
- Current-facing references to update: `AGENTS.md` (rule 13, development
  workflow, Documentation Entry Points table), `README.md` (Documentation
  table), `docs/ux/README.md`, `docs/ux/app-shell.md`,
  `docs/ux/features/candidate/profile-import.md`, plus internal `docs/…`
  links inside the five moved files themselves (relative-link rewrites).

## Implementation Steps

## 1. Move the files (`git mv`, preserves history)

- `git mv CONTEXT.md docs/context.md`
- `git mv API.md docs/api/API.md`
- `git mv ARCHITECTURE.md docs/architecture/overview.md`
- `git mv DOMAIN.md docs/domain/overview.md`
- `git mv DESIGN.md docs/ux/DESIGN.md`

## 2. Fix internal `docs/…` links inside the moved files

- `docs/context.md` — none (no file links).
- `docs/api/API.md` — `docs/api/api-design.md` → `api-design.md`;
  `docs/api/` per-context list → `.` + subdir names;
  `docs/api/applications/README.md` → `applications/README.md`;
  `docs/ai/application-intelligence.md` → `../ai/application-intelligence.md`.
- `docs/architecture/overview.md` — "More Details" list becomes relative:
  `ARCHITECTURE.md`, `./`, `../ai/`, `../domain/` (incl.
  `../domain/applications/`), `../queue/`.
- `docs/domain/overview.md` — `docs/domain/candidates/events.md` →
  `candidates/events.md`; `docs/domain/applications/events.md` →
  `applications/events.md`.
- `docs/ux/DESIGN.md` — all `docs/ux/…` links become relative (`features/…`,
  `flows/…`, `design-system/`, `README.md`).

## 3. Update external references

- `AGENTS.md` rule 13: `DESIGN.md` → `docs/ux/DESIGN.md`.
- `AGENTS.md` development workflow: the repo-root guides list gains `docs/`
  paths.
- `AGENTS.md` Documentation Entry Points table: retarget the five rows to
  their moved locations.
- `README.md` Documentation table: same retarget.
- `docs/ux/README.md`, `docs/ux/app-shell.md`,
  `docs/ux/features/candidate/profile-import.md`: `DESIGN.md` →
  `docs/ux/DESIGN.md`.

## 4. Docs trace

Write this implementation-history file and commit it with the change.

---

# Testing Requirements

Docs-only change; no backend/frontend tests are affected. Verification:

- `rg -n "CONTEXT\.md|DOMAIN\.md|ARCHITECTURE\.md|DESIGN\.md|API\.md"`
  shows no current-facing reference to the old root paths outside
  `implementation-history/` and `CHANGELOG.md` (historical records).
- `git mv` preserved history (`git log --follow` on the moved files).
- `git status` / `git diff` review.

---

# Important Constraints

- Do not touch historical records: `implementation-history/`,
  `CHANGELOG.md`, `docs/adr/`.
- Do not modify `docs/architecture/ARCHITECTURE.md` (out of scope; a separate
  task should reconcile the stale full-design doc).
- Do not touch app code, version files, or `AGENTS.md` rules other than the
  three reference locations above.
- No version bump unless a release is requested (AGENTS.md rule 12).