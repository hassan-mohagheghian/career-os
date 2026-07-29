"""FastAPI application entry point.

This is the primary server for the Job Search Intelligence platform.
Replaces Flask as the main backend server.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import time

# Ensure app/server/ is on sys.path so bare imports (shared.*, dependencies, etc.) work
_server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from shared.infrastructure.config.app_config import DB_PATH, STATIC_FOLDER
from shared.infrastructure.process.logging_config import setup_logging, get_logger

# ── Logging ────────────────────────────────────────────────────────

_log_dir = os.path.join(_server_dir, 'logs')
setup_logging(log_dir=_log_dir, level='INFO')
log = get_logger('fastapi')


# ── SocketIO Server ───────────────────────────────────────────────

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')


@sio.event
async def connect(sid, environ):
    log.info("socketio.connect", sid=sid)


@sio.event
async def disconnect(sid):
    log.info("socketio.disconnect", sid=sid)


@sio.event
async def watch_job(sid, data):
    pid = data.get('id')
    if pid:
        await sio.enter_room(sid, f'job_{pid}')
        log.info("socketio.watch", room=f'job_{pid}')


@sio.event
async def unwatch_job(sid, data):
    pid = data.get('id')
    if pid:
        await sio.leave_room(sid, f'job_{pid}')


@sio.event
async def watch_company(sid, data):
    pid = data.get('id')
    if pid:
        await sio.enter_room(sid, f'company_{pid}')
        log.info("socketio.watch", room=f'company_{pid}')


@sio.event
async def unwatch_company(sid, data):
    pid = data.get('id')
    if pid:
        await sio.leave_room(sid, f'company_{pid}')


@sio.event
async def watch_generation(sid, data):
    gen_id = data.get('id')
    if gen_id:
        await sio.enter_room(sid, f'generation_{gen_id}')
        log.info("socketio.watch", room=f'generation_{gen_id}')


@sio.event
async def unwatch_generation(sid, data):
    gen_id = data.get('id')
    if gen_id:
        await sio.leave_room(sid, f'generation_{gen_id}')


@sio.event
async def watch_skills(sid):
    await sio.enter_room(sid, 'skills')
    log.info("socketio.watch", room='skills')


@sio.event
async def unwatch_skills(sid):
    await sio.leave_room(sid, 'skills')


@sio.event
async def cancel_job(sid, data):
    pid = data.get('id')
    entity_type = data.get('entity_type', 'job')
    if pid:
        from dependencies import get_session_sync
        session = get_session_sync()
        try:
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                from datetime import datetime, UTC
                repo.update_fields(pid, status='cancelled', updated_at=datetime.now(UTC).isoformat())
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                from datetime import datetime, UTC
                repo.update_fields(pid, status='cancelled', updated_at=datetime.now(UTC).isoformat())
            log.info("socketio.cancel", pid=pid, success=True)
        finally:
            session.close()


@sio.event
async def reset_job(sid, data):
    pid = data.get('id')
    entity_type = data.get('entity_type', 'job')
    if pid:
        from dependencies import get_session_sync
        session = get_session_sync()
        try:
            from datetime import datetime, UTC
            now = datetime.now(UTC).isoformat()
            if entity_type == 'job':
                from jobs.infrastructure import SQLAlchemyJobRepository
                repo = SQLAlchemyJobRepository(session)
                repo.update_fields(pid, status='pending', error=None, current_node=None,
                    progress_pct=0, retry_count=0, failure_reason=None,
                    failure_step=None, failure_timestamp=None, updated_at=now)
            else:
                from companies.infrastructure import SQLAlchemyCompanyRepository
                repo = SQLAlchemyCompanyRepository(session)
                repo.update_fields(pid, status='pending', error=None, current_node=None,
                    progress_pct=0, retry_count=0, failure_reason=None,
                    failure_step=None, failure_timestamp=None, updated_at=now)
            log.info("socketio.reset", pid=pid, success=True)
        finally:
            session.close()


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    from shared.infrastructure.config.db import init_db
    from shared.infrastructure.queue.arq_client import get_arq_pool, close_arq_pool

    # Startup
    log.info("fastapi.startup")

    # Run Alembic migrations for schema management
    _run_alembic_migrations()
    log.info("fastapi.alembic_migrations_complete")

    # Initialize database tables and seed data
    init_db()
    log.info("fastapi.database_ready")

    # Initialize ARQ connection pool
    try:
        await get_arq_pool()
        log.info("fastapi.arq_pool_ready")
    except Exception as e:
        log.warning("fastapi.arq_pool_init_failed", error=str(e))

    # Recover interrupted tasks
    _recover_tasks()

    yield

    # Shutdown
    log.info("fastapi.shutdown")
    try:
        await close_arq_pool()
    except Exception as e:
        log.warning("fastapi.arq_pool_close_error", error=str(e))
    log.info("fastapi.shutdown_complete")


def _run_alembic_migrations():
    """Run Alembic migrations to ensure database schema is up to date."""
    import subprocess
    try:
        project_dir = os.path.join(_server_dir, '..', '..')
        result = subprocess.run(
            [os.path.join(project_dir, '.venv', 'bin', 'alembic'), 'upgrade', 'head'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.warning("alembic.warning", stderr=result.stderr)
        else:
            log.info("alembic.success", output=result.stdout.strip())
    except FileNotFoundError:
        log.warning("alembic.not_found", message="alembic not found, skipping schema migrations")
    except subprocess.TimeoutExpired:
        log.warning("alembic.timeout", message="alembic migration timed out")
    except Exception as e:
        log.warning("alembic.error", error=str(e))


def _recover_tasks():
    """On startup, check for interrupted tasks and mark them as failed."""
    try:
        from dependencies import get_session_sync
        from jobs.infrastructure import SQLAlchemyJobRepository
        from companies.infrastructure import SQLAlchemyCompanyRepository
        from datetime import datetime, UTC

        session = get_session_sync()
        try:
            job_repo = SQLAlchemyJobRepository(session)
            company_repo = SQLAlchemyCompanyRepository(session)
            now = datetime.now(UTC).isoformat()

            stuck_jobs = job_repo.get_processing_items()
            if stuck_jobs:
                log.info("fastapi.recovery_stuck_jobs", count=len(stuck_jobs))
                for job in stuck_jobs:
                    job_repo.update_fields(
                        job['num'], status='failed', error='Interrupted by server restart',
                        failure_reason='Server restart', failure_timestamp=now,
                        updated_at=now,
                    )

            stuck_companies = company_repo.get_processing_items()
            if stuck_companies:
                log.info("fastapi.recovery_stuck_companies", count=len(stuck_companies))
                for company in stuck_companies:
                    company_repo.update_fields(
                        company['id'], status='failed', error='Interrupted by server restart',
                        failure_reason='Server restart', failure_timestamp=now,
                        updated_at=now,
                    )
        finally:
            session.close()
    except Exception as e:
        log.warning("fastapi.recovery_failed", error=str(e))


# ── App Factory ──────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Job Search Intelligence API",
        description="AI-powered career intelligence platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging Middleware ────────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    # ── Exception Handlers ───────────────────────────────────────
    from shared.application.exceptions import AppError
    from shared.presentation.error_handler import app_error_handler as _app_error_handler

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return await _app_error_handler(request, exc)

    # ── Register API Routers ─────────────────────────────────────
    from shared.presentation.api.root_router import api_router
    app.include_router(api_router)

    # ── Health Check ─────────────────────────────────────────────
    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    # ── Static Files (Frontend) ──────────────────────────────────
    if os.path.isdir(STATIC_FOLDER):
        from fastapi.responses import FileResponse
        app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_FOLDER, "assets")), name="assets")
        index_html = os.path.join(STATIC_FOLDER, "index.html")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = os.path.join(STATIC_FOLDER, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(index_html)

    return app


# ── App Instance ─────────────────────────────────────────────────

fastapi_app = create_app()

# Wire SocketIO to the broadcaster for real-time events
from shared.infrastructure.process_utils import broadcaster as _shared_broadcaster
_shared_broadcaster.set_socketio(sio)

# Also wire the new WebSocket broadcaster
from shared.infrastructure.websocket.broadcaster import set_socketio_server
set_socketio_server(sio)

# Wrap with SocketIO for real-time events
app = socketio.ASGIApp(sio, fastapi_app)


# ── Run ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.server.entrypoints.api:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        reload=True,
    )
