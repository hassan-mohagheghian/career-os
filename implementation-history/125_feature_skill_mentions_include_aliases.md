# Prompt 125 - Skill Mentions Include Aliases

## Objective

A skill's `mention_count` must equal the sum of its own mentions and the
mentions recorded under any separate skill row whose name is one of the
skill's aliases. This is computed at read time (folding); no data migration.

## Current State

`mention_count` comes from `get_mention_counts()` in
`apps/backend/skills/infrastructure/repositories/sa_skill_repository.py`
(counts `skill_mentions` rows grouped by exact `skill_id`). It is consumed
only by the skills list endpoint (`apps/backend/skills/presentation/api/skills_router.py`).

Mentions are attributed to a canonical skill via `resolve_skill()` (name match
first, then alias match). However, when a job/company mentions a name that
matches neither an existing skill nor an alias, `resolve_skill()` creates a new
`ai_generated` skill row and stores the mentions under it. If the user later
adds that name as an alias of an existing skill, those stored mentions are NOT
counted toward the canonical skill today.

## Implementation Steps

1. Add tests (TDD red phase):
   - `apps/backend/tests/skills/infrastructure/test_skill_mentions.py`:
     alias skill row mentions fold into the canonical skill's count; alias with
     no matching skill row does not fold; alias resolving to the skill's own id
     is not double-counted.
   - `apps/backend/tests/skills/presentation/api/test_skills_list_api.py`:
     `/api/skills/list` reports `mention_count` including alias-row mentions and
     sorts by it.
2. Update docs before/with code:
   - `docs/ux/features/skills/skill-row.md` and `docs/ux/features/skills/page.md`
     (Mentions column/section semantics).
   - `docs/ux/flows/skills/merge-skills.md` (note read-time alias folding).
3. Implement `get_mention_counts()` alias folding in `sa_skill_repository.py`:
   - Direct mention counts per `skill_id` (as today).
   - Query `skill_aliases` for the requested ids.
   - Resolve alias names to skill row ids via exact `SkillModel.name` match
     (consistent with `resolve_skill`).
   - Count `skill_mentions` for those resolved ids, excluding a skill's own id,
     and add to the canonical skill's count.
4. Version bump (MINOR): `VERSION` → 3.10.0, `CHANGELOG.md` entry,
   `pyproject.toml`, `apps/frontend/package.json`; verify via
   `./scripts/check-version.sh`.

## Testing Requirements

- `uv run pytest apps/backend/tests/ -v`
- `./scripts/check-version.sh`

## Constraints

- No schema change, so no Alembic migration.
- Frontend untouched (it displays `mention_count` as-is).
- Keep exact-name alias resolution consistent with `resolve_skill`.
