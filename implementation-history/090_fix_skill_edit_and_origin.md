# Prompt 090 - Fix Skill Edit Drawer (missing GET /skills/{id}) + Skill Origin

## Objective

1. Fix the broken Skill Edit drawer. The drawer loads existing values via
   `skillApi.get(id)` → `GET /api/skills/{id}`, but no such route is registered,
   so every edit shows "Unable to load skill details." Add the route.
2. Introduce the **skill origin** concept end-to-end. The data layer already has
   `source` / `source_type` columns (`user_input` vs `ai_generated`), but they
   are dropped by `SkillListItemSchema`, absent from frontend types, and never
   rendered. Surface origin in the list API, the skill row, and the detail drawer.

## Current State

- `skills_router.py` registers `GET /list`, `GET ""`, `GET /hidden`, `GET
  /categories`, `GET /stats`, `PUT/PATCH/DELETE /{id}`, `/merge`,
  `/skill-relationships/*`, `/bulk-*` — but **no `GET /{id}`**.
- `SkillEditDrawer` (`features/skills-v2/components/SkillEditDrawer.tsx`) loads
  via `skillApi.get(skillId)` → 404 every time.
- `SkillModel.source` defaults `"service"`; `source_type` defaults `"service"`.
  Manual create sets `source="user"`, `source_type="user_input"`.
  `create_from_dict` (the AI-insert path) defaults `source_type="ai_generated"`
  but has no production caller yet.
- `SkillResponse` / `SkillUpdate` carry `source`/`source_type`; the v2
  `SkillListItemSchema` drops them. Frontend `SkillListItem`/`Skill` types have
  no origin fields. No UI shows origin.

## Implementation Steps

1. Backend — add `GET /skills/{id}` in `skills_router.py` (registered after the
   literal `/list`, `/hidden`, `/categories`, `/stats` routes so those win):
   `repo.get_by_id(id)`, raise `NotFoundError` when missing.
2. Backend — add `source_type` to `SkillListItemSchema`; fill it in
   `list_skills_v2` from `r.get("source_type")` (default `"user_input"`).
3. Frontend — add `source_type: string` to `SkillListItem`/`Skill` types.
4. Frontend — SkillRow: render a small origin badge (AI vs Manual) next to the
   name for `ai_generated` skills. SkillDetailDrawer Details tab: show origin.
5. Docs — `docs/api/skills/get-skill.md`; update `docs/api/skills/list-skills.md`
   (source_type field); update `docs/ux/features/skills/skill-row.md` +
   `skill-detail.md` (origin); this file.

## Testing Requirements

- Backend: `GET /skills/{id}` returns the skill (with aliases/tags); unknown id
  → 404; `/list` rows carry `source_type`.
- Frontend: `SkillRow` renders origin badge; `SkillEditDrawer` load/save happy
  path (now reachable); typecheck clean for changed files.
- Full suites: `uv run pytest apps/backend/tests/ -v`,
  `cd apps/frontend && npx vitest run`, `npm run typecheck`.

## Constraints

- No routes in `entrypoints/api.py`.
- SQLAlchemy ORM only.
- Origin is derived from `source_type` (`user_input` → manual, `ai_generated`
  → AI). No new DB columns.
- Rule 13: wireframe/UX docs updated for the row + detail drawer changes.
