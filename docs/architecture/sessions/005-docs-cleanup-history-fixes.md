# Session 005: Documentation Cleanup, History Fixes & Entrypoints Restructure

## Session Goals
- Remove all stale `api/v1/` references from documentation (post-DDD refactor)
- Fix `GenerationHistoryDrawer` to auto-refresh while open
- Fix `pending_generations` history to show completed resume/cover generations
- Restructure CLI and API entry points into `app/server/entrypoints/` package

## Findings

### Documentation Issues
- Multiple docs referenced `app/server/api/v1/` paths that no longer exist after DDD refactor
- Actual route prefix is `/api/` with no versioning — bounded contexts own their routers
- `api/v1/` directory was removed; routers live in `*/presentation/api/*_router.py`
- Test file `test_api_all_endpoints.py` imported from non-existent `api.v1.skill_roadmaps`

### GenerationHistoryDrawer
- Only fetched history on mount (`useEffect` on `open` change)
- No polling or WebSocket subscription — active generations didn't update live
- Other drawers (SkillDetailDrawer, JobDrawer) already had real-time updates via WebSocket

### pending_generations History
- `_query_pending_generations()` called `repo.get_all_active()` which filters `status.in_(["queued", "processing"])`
- Completed/failed resume/cover generations were invisible in the global history
- `get_history_for_job()` existed but only returned results for a specific `job_num`

### Entrypoints Restructure
- CLI and API lived at `app/server/cli.py` and `app/server/main.py` alongside domain code
- DDD bounded context convention: entry points in dedicated `entrypoints/` package
- Path calculations in old `cli.py` and `main.py` used `_server_dir = Path(__file__).parent.parent` which assumed specific file locations
- Bare imports (`from shared...`, `from dependencies...`) require `app/server/` on `sys.path`

## Changes Made

### 1. Documentation — Remove v1 References (11 files)

| File | Change |
|------|--------|
| `docs/api/api-design.md` | Removed "API Versioning" section, updated router org code, replaced all `/api/v1/` with `/api/` |
| `docs/architecture/backend-structure.md` | Replaced folder structure with DDD bounded contexts, updated Migration Mapping table |
| `docs/architecture/modular-monolith.md` | Removed `api/v1/` from folder tree, added `root_router.py` to shared kernel |
| `docs/architecture/folder-structure.md` | Removed `api/` legacy re-export shims section |
| `docs/architecture/code-ownership-map.md` | Removed `api/v1/*.py` from legacy re-export table |
| `docs/architecture/dependency-injection.md` | Updated test example from `/api/v1/jobs` to `/api/jobs` |
| `docs/testing/backend-testing.md` | Replaced all `/api/v1/` with `/api/` in test examples |
| `docs/architecture/sessions/003-generation-history-persistence.md` | Fixed file path references to DDD structure |
| `docs/architecture/sessions/2026-07-27_generation-unification.md` | Fixed file path references to DDD structure |

### 2. Test Fix

| File | Change |
|------|--------|
| `tests/unit/test_api_all_endpoints.py` | Changed `from api.v1.skill_roadmaps import build_roadmap_tree` → `from skills.presentation.api.skill_roadmaps_router import build_roadmap_tree` |

### 3. GenerationHistoryDrawer Auto-Refresh

**File:** `app/client/src/shared/components/GenerationHistoryDrawer.tsx`

- Added `useSocketIO` import and WebSocket subscription hooks
- Added 5-second polling interval while drawer is open
- Subscribes to all relevant WebSocket events: `pending:update`, `generation:update`, `company:update`, `skill_roadmap:update`, `insights:progress`
- Joins rooms: `pending`, `company`, `skills`, `insights`
- Cleans up polling and subscriptions on close

### 4. pending_generations History Fix

**Files:**
- `processing/domain/repositories/pending_generation_repository.py` — Added `get_all(limit)` abstract method
- `processing/infrastructure/repositories/sa_pending_generation_repository.py` — Implemented `get_all(limit)` returning all rows ordered by `created_at desc`
- `shared/infrastructure/repositories/generation_repository.py` — Changed `_query_pending_generations()` from `get_all_active()` to `get_all(limit=200)`

