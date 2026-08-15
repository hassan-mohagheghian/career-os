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

# Ensure apps/backend/ is on sys.path so bare imports (shared.*, dependencies, etc.) work
_server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from shared.infrastructure.config.app_config import STATIC_FOLDER
from shared.infrastructure.process.logging_config import setup_logging, get_logger


def _read_version() -> str:
    """Read the repo version from the VERSION file at the repository root."""
    version_file = os.path.join(os.path.dirname(os.path.dirname(_server_dir)), "VERSION")
    try:
        with open(version_file) as f:
            return f.read().strip()
    except OSError:
        return "0.0.0"

# ── Logging ────────────────────────────────────────────────────────

_log_dir = os.path.join(_server_dir, 'logs')
setup_logging(log_dir=_log_dir, level='INFO')
log = get_logger('fastapi')


# ── Lifespan ──────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    from shared.infrastructure.config.db import init_db
    # Startup
    log.info("fastapi.startup")

    # Initialize database tables and seed data
    init_db()
    log.info("fastapi.database_ready")

    # Recover interrupted tasks
    _recover_tasks()

    yield

    # Shutdown
    log.info("fastapi.shutdown")
    log.info("fastapi.shutdown_complete")


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
                        job['id'], status='pending', error='Interrupted by server restart',
                        failure_reason='Server restart', failure_timestamp=now,
                        updated_at=now,
                    )

            stuck_companies = company_repo.get_processing_items()
            if stuck_companies:
                log.info("fastapi.recovery_stuck_companies", count=len(stuck_companies))
                for company in stuck_companies:
                    company_repo.update_fields(
                        company['id'], status='pending', error='Interrupted by server restart',
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
        version=_read_version(),
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

    # ── Processing-events SSE (no /api prefix — frontend subscribes at /events/processing) ──
    from shared.presentation.api.processing_events_router import router as processing_events_router
    app.include_router(processing_events_router, prefix="/events", tags=["processing-events"])

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
app = fastapi_app

# ── Run ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.backend.entrypoints.api:fastapi_app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        reload=True,
    )
