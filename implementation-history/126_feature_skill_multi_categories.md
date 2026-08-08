# Prompt 126 - Skill Multi-Categories with Dynamic Catalog and Alias Inheritance

## Objective

A skill can belong to **multiple categories**, categories are **no longer a
hardcoded list** — users can create new ones — and **aliases inherit the
categories of their canonical skill**.

## Current State

- `skill.skills.category` is a single string; the valid set is hardcoded as
  `SKILL_CATEGORIES = ("technical", "engineering", "professional", "domain",
  "career")` in `apps/backend/skills/presentation/api/skills_router.py` and as
  a frontend const in `apps/frontend/src/entities/skill/types.ts`.
- `GET /api/skills/categories` aggregates counts from the `skills.category`
  column. There is no category catalog table and no endpoint to create one.
- Skill rows that are registered as an alias of another skill (e.g. an
  `ai_generated` "K8s" row whose name is an alias of "Kubernetes") keep their
  own `category`; they do **not** inherit the canonical skill's category.

## Design (Best Practices)

### Data model (skill schema — all FKs stay within the context, rule 15)

- New `skill.skill_categories` — category catalog:
  `id`, `name` (unique, not null), `created_at`. Seeded with the five canonical
  categories; users can add more via a new endpoint.
- New `skill.skill_category_links` — M2M association:
  `id`, `skill_id` (FK `skill.skills.id`), `category_id` (FK
  `skill.skill_categories.id`), `created_at`, `UniqueConstraint(skill_id,
  category_id)`.
- `skill.skills.category` is kept as the denormalized **primary category** and
  is always kept equal to `categories[0]` (or `""`) — backward compatible with
  the AI intelligence graph and the legacy single-category API.
- Migration backfills links from existing `skills.category` values and seeds the
  canonical catalog.

### Read-time alias inheritance

Effective categories for a skill row = **its own linked categories ∪ the
canonical skill's categories** when the row's name is registered as an alias of
that canonical skill (one level, mirroring `get_mention_counts` alias folding).
The primary `category` falls back to the canonical's first category when the row
has none of its own. Applied in the list response, detail response, the category
filter, and category counts.

### Dynamic catalog

- `GET /api/skills/categories` — returns the catalog with per-category counts
  (visible skills), demand/level averages.
- `POST /api/skills/categories` — create a new category (idempotent, returns the
  existing row when it already exists).
- `DELETE /api/skills/categories/{name}` — delete an unused category; 409 when
  any skill is still linked to it.
- Assigning a category to a skill auto-creates it in the catalog (no separate
  step required).

### EDD (AGENTS.md rule 16)

New events in `apps/backend/skills/domain/events.py`, published via a new port
`apps/backend/skills/domain/event_publisher.py` (in-memory collector — no
transport):

- `skill.category.created` (`SkillCategoryCreated`) — a category was added.
- `skill.category.deleted` (`SkillCategoryDeleted`) — an unused category was
  removed.
- `skill.categories.changed` (`SkillCategoriesChanged`) — a skill's category set
  changed (create/update/categorize/bulk-categorize).

Emission is handled by a new application service
`apps/backend/skills/application/use_cases/skill_category_service.py` — never by
callers (rule 16b). The router's category/skill-update routes delegate to it.

## Implementation Steps

1. Write backend tests first (TDD red): multi-category create/update/list/filter,
   category catalog CRUD, alias category inheritance, event emission.
2. Models + Alembic autogenerate for the skill schema; tune the migration with
   seed + backfill; verify upgrade/downgrade.
3. Repository (`sa_skill_repository.py` + `ISkillRepository`): `set_categories`,
   `get_categories` (catalog), `create_category`, `delete_category`,
   effective-categories helper with alias inheritance; update `create`, `update`,
   `resolve_skill`, `create_from_dict`, `list_visible`, `bulk_categorize`.
4. Events + publisher + `SkillCategoryService`.
5. Schemas + router: add `categories` to create/update/response schemas, new
   category endpoints, drop hardcoded category validation (auto-create instead).
6. Frontend: fetch categories dynamically; multi-category picker with "create
   new"; toolbar filter from catalog; row primary badge + count; detail drawer
   shows all category badges.
7. Docs: `docs/ux/features/skills/*`, `docs/ux/flows/skills/browse-skills.md`,
   `docs/api/skills/*` (+ category endpoints), new `docs/domain/skills/events.md`,
   `DESIGN.md` wireframes, `docs/ux/README.md`.
8. Version bump (MINOR) → 3.11.0 across VERSION / CHANGELOG / pyproject.toml /
   apps/frontend/package.json; verify `./scripts/check-version.sh`.

## Testing Requirements

- `uv run pytest apps/backend/tests/ -v`
- `cd apps/frontend && npx vitest run`
- `cd apps/frontend && npm run lint && npm run typecheck`
- `./scripts/check-version.sh`
- `uv run alembic upgrade head` + downgrade/upgrade round-trip against a dev DB.

## Constraints

- No cross-context FKs (category tables stay inside the `skill` schema).
- Keep `skills.category` (primary) in sync whenever categories change.
- No pub/sub transport — in-memory collector only.
- Aliases inherit categories at read time (own ∪ canonical), matching the
  existing read-time mention folding.
