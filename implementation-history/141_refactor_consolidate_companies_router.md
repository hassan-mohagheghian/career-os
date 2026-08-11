# Prompt 141 - Consolidate companies router into companies_v2_router

## Objective

Delete the last legacy companies router so the app is fully on the V2
companies API. The V2 router already owns list (`/companies/list`), detail
(`/companies/{id}`), pinned, and main endpoints; this prompt moves the
remaining create / update / delete / notes / links / reprocess endpoints from
`companies_router.py` into `companies_v2_router.py`, then removes the legacy
files.

## Current State

- `apps/backend/companies/presentation/api/companies_router.py` registers:
  - `POST /companies` → `create_company` (intake create + queue)
  - `PUT /companies/{id}` → `update_company`
  - `DELETE /companies/{id}` → `delete_company` (hard delete cascade)
  - `GET/POST/PUT/DELETE /companies/{id}/notes[/{note_id}]`
  - `POST/PUT/DELETE /companies/{id}/links[/{link_id}]`
- `companies_v2_router.py` is registered first in `root_router.py`, so the
  paths survive the move unchanged.
- `shared/presentation/api/root_router.py` includes both routers; the legacy
  one must be dropped after the move.
- `reprocess_company` currently lives in `shared/presentation/api/root_router.py`
  and must move into the companies context router alongside the rest.

## Changes

- Port `create_company`, `update_company`, `delete_company`, the notes CRUD
  (`get/add/update/delete`), the links CRUD (`add/update/delete`), and
  `reprocess_company` into `companies_v2_router.py`.
- Add the request schemas to `schemas/companies_v2.py`
  (`CompanyCreateRequest`, `CompanyCreateResponse`, `CompanyUpdateRequest`,
  `CompanyNoteSchema`, `CompanyLinkSchema`).
- Add `update()` to `CompanyLinkRepository` /
  `SQLAlchemyCompanyLinkRepository` so link edits have a repository method.
- Delete `companies_router.py` and `schemas/companies.py`.
- Update `root_router.py`: remove the legacy router import/include and the
  standalone reprocess route.
- Update `docs/api/api-design.md` companies table + router snippet.

## Testing Requirements

- `apps/backend/tests/companies/presentation/api/test_companies_v2_api.py` is
  extended to cover create (with/without queue), update, delete, notes CRUD,
  links CRUD, and reprocess against the v2 router.
- `apps/backend/tests/shared/presentation/api/test_root_router_compat.py`
  create-company compat tests keep passing against the moved route.
- `apps/backend/tests/jobs/presentation/api/test_integration_jobs.py` keeps
  passing (it hits company create via the root router path).
- Grep confirms no references to `companies_router` or `schemas.companies`
  remain in `apps/backend/`.

## Constraints

- No schema/DB change, no migration, no version bump.
- Keep the exact response shapes (`201` create with
  `response_model_exclude_none`, `204` deletes) and the `JobAlreadyExistsError`
  style duplicate handling.
- Do not declare foreign keys across contexts (notes/links stay plain JSON or
  intra-context tables).
