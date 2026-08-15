# Prompt 159 - Separate migrations from app startup

## Objective

Separate "running the app" from "applying DB migrations". Migrations must only
ever be applied via an explicit standalone migration step — never implicitly as
part of starting the backend. This lets a developer apply migrations on their
own, before running the apps. In Docker, migrations already run as a standalone
`alembic` compose service; keep it that way (it is the only migration path).

## Current state

Two code paths run migrations implicitly every time the backend starts:

1. `apps/backend/entrypoints/api.py` — the FastAPI `lifespan` calls
   `_run_alembic_migrations()` on startup (used by the production Docker
   backend image, whose `CMD` runs `uvicorn apps.backend.entrypoints.api:app`).
2. `apps/start.py` — `_start_backend()` (used by `start dev`) and the `backend`
   command both call `_run_migrations()` before launching uvicorn.

Docker already has a standalone `alembic` compose service (`command: uv run
alembic upgrade head`), and `backend`/`background` depend on it via
`service_completed_successfully`. This is the correct "standalone" pattern and
must be preserved.

## Implementation steps

1. `apps/start.py`:
   - Remove the `_run_migrations()` call inside `_start_backend()` (removes the
     implicit migration for both `dev` and `backend`).
   - Remove the `_run_migrations()` call inside the `backend` command.
   - Delete the now-unused `_run_migrations()` helper.
   - The `migrate` command and `db up/down/new` subcommands remain the only
     migration paths via the `start` CLI.
2. `apps/backend/entrypoints/api.py`:
   - Remove the `_run_alembic_migrations()` call and its log line from the
     `lifespan` startup.
   - Delete the now-unused `_run_alembic_migrations()` function.
3. `apps/backend/tests/entrypoints/test_api_entrypoint.py`:
   - Remove the `TestRunAlembicMigrations` class (the function no longer
     exists); keep `TestRecoverTasks`, `TestCreateApp`, `TestAsgiApp`.
4. Docs (TDD: docs updated before code):
   - `docs/database/alembic-guide.md`: correct the Docker service name
     (`alembic-migrate` → `alembic`) and state explicitly that migrations are
     NOT run automatically on app startup — run `./start migrate` (or
     `./start db up`) locally, or the standalone `alembic` compose service in
     Docker.
   - `README.md` Quick Start: add `./start migrate` before `./start`.
   - `AGENTS.md` Quick Start: add `./start migrate` before `./start`.

## Testing requirements

- `uv run pytest apps/backend/tests/entrypoints/test_api_entrypoint.py -q`
  passes (migration class removed, rest intact).
- `uv run pytest apps/backend/tests/shared/presentation/api/test_root_router_compat.py -q`
  (exercises the lifespan path) passes.
- Ruff clean on changed files: `uv run ruff check apps/backend apps/start.py`.

## Constraints

- No behavior change to the migration commands themselves; only the implicit
  triggers are removed.
- Docker migration stays standalone (the `alembic` compose service); do not add
  any migration call into the backend/background image startup.
- Follow AGENTS.md: implementation-history first (this file), docs/tests before
  code, no comments added to code.