### 5. Entrypoints Restructuring (NEW)

**Created files:**
| File | Description |
|------|-------------|
| `app/server/entrypoints/__init__.py` | New package marker |
| `app/server/entrypoints/cli.py` | Typer CLI (moved from `app/server/cli.py`) — fixed `_server_dir` to use `os.path.dirname()` of `__file__`, `DB_PATH` uses `_server_dir` for `db/` path |
| `app/server/entrypoints/api.py` | FastAPI app factory + SocketIO (moved from `app/server/main.py`) — fixed `_server_dir`, adds `_server_dir` to `sys.path` for bare imports |

**Deleted files:**
- `app/server/cli.py`
- `app/server/main.py`
- `app/server/shared/presentation/cli.py` (duplicate)

**Updated files:**
- `pyproject.toml` — `jobsearch = "app.server.entrypoints.cli:app"`
- `start.sh` — `uvicorn app.server.entrypoints.api:app`, `start_backend()` now runs from `$SCRIPT_DIR` (project root) instead of `$SERVER_DIR`
- `docs/architecture/backend-structure.md` — folder structure updated with `entrypoints/`
- `docs/architecture/modular-monolith.md` — folder structure updated
- `docs/architecture/folder-structure.md` — folder structure updated
- `docs/architecture/ARCHITECTURE.md` — folder structure updated

## Bugs Fixed
1. **Stale v1 references in docs** — 11 files referenced non-existent `api/v1/` paths
2. **Broken test import** — `test_api_all_endpoints.py` imported from deleted `api.v1.skill_roadmaps`
3. **GenerationHistoryDrawer not live** — Active generations didn't update while drawer was open
4. **Completed generations invisible** — Resume/cover generations only showed active items in global history
5. **Entry points mixed with domain code** — CLI and API now have dedicated `entrypoints/` package

## Pending / Future Work
- None — all session goals completed

## File Reference

### Modified Files
| File | Lines Changed |
|------|--------------|
| `docs/api/api-design.md` | ~50 (versioning section + all endpoint tables) |
| `docs/architecture/backend-structure.md` | ~60 (folder structure + migration mapping) |
| `docs/architecture/modular-monolith.md` | ~15 |
| `docs/architecture/folder-structure.md` | ~15 |
| `docs/architecture/code-ownership-map.md` | ~5 |
| `docs/architecture/dependency-injection.md` | ~2 |
| `docs/testing/backend-testing.md` | ~20 |
| `docs/architecture/sessions/003-generation-history-persistence.md` | ~5 |
| `docs/architecture/sessions/2026-07-27_generation-unification.md` | ~5 |
| `tests/unit/test_api_all_endpoints.py` | 4 |
| `app/client/src/shared/components/GenerationHistoryDrawer.tsx` | ~50 |
| `app/server/processing/domain/repositories/pending_generation_repository.py` | 5 |
| `app/server/processing/infrastructure/repositories/sa_pending_generation_repository.py` | 6 |
| `app/server/shared/infrastructure/repositories/generation_repository.py` | 1 |
| `pyproject.toml` | 1 (script entry) |
| `start.sh` | ~10 (uvicorn command + start_backend cwd) |
| `docs/architecture/ARCHITECTURE.md` | ~5 (folder structure) |

### Created Files
| File | Description |
|------|-------------|
| `app/server/entrypoints/__init__.py` | Package marker |
| `app/server/entrypoints/cli.py` | Typer CLI entry point |
| `app/server/entrypoints/api.py` | FastAPI app factory entry point |

### Deleted Files
| File | Reason |
|------|--------|
| `app/server/cli.py` | Moved to `entrypoints/cli.py` |
| `app/server/main.py` | Moved to `entrypoints/api.py` |
| `app/server/shared/presentation/cli.py` | Duplicate of `app/server/cli.py` |
