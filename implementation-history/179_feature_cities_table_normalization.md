# Prompt 179 - Feature: Cities Table & Normalization

## Objective

Introduce a **cities** bounded context: a normalized catalog of locations with a
dedicated page (like Companies/Skills). Every city stored on jobs, companies,
and the candidate profile must be **normalized to a unique canonical
`{city, country}`** and **linked to a row** in the cities table. The cities
page lists each city with its country and the number of jobs, default-sorted by
jobs count (desc), and sortable by jobs count, country, and city. The legacy
`shared.cities` table and the dashboard `GET /api/cities` endpoint are removed.

Normalization = extracting, for each city, a **unique canonical city + country**
(e.g. "berlin" → city `Berlin`, country `Germany`; "München" → `Munich`,
`Germany`).

## Current State

- Jobs store a single free-form `location` string + a `locations` JSON array
  (`apps/backend/jobs/infrastructure/models/job_model.py`). No country/city split.
- Companies already store `city` and `country`
  (`apps/backend/companies/infrastructure/models/company_model.py`).
- Candidate profile stores a single `location` string
  (`apps/backend/candidates/infrastructure/models/candidate_model.py`).
- Legacy: `shared.cities` table
  (`apps/alembic/shared/versions/shared_001_initial_shared_schema.py`) and the
  dashboard `GET /api/cities` endpoint
  (`apps/backend/shared/presentation/api/dashboard_router.py`) — to be removed.
- Frontend: nav config `apps/frontend/src/widgets/sidebar/nav-items.ts`
  (Companies at index 1). Companies page is the template
  (`widgets/companies-page`, `features/companies-v2`, `entities/company`).
- AGENTS.md rules honored: per-context router (10), Alembic autogenerate-then-tune
  (14), no cross-context FKs (15), EDD events (16), no raw SQL (2), UI wireframe
  docs (13), implementation-history before code.

## Implementation Steps

1. **City backend context** (`apps/backend/cities/`, schema `city`, table
   `cities`): domain (`City` entity, `ICityRepository`), infrastructure
   (`CityModel` + `SQLAlchemyCityRepository`), application (`CityService.ensure`,
   `CityNormalizer`), presentation (`cities_router.py` `GET /cities/list` +
   schemas). Columns: `id`, `city`, `country`, `original_text` (Text, truncate),
   `address` (Text, truncate), `created_at`, `updated_at`, `UniqueConstraint(city,
   country)`.
2. **Normalization**: `CityNormalizer.normalize(raw) -> (city, country)` — alias
   map (München→Munich, Köln→Cologne, Zürich→Zurich, Wien→Vienna), known
   city→country map (Berlin→Germany, …), parse "City, Country", handle
   Remote/Germany/Europe; unknown → title-case token, empty country.
3. **city_id linkage**: add `city_id` (String 36) + denormalized `city`/`country`
   to `jobs`; add `city_id` to `companies`; add `city_id`, `city`, `country`,
   `original_text`, `address` to `candidate_profiles`. No cross-context FKs
   (plain columns only).
4. **Persist wiring**: run `CityService.ensure` during job persist, company
   persist, and profile persist; store the derived city_id/city/country (+
   original_text/address for profile).
5. **Backfill**: `apps/backend/cities/application/commands/backfill_cities.py`
   iterates existing jobs (location) and companies (city/country), normalizes,
   upserts city rows, sets `city_id` (+ denormalized city/country on jobs).
6. **Config wiring**: `alembic.ini` `version_locations` += `city/versions`;
   `apps/alembic/env.py` import city models; `SCHEMAS["city"] = ["city"]` and
   remove `"cities"` from `SCHEMAS["shared"]` in `sqlalchemy_config.py`; mount
   `cities_router` at `/api/cities` in `root_router.py`; `get_city_repo` in
   `dependencies.py`.
7. **Migrations (autogenerate-then-tune)**: `city_001` creates `city` schema +
   `cities` table; a migration adds `city_id`/`city`/`country` to jobs, `city_id`
   to companies, the 5 columns to candidate_profiles; a migration drops the
   legacy `shared.cities` table.
8. **Legacy removal**: delete dashboard `GET /api/cities` handler + the
   `shared.cities` table.
9. **Frontend**: `entities/city` (types/api/hooks), `features/cities-v2`
   (`CitiesPage/Header/Toolbar/Table/Row`), `widgets/cities-page`,
   `app/cities/page.tsx`; insert `{ id:'cities', label:'Cities', icon: MapPin }`
   in `nav-items.ts` after Companies. Columns: City, Country, Jobs — Jobs is
   default-sorted desc; sortable by Jobs/Country/City.
10. **Consistency**: add shared `formatLocation(city, country)`; apply to
    `JobRow`, `CompanyRow`, `CompanyDetailDrawer` city rendering.

## Testing

- Backend: `tests/cities/` (normalizer, service, repository, router), backfill
  test, jobs/company/profile persist wiring tests, legacy-removal test.
- Frontend: `entities/city/api.test.ts`, `CitiesTable`/page tests.
- Run `uv run pytest apps/backend/tests/ -q` and
  `cd apps/frontend && npx vitest run` + `npx tsc --noEmit`.

## Constraints

- All AI calls via LLMService (no change to live AI prompt schemas in this
  prompt — normalization happens at persist/backfill via `CityNormalizer`).
- No cross-context FKs. Default sort newest first applies where relevant; the
  cities list default sort is **jobs count desc** (explicit requirement).
- Commit this prompt + code together as one change.