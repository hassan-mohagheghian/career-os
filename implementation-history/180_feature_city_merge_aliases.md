# Prompt 180 - Feature: City Merge & Aliases (canonical cities)

## Objective

Give the Cities page the ability to **merge cities** and manage **aliases** so
that one city can be canonical, mirroring the existing Skills pattern
(soft-hidden merged-away rows, an alias table, "make canonical", merge-into).
When two rows represent the same physical place (e.g. "München, Germany" and
"Munich, Germany"), a user can merge one into the other: the merged-away city
becomes hidden and its name becomes an alias of the target, and every logical
reference (`jobs.city_id`, `companies.city_id`, `candidate_profiles.city_id`)
plus the denormalized `city`/`country` text is re-pointed to the target.

## Current State

- `apps/backend/cities/` context (prompt 179): `City` entity + `CityNormalizer`,
  `CityModel` (schema `city`, table `cities`, `UniqueConstraint(city, country)`,
  columns `id/city/country/original_text/address/created_at/updated_at`),
  `ICityRepository` (`find_by_city_country`, `create`, `list_with_job_counts`),
  `SQLAlchemyCityRepository`, `CityService` (`ensure`, `normalize`, `normalize_and_ensure`)
  emitting `CityCreated`, `cities_router` `GET /cities/list`, schemas.
- Cities are referenced by logical `city_id` columns on jobs/companies/candidate
  profiles (no cross-context FK, rule 15). Cross-context writes during merge are
  done via the shared SQLAlchemy session (application-level integrity).
- Skills merge/alias pattern to mirror:
  `apps/backend/skills/infrastructure/repositories/sa_skill_repository.py`
  (`merge`, `_fold_mentions`, `add_alias`, `remove_alias`, `promote_alias_to_canonical`),
  `apps/backend/skills/presentation/api/skills_router.py`, frontend
  `features/skills-v2/components/MergeSkillDialog.tsx`, `SkillEditDrawer.tsx`,
  `SkillRow.tsx`, `SkillsToolbar.tsx`, `SkillsPage.tsx`.
- Frontend cities page (prompt 179) is read-only: `entities/city`,
  `features/cities-v2` (CitiesPage/Header/Toolbar/Table/Row), `widgets/cities-page`,
  `app/cities/page.tsx`. No drawer currently.

## Implementation Steps

1. **Model** (`apps/backend/cities/infrastructure/models/city_model.py`):
   add `hidden: int default 0` to `CityModel`; add `CityAliasModel`
   (table `city_aliases`, schema `city`): `id` String36 uuid7 PK, `city_id`
   String36 (FK to `city.cities.id` — within-context, OK per rule 15),
   `alias_name` String, `normalized_name` String default "", `created_at` Text.
   No unique constraint on `alias_name` (mirror Skills).
2. **Entity + mapper**: add `hidden` to `City` and `city_model_to_dict`;
   mapper gains an optional `aliases: list[str]` for the list payload.
3. **Repository port** (`city_repository.py`): add `get_by_id`,
   `merge(target_id, source_ids)`, `add_alias(skill_id, alias_name)`,
   `remove_alias`, `promote_alias_to_canonical`.
4. **SACityRepository**: implement merge (soft-hide source `hidden=1`, add
   source city name as alias of target if absent, re-point logical references on
   `jobs`/`companies`/`candidate_profiles` and their denormalized city/country to
   the target), alias add/remove, promote (swap canonical `city`, old canonical
   becomes an alias), and `get_aliases`. Make `list_with_job_counts` filter
   `hidden == 0` and attach `aliases`.
5. **Service + events** (`city_service.py`, `events.py`): add `merge`,
   `add_alias`, `remove_alias`, `promote_alias_to_canonical` delegating to the
   repo and emitting `CityMerged` (`city.merged`) and `CityCanonicalChanged`
   (`city.canonical.changed`). Event publisher stays the in-memory collector.
6. **Router + schemas** (`cities_router.py`, `schemas/cities.py`):
   `POST /cities/merge` (`{target_id, source_ids}`), `POST /cities/{id}/aliases`
   (`{alias_name}`), `DELETE /cities/{id}/aliases?alias_name=`, `PATCH
   /cities/{id}/canonical` (`{alias_name}`). Validation: empty source_ids → 400,
   target-in-sources → 400, missing → 404, alias-not-an-alias → 400,
   promotion collision → 409. Add `aliases: list[str]` to `CityListItemSchema`.
7. **Migration** (autogenerate-then-tune): add `hidden` to `cities` and create
   `city_aliases`; single head, verify up/downgrade round-trip.
8. **Frontend** (`entities/city`, `features/cities-v2`): types + api
   (`merge`, `addAlias`, `removeAlias`, `promoteAliasToCanonical`) + hooks
   (invalidate `cities-infinite`); `MergeCityDialog` (copy of `MergeSkillDialog`);
   `CityEditDrawer` (aliases CRUD + Make canonical + Merge into another city);
   row alias badge + row merge action; toolbar bulk-selection merge bar; wire
   into `CitiesPage`/`CitiesTable`/`CityRow`/`CitiesToolbar`.
9. **Docs**: `docs/api/cities/merge-cities.md` + `aliases.md`, `docs/domain/cities/events.md`
   (add CityMerged + CityCanonicalChanged), `docs/domain/cities/cities.md`,
   `docs/ux/features/cities/page.md` + `edit-city.md` + `docs/ux/flows/cities/merge-cities.md`
   (ASCII wireframe + Mermaid), index `docs/ux/README.md` + `DESIGN.md`.

## Testing

- Backend: `tests/cities/` — repo merge (re-points jobs/companies/profiles,
  hidden source, alias added, job_count folds), alias add/remove, promote
  (old canonical becomes alias), list excludes hidden + includes aliases; API
  tests for merge/aliases/canonical incl. 400/404/409; event emission via
  `InMemoryEventCollector`. Run `uv run pytest apps/backend/tests/ -q`.
- Frontend: `MergeCityDialog` test (candidates exclude sources), city api tests;
  `npx vitest run` + `npx tsc --noEmit`.

## Constraints

- Cross-context references re-pointed at the repository layer via the shared
  session (no cross-context FK, rule 15).
- Merge soft-hides; never hard-deletes the merged-away city (keeps lineage).
- All AI calls via LLMService — none added here.
- Default sort stays jobs count desc; merged/hidden cities excluded from list.
- One prompt = one commit (with this file).
