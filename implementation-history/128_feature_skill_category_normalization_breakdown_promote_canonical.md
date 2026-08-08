# Prompt 128 - Skill/Category Normalization, Break-Down & Promote-to-Canonical

## Objective

Make skill and category naming canonical and case/format-insensitive, add the
ability to break a composite skill into atomic children, and let an alias be
promoted to the canonical name. Extraction becomes fine-grained (splits
compound entries such as `NoSQL / SQL`) and honors the breakdown map.

Naming is locked to **canonical** (the authoritative skill/category name) and
**alias** (an alternate registered name). "main"/"primary" are never used.

## Current State

- `skill.skills.name` is unique but case/format-sensitive: `NoSQL` and `nosql`
  can coexist. `skill.skill_aliases` holds `alias_name` + `normalized_name`.
  Categories (`skill.skill_categories`, in-flight category work, migration
  `skill_002` untracked) have a unique `name` with the same case problem.
- `resolve_skill` matches exact name then alias, then creates (`source_type`
  `ai_generated`). `rename` swaps `name` and re-points aliases.
- Extraction: `AnalyzeNode` builds one combined prompt
  (`job_analysis_prompt.py`, `JOB_ANALYSIS_PROMPT_VERSION` 1.4.0);
  `ExtractSkillsNode` normalizes via `normalize_skills`
  (`job_analysis_scoring.py`); `PersistSkillsNode` resolves + upserts mentions.
- Frontend: `SkillActions` row buttons, `SkillDetailDrawer` footer, and
  `SkillEditDrawer` alias badges (add/remove). No breakdown or promote actions.

## Implementation Steps

1. Add tests (TDD red phase) — see Testing Requirements.
2. Models (`skill_model.py`): `SkillModel.slug` and `SkillCategoryModel.slug`
   (unique, not null, indexed); `SkillBreakdownModel` on `skill.skill_breakdowns`
   (`origin_skill_id`, `child_skill_id` FKs cascade, unique pair, `created_at`).
3. Migration `skill_003` (autogenerate then tune, chain after `skill_002`):
   add nullable slugs, SQL backfill, merge collisions (keep lowest-id, re-point
   mentions/category links, alias+hide dups), `SET NOT NULL` + unique index,
   create breakdown table. Verify single head + upgrade/downgrade round-trip.
4. `skills/domain/slug_utils.py`: `slugify()` (lowercase, trim, collapse
   separators to `-`, keep `+.#-`).
5. Repo slug resolution: `resolve_skill` exact → alias → slug → create (set
   slug); `create`/`create_from_dict`/`update`/`rename` recompute slug.
6. Category normalization: `_ensure_category`/`create_category` resolve exact →
   slug → create; store slugified canonical name.
7. Repo operations: `break_down(origin_id, child_names)` (validate origin
   visible, ≥2 children, resolve children by name/alias/slug, idempotent links,
   duplicate origin mentions to every child, hide origin);
   `get_breakdown_map()`; `list_breakdowns(skill_id)`;
   `promote_alias_to_canonical(skill_id, alias_name)` (verify alias, collision
   check, swap name ↔ alias, recompute slug);
   `normalize_all()` (re-slugify + merge collisions + report).
8. Events: `SkillBrokenDown`, `SkillCanonicalChanged` via in-memory
   `SkillEventPublisher`; document in `docs/domain/skills/events.md`.
9. API: `POST /skills/{id}/breakdown`, `PATCH /skills/{id}/canonical`,
   `GET /skills/breakdowns`; schemas `SkillBreakdown`, `SkillCanonicalChange`;
   CLI `normalize-skills-and-categories` → `normalize_all()`.
10. Extraction: bump prompt to 1.5.0 (atomic/lowercase/version-free skills,
    consistent lowercase categories, optional breakdown section);
    `prepare_profile_node` fetches `get_breakdown_map()` into
    `analysis_context["breakdown_map"]`; `analyze_node` passes to prompt;
    `normalize_skills(raw, breakdown_map=None)` splits `/ , and & or`, dedupes
    by slug, expands map matches, slug-normalizes category names;
    `extract_skills_node` passes the map.
11. Frontend: `api.ts`/`types.ts` (`breakdown`, `promoteAliasToCanonical`),
    `hooks.ts` (`useBreakdownSkill`, `usePromoteAliasToCanonical`), row
    `onBreakDown` action, `BreakdownSkillDialog`, Detail drawer Break Down
    button, Edit drawer "Make canonical" per alias, row `onMerge` action
    (Merge dialog with the row as the single source).
12. Docs: API (`normalization.md`), domain (`events.md` + catalog entries),
    UX features/flows (breakdown dialog + flow, edit-skill make-canonical,
    skill-row/merge actions) + Mermaid + README + DESIGN.
13. Version bump MINOR → 3.12.0 (all 5 locations) + `check-version.sh`.

## Testing Requirements

- `uv run pytest apps/backend/tests/skills/ -v`
- `cd apps/frontend && npx vitest run`
- `cd apps/frontend && npm run typecheck`
- `uv run alembic upgrade head` / `alembic history` / `alembic heads` (single)

## Constraints

- Naming: **canonical** + **alias** only; never "main"/"primary"/"switch main".
- Cross-context rules: breakdown/alias FKs stay inside the `skill` schema.
- LLM calls only through `LLMService` (prompt text only here).
- The in-flight category feature (untracked) is preserved; this work chains
  after its migration `skill_002` and reuses its events/catalog pattern.
- TODO tracked at end: run `normalize-skills-and-categories` CLI pass against
  dev data and verify counts.
