"""FastAPI application entry point.

This is the primary server for the Job Search Intelligence platform.
Replaces Flask as the main backend server.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

import os
import time

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config import DB_PATH, STATIC_FOLDER
from services.process.logging_config import setup_logging, get_logger

# ── Logging ────────────────────────────────────────────────────────

_server_dir = os.path.dirname(os.path.abspath(__file__))
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
async def watch_pending(sid, data):
    pid = data.get('id')
    if pid:
        await sio.enter_room(sid, f'pending_{pid}')
        log.info("socketio.watch", room=f'pending_{pid}')


@sio.event
async def unwatch_pending(sid, data):
    pid = data.get('id')
    if pid:
        await sio.leave_room(sid, f'pending_{pid}')


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
async def watch_insights(sid):
    await sio.enter_room(sid, 'insights')
    log.info("socketio.watch", room='insights')


@sio.event
async def unwatch_insights(sid):
    await sio.leave_room(sid, 'insights')


@sio.event
async def cancel_job(sid, data):
    pid = data.get('id')
    table = data.get('table', 'pending_jobs')
    if pid:
        from core.queue import get_queue_manager
        ok = get_queue_manager().cancel_job(pid, table)
        log.info("socketio.cancel", pid=pid, success=ok)


@sio.event
async def reset_job(sid, data):
    pid = data.get('id')
    table = data.get('table', 'pending_jobs')
    if pid:
        from core.queue import get_queue_manager
        ok = get_queue_manager().reset_job(pid, table)
        log.info("socketio.reset", pid=pid, success=ok)


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    from migrations import run_migrations
    from core.queue import init_queue_manager

    # Startup
    log.info("fastapi.startup")

    # Run Alembic migrations for schema management
    _run_alembic_migrations()
    log.info("fastapi.alembic_migrations_complete")

    # Run data migrations (backfills, transforms, etc.)
    run_migrations()
    log.info("fastapi.database_ready")

    init_queue_manager(DB_PATH)
    log.info("fastapi.queue_started")

    # Recover interrupted tasks
    _recover_tasks()

    yield

    # Shutdown
    log.info("fastapi.shutdown")
    from core.queue import get_queue_manager
    try:
        get_queue_manager().stop(timeout=15)
    except Exception as e:
        log.warning("fastapi.queue_stop_error", error=str(e))
    log.info("fastapi.shutdown_complete")


def _run_alembic_migrations():
    """Run Alembic migrations to ensure database schema is up to date."""
    import subprocess
    try:
        server_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.join(server_dir, '..', '..')
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
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        conn.row_factory = sqlite3.Row

        # Mark stuck pending jobs as failed
        stuck_jobs = conn.execute(
            "SELECT id, version FROM pending_jobs WHERE status='processing'"
        ).fetchall()
        if stuck_jobs:
            log.info("fastapi.recovery_stuck_jobs", count=len(stuck_jobs))
            for job_id, version in stuck_jobs:
                new_version = (version or 1) + 1
                conn.execute(
                    "UPDATE pending_jobs SET status='failed', error='Interrupted by server restart', version=?, updated_at=datetime('now') WHERE id=?",
                    (new_version, job_id),
                )

        # Mark stuck pending companies as failed
        stuck_companies = conn.execute(
            "SELECT id, version FROM pending_companies WHERE status='processing'"
        ).fetchall()
        if stuck_companies:
            log.info("fastapi.recovery_stuck_companies", count=len(stuck_companies))
            for company_id, version in stuck_companies:
                new_version = (version or 1) + 1
                conn.execute(
                    "UPDATE pending_companies SET status='failed', error='Interrupted by server restart', version=?, updated_at=datetime('now') WHERE id=?",
                    (new_version, company_id),
                )

        conn.commit()
        conn.close()
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
    from exceptions import AppError

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.detail,
                    "details": getattr(exc, "details", None),
                }
            },
        )

    # ── Register API Routers ─────────────────────────────────────
    from api.router import api_router
    app.include_router(api_router)

    # ── Health Check ─────────────────────────────────────────────
    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    # ── Static Files (Frontend) ──────────────────────────────────
    if os.path.isdir(STATIC_FOLDER):
        app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_FOLDER, "assets")), name="assets")

    return app


# ── App Instance ─────────────────────────────────────────────────

fastapi_app = create_app()

# Wire SocketIO to the broadcaster for real-time events
from services.process_utils import broadcaster as _shared_broadcaster
_shared_broadcaster.set_socketio(sio)

# Also wire the new WebSocket broadcaster
from infrastructure.websocket.broadcaster import set_socketio_server
set_socketio_server(sio)

# Wrap with SocketIO for real-time events
app = socketio.ASGIApp(sio, fastapi_app)


# ── Run ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        reload=True,
    )
