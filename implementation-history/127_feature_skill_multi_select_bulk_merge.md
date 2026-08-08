# Prompt 127 - Skill Multi-Select + Bulk Merge

## Objective

Add multi-select to the Skills v2 list and a bulk action that merges all
selected skills into a single user-picked target, reusing the existing
merge-one-skill-into-another dialog and the already bulk-capable
`POST /api/skills/merge` contract.

## Current State

- Backend `SQLAlchemySkillRepository.merge(target_id, source_ids)` already loops
  over a list of source ids (alias creation, mention folding, soft-hide). The
  endpoint accepts `source_ids: list[int]` with no request validation.
- Frontend lists skills in a virtualized table (`SkillsTable` +
  `SkillRow`). There is no multi-select pattern anywhere in the app.
- Single merge lives in `SkillEditDrawer`, which calls `skillApi.merge(targetId,
  [skillId])` ad-hoc and opens `MergeSkillDialog` (single source).
- `MergeSkillDialog` is single-select target picker built on
  `DebouncedInput` + scrollable list (the app has no Command/Combobox).

## Implementation Steps

1. Add tests (TDD red phase):
   - Backend: `apps/backend/tests/skills/presentation/api/` — merge rejects empty
     `source_ids` (400) and target ∈ sources (400).
   - Frontend: update `MergeSkillDialog.test.tsx` for the plural `sources` prop;
     add `SkillRow` select-checkbox test (toggle + stopPropagation); add
     selection/bulk-merge coverage (select-all/indeterminate, merge posts all
     selected ids, selection clears on filter change and after merge).
2. Backend validation in `merge_skills` (`skills_router.py`):
   `BadRequestError` when `source_ids` empty or `target_id ∈ source_ids`; fix
   stale `docs/api/skills/merge-skills.md` (JSON response, not 204).
3. Frontend entity layer: add `useMergeSkills()` mutation hook in
   `entities/skill/hooks.ts` (invalidates `[SKILLS_KEY]` on settle).
4. Grid templates: add `SKILL_GRID_TEMPLATE_WITH_SELECT` and
   `SKILL_GRID_TEMPLATE_WITH_PIN_SELECT` (44px leading column, like Pin).
5. `SkillRow`: optional `showSelectColumn` / `selected` / `onToggleSelect`;
   checkbox cell stops propagation (matches the Pin cell).
6. `SkillsTable`: optional `showSelectColumn` + `selectedIds` /
   `onToggleSelect` / `onToggleSelectAll`; indeterminate-aware header
   checkbox; thread props to rows and skeleton.
7. `SkillsToolbar`: selection action bar rendered when `selectedCount > 0`
   (count, "Merge N into…", "Clear"), plus `mergePending`.
8. `SkillsPage`: owns selection state (`Set<number>`); select-all derived from
   loaded items; clears selection on query/category/pinned change and prunes
   stale ids; mounts the generalized `MergeSkillDialog`; bulk merge mutation
   with toast + selection clear on success.
9. `MergeSkillDialog`: generalize `skill` → `sources: {id,name}[]`; exclude all
   source ids; plural copy/labels; `onMerge(targetId)` unchanged.
10. `SkillEditDrawer`: switch to `useMergeSkills()` and pass
    `sources={[{id, name}]}` (single-source path unchanged).
11. Docs: `docs/ux/features/skills/page.md`, `skill-row.md`,
    `docs/ux/flows/skills/merge-skills.md` (bulk flow + Mermaid diagram),
    `docs/ux/README.md`, `DESIGN.md` wireframes.
12. Version bump (MINOR): `VERSION` → 3.11.0, `CHANGELOG.md` entry,
    `pyproject.toml`, `apps/frontend/package.json`; `./scripts/check-version.sh`.

## Testing Requirements

- `uv run pytest apps/backend/tests/skills/ -v`
- `cd apps/frontend && npx vitest run`
- `cd apps/frontend && npm run lint && npm run typecheck`

## Constraints

- No schema change, so no Alembic migration.
- Selection survives pagination (virtualized rows unmount); cleared on filter
  change; pruned to ids still present in loaded items.
- Reuse the existing `DebouncedInput` + list picker; no new Command/Combobox.
- Keep cross-context logical-reference rules untouched.
