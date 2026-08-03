"""Tests for the FastAPI entrypoint (apps/backend/entrypoints/api.py).

Importing this module runs create_app() at import time, exactly what the
module does in production.
"""

import os
import sys
import subprocess as _subprocess
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from apps.backend.entrypoints import api


# ── _run_alembic_migrations ───────────────────────────────────────

class TestRunAlembicMigrations:
    def test_success(self):
        result = MagicMock()
        result.returncode = 0
        result.stdout = 'upgraded'
        result.stderr = ''
        with patch('subprocess.run', return_value=result) as run_mock:
            api._run_alembic_migrations()
        args = run_mock.call_args[0][0]
        assert args[-2:] == ['upgrade', 'head']
        assert args[0].endswith(os.path.join('.venv', 'bin', 'alembic'))

    def test_nonzero_returncode(self):
        result = MagicMock()
        result.returncode = 1
        result.stderr = 'boom'
        result.stdout = ''
        with patch('subprocess.run', return_value=result):
            api._run_alembic_migrations()

    def test_file_not_found(self):
        with patch('subprocess.run',
                   side_effect=FileNotFoundError('no alembic')):
            api._run_alembic_migrations()

    def test_timeout_expired(self):
        with patch('subprocess.run',
                   side_effect=_subprocess.TimeoutExpired(['alembic'], timeout=30)):
            api._run_alembic_migrations()

    def test_generic_exception(self):
        with patch('subprocess.run',
                   side_effect=RuntimeError('oops')):
            api._run_alembic_migrations()


# ── _recover_tasks ────────────────────────────────────────────────

class TestRecoverTasks:
    def test_stuck_jobs_and_companies(self):
        session = MagicMock()
        job_repo = MagicMock()
        job_repo.get_processing_items.return_value = [{'id': 'job-1'}]
        company_repo = MagicMock()
        company_repo.get_processing_items.return_value = [{'id': 2}]
        with (
            patch('dependencies.get_session_sync', return_value=session),
            patch('jobs.infrastructure.SQLAlchemyJobRepository', return_value=job_repo),
            patch('companies.infrastructure.SQLAlchemyCompanyRepository', return_value=company_repo),
        ):
            api._recover_tasks()
        job_repo.update_fields.assert_called_once()
        company_repo.update_fields.assert_called_once()
        session.close.assert_called_once()

    def test_no_stuck_tasks(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.all.side_effect = [[], []]
        with patch('dependencies.get_session_sync', return_value=session):
            api._recover_tasks()
        assert session.query.return_value.filter.return_value.all.call_count == 2

    def test_exception_path(self):
        with patch('dependencies.get_session_sync', side_effect=RuntimeError('db down')):
            api._recover_tasks()


# ── create_app ────────────────────────────────────────────────────

class TestCreateApp:
    def test_returns_fastapi_with_health_route(self):
        app = api.create_app()
        assert app.title == 'Job Search Intelligence API'
        client = TestClient(app)
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}

    def test_spa_static_serving(self, tmp_path):
        (tmp_path / 'index.html').write_text('<html>INDEX</html>')
        assets = tmp_path / 'assets'
        assets.mkdir()
        (assets / 'app.js').write_text('console.log(1)')
        with patch('apps.backend.entrypoints.api.STATIC_FOLDER', str(tmp_path)):
            app = api.create_app()
        client = TestClient(app)
        assert client.get('/').status_code == 200
        assert 'INDEX' in client.get('/some/route').text
        asset = client.get('/assets/app.js')
        assert asset.status_code == 200
        assert 'console.log(1)' in asset.text

    def test_no_static_folder_no_fallback(self, tmp_path):
        with patch('apps.backend.entrypoints.api.STATIC_FOLDER', str(tmp_path / 'missing')):
            app = api.create_app()
        client = TestClient(app)
        assert client.get('/api/health').status_code == 200
        assert client.get('/nope').status_code == 404


# ── socketio-wrapped ASGI app ─────────────────────────────────────

class TestAsgiApp:
    @pytest.mark.asyncio
    async def test_health_via_asgi_app(self):
        transport = httpx.ASGITransport(app=api.fastapi_app)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            response = await client.get('/api/health')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}

    @pytest.mark.asyncio
    async def test_events_processing_stream(self):
        from fastapi import FastAPI, Request
        from fastapi.responses import StreamingResponse
        from shared.presentation.api import processing_events_router as router_mod

        async def fake_processing_events(request: Request):
            async def event_stream():
                yield 'data: ping\n\n'

            return StreamingResponse(
                event_stream(),
                media_type='text/event-stream',
                headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
            )

        original_endpoint = router_mod.router.routes[0].endpoint
        router_mod.router.routes[0].endpoint = fake_processing_events
        try:
            # Fresh app so the deferred router resolution picks up the patched
            # endpoint before any request caches the real SSE handler.
            app = FastAPI()
            app.include_router(router_mod.router, prefix='/events')

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url='http://test', timeout=5) as client:
                response = await client.get('/events/processing')
                assert response.status_code == 200
                assert 'text/event-stream' in response.headers['content-type']
                assert response.text == 'data: ping\n\n'
        finally:
            router_mod.router.routes[0].endpoint = original_endpoint
