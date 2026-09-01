# Prompt 203 - Backend Authentication (JWT + User Model)

## Objective

Introduce JWT-based authentication to the backend. Create an `auth` bounded context with User model, registration, login, and a FastAPI dependency for extracting the current user from JWT tokens. Seed a default user.

## Current State

- Completely unauthenticated — no User model, no auth middleware, no JWT
- Backend: `apps/backend/entrypoints/api.py` with lifespan, CORS, request logging
- DI: `apps/backend/dependencies.py` — centralized repo/service injection via `Depends()`
- DB: PostgreSQL with 11 schemas (per bounded context), `SCHEMAS` dict in `sqlalchemy_config.py`
- No bcrypt/passlib installed — need `bcrypt` + `PyJWT` (both now in pyproject.toml)
- `.env` has no auth-related vars

## Changes

### 1. Auth Bounded Context (`apps/backend/auth/`)
- `domain/user.py` — User entity (id, username, display_name, password_hash, created_at, updated_at)
- `domain/user_repository.py` — RepositoryInterface for User
- `infrastructure/user_model.py` — SQLAlchemy model (`auth.users` table)
- `infrastructure/user_repository.py` — SQLAlchemy implementation
- `infrastructure/__init__.py` — exports
- `application/auth_service.py` — register (hash password), login (verify + JWT), get_current_user (decode JWT)
- `presentation/api/auth_router.py` — POST /register, POST /login, GET /me
- `presentation/api/schemas.py` — Pydantic request/response schemas

### 2. Database
- Add `"auth": ["users"]` to `SCHEMAS` dict in `sqlalchemy_config.py`
- Add `apps/alembic/auth/versions/` to `alembic.ini` version_locations
- Create Alembic migration: `auth_001_initial_auth_schema.py`

### 3. Configuration
- Add `JWT_SECRET` and `JWT_ALGORITHM` and `JWT_EXPIRATION_HOURS` to `.env` and `app_config.py`
- Add `DEFAULT_USER_USERNAME` and `DEFAULT_USER_PASSWORD` and `DEFAULT_USER_DISPLAY_NAME` to `.env`

### 4. Auth Dependency
- Add `get_current_user` dependency to `dependencies.py` — extracts JWT from Authorization header, validates, returns User

### 5. Seed Default User
- In `init_db()` or lifespan, create default user if not exists

### 6. Register Router
- Add auth router to `root_router.py` at `/api/auth`
- Auth endpoints are PUBLIC (no `get_current_user` required for register/login/me)

## Testing Requirements

```bash
uv run pytest apps/backend/tests/ -v
```

## Constraints

- Auth endpoints (`/register`, `/login`, `/me`) must NOT require auth (circular)
- Passwords hashed with bcrypt
- JWT tokens expire after 1 day
- Follow DDD: auth is its own bounded context
- No cross-context FKs
- Use structlog for logging
