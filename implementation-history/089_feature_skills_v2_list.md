# Prompt 089 - Skills V2: List Page with Add / Detail / Edit Drawers

## Objective

Bring the Skills workspace to parity with the modern Jobs/Companies (v2) UX: a
virtualized, server-paginated skills table with a header/toolbar (search,
category filter, sort) and Sheet-based Add / Detail / Edit drawers. Replace the
legacy `SkillsTab` card list and its `useSkills` hook entirely.

## Current State

- `GET /api/skills` returns a plain array (`repo.list_visible(category)`),
  ordered by `level desc` — no pagination, search, or sort. Companies v2 has a
  cursor-paginated `/companies/list` endpoint with typed schemas; jobs v2 the
  same via `/jobs/list`.
- The skills table (`SkillModel`) carries `created_at` only (no `updated_at`),
  so rows show a Created column but no Updated column.
- Canonical skill categories (validated in `skills_router`): `technical`,
  `engineering`, `professional`, `domain`, `career`. The legacy `SkillsTab`
  still maps legacy AI badge colors (`language/framework/tool/concept/platform`).
- Frontend legacy: `/skills` route → `widgets/skills-page` → `SkillsTab` (card
  list + category chips + roadmap progress bars) using `features/skills/hooks/
  useSkills.ts` (raw `fetch`, calls nonexistent `/api/skills-intelligence/
  dashboard`). `entities/skill/{types,api}.ts` exist but are minimal and unused.
  `SkillDetailDrawer.tsx` (Details/Roadmap/History tabs + Generate/Extend/
  Finegrain) is worth preserving and extending with Edit + Delete.
- No UX docs exist for skills (`docs/ux/features/skills/` missing) — violates
  AGENTS.md rule 13.

## Implementation Steps

1. Backend — add `GET /api/skills/list` in `skills/presentation/api/skills_router.py`
   (registered before the legacy routes): `query` (substring over name, roles,
   path, aliases), `category` filter, `sort` (`created_at` default desc, plus
   `name`, `level`, `confidence`, `market_relevance`), `order`, `page_size`
   (default 25, max 200), `cursor` (base64 offset, mirrors `companies_v2_router`).
   Filter/sort/paginate in-memory over `repo.list_visible()` (already returns
   full dicts incl. aliases). Response
   `{ items, next_cursor, has_more, total_items }` with typed
   `SkillListItemSchema` (id, name, level, roles, path, category, confidence,
   market_relevance, evidence, tags, aliases, created_at).
2. Frontend entity layer — expand `entities/skill/{types,api}.ts` and add
   `hooks.ts`: `SkillListItem`, `SkillSearchQuery`, `InfiniteSkillSearchResult`;
   `skillApi.listInfinite/create/update/delete/rename/setCategory`;
   react-query `useSkillsInfiniteQuery` (mirroring `useCompaniesInfiniteQuery`)
   plus delete/update mutations and `useCreateSkill`.
3. Frontend UI — new `features/skills-v2/components/`: `SkillsPage` shell
   (header + toolbar + table + drawers + ConfirmDialog), `SkillsHeader`,
   `SkillsToolbar` (DebouncedInput search + canonical-category Select + Clear),
   `SkillsTable` (virtualized + infinite-scroll sentinel, reuse `SortableHeader`),
   `SkillRow` + `skillsColumns`, `SkillDetailDrawer` (migrate the existing
   drawer: keep Details/Roadmap/History tabs + Generate/Extend/Finegrain, add
   Edit in header and Delete in footer), `SkillEditDrawer` (PUT
   `/api/skills/{id}`), `AddSkillDrawer` (POST `/api/skills`).
4. Widget — rewire `widgets/skills-page/index.tsx` to react-query, keep
   `?skill=` deep-link via `setSearchParam`/`getSearchParam`, `ConfirmDialog`
   for delete, `toast` feedback.
5. Cleanup — delete `features/skills/components/SkillsTab.tsx`,
   `features/skills/hooks/useSkills.ts`, `features/skills/components/SkillsTab.test.tsx`.
6. Docs — `implementation-history/089_feature_skills_v2_list.md` (this file);
   `docs/ux/features/skills/{page,skill-row,add-skill,edit-skill,skill-detail}.md`
   with ASCII wireframes; `docs/ux/flows/skills/browse-skills.md`; update
   `docs/ux/README.md`, `DESIGN.md`, `docs/api/api-design.md`, and add
   `docs/api/skills/list-skills.md`.
7. Version — bump `3.5.4` → `3.6.0` across `VERSION`, `CHANGELOG.md`,
   `pyproject.toml`, `apps/frontend/package.json`; run `./scripts/check-version.sh`.

## Testing Requirements

- Backend: list endpoint pagination (cursor, has_more), search across
  name/roles/path/aliases, category filter, sort + empty-value (NULLS) handling,
  default `created_at desc`, total_items.
- Frontend: `SkillsPage` render/empty/error; `SkillRow` columns + actions;
  `AddSkillDrawer` validation/submit; `SkillEditDrawer` load/prefill/save;
  `useSkillsInfiniteQuery` pagination; `SkillDetailDrawer` Edit/Delete wiring.
- Full suites: `uv run pytest apps/backend/tests/ -v` and
  `cd apps/frontend && npx vitest run`, plus `npm run lint` and `npm run typecheck`.

## Constraints

- No routes in `entrypoints/api.py` (per-context routers only).
- All AI calls via `LLMService` (not needed here — no AI work in this change).
- SQLAlchemy ORM only; default sort newest first (`created_at desc`).
- Delete requires a confirm dialog; every card/row has a delete action.
- Rule 13: wireframe docs for every UI change (this change ships its docs).
- Skill categories stay canonical: `technical`, `engineering`, `professional`,
  `domain`, `career`.
