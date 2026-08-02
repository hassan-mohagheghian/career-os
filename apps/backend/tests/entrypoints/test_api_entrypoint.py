"""Tests for the FastAPI/socketio entrypoint (apps/backend/entrypoints/api.py).

Importing this module runs create_app() at import time, which wires the
socketio broadcasters and builds the ASGI app — exactly what the module
does in production.
"""

import os
import sys
import subprocess as _subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from apps.backend.entrypoints import api


@pytest.fixture
def mock_sio():
    with patch('apps.backend.entrypoints.api.sio', AsyncMock()) as sio:
        yield sio


# ── SocketIO event handlers ───────────────────────────────────────

class TestSocketioHandlers:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        await api.connect('sid', {'HTTP_USER_AGENT': 'x'})
        await api.disconnect('sid')

    @pytest.mark.asyncio
    async def test_watch_job(self, mock_sio):
        await api.watch_job('sid', {'id': 5})
        mock_sio.enter_room.assert_awaited_once_with('sid', 'job_5')

    @pytest.mark.asyncio
    async def test_watch_job_no_id(self, mock_sio):
        await api.watch_job('sid', {})
        mock_sio.enter_room.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unwatch_job(self, mock_sio):
        await api.unwatch_job('sid', {'id': 5})
        mock_sio.leave_room.assert_awaited_once_with('sid', 'job_5')

    @pytest.mark.asyncio
    async def test_watch_company(self, mock_sio):
        await api.watch_company('sid', {'id': 5})
        mock_sio.enter_room.assert_awaited_once_with('sid', 'company_5')

    @pytest.mark.asyncio
    async def test_unwatch_company(self, mock_sio):
        await api.unwatch_company('sid', {'id': 5})
        mock_sio.leave_room.assert_awaited_once_with('sid', 'company_5')

    @pytest.mark.asyncio
    async def test_watch_generation(self, mock_sio):
        await api.watch_generation('sid', {'id': 9})
        mock_sio.enter_room.assert_awaited_once_with('sid', 'generation_9')

    @pytest.mark.asyncio
    async def test_unwatch_generation(self, mock_sio):
        await api.unwatch_generation('sid', {'id': 9})
        mock_sio.leave_room.assert_awaited_once_with('sid', 'generation_9')

    @pytest.mark.asyncio
    async def test_watch_skills(self, mock_sio):
        await api.watch_skills('sid')
        mock_sio.enter_room.assert_awaited_once_with('sid', 'skills')

    @pytest.mark.asyncio
    async def test_unwatch_skills(self, mock_sio):
        await api.unwatch_skills('sid')
        mock_sio.leave_room.assert_awaited_once_with('sid', 'skills')

    @pytest.mark.asyncio
    async def test_watch_generation_no_id(self, mock_sio):
        await api.watch_generation('sid', {})
        mock_sio.enter_room.assert_not_awaited()


class TestCancelJob:
    @pytest.mark.asyncio
    async def test_no_id_noop(self):
        await api.cancel_job('sid', {})

    @pytest.mark.asyncio
    async def test_cancel_job_entity(self, mock_get_session):
        from jobs.infrastructure.models.job_model import JobModel
        job = JobModel(num=2001, url='https://ex.com/1', status='processing')
        mock_get_session.add(job)
        mock_get_session.commit()
        await api.cancel_job('sid', {'id': 2001, 'entity_type': 'job'})
        row = mock_get_session.query(JobModel).filter(JobModel.num == 2001).first()
        assert row.status == 'cancelled'

    @pytest.mark.asyncio
    async def test_cancel_company_entity(self, mock_get_session):
        from companies.infrastructure.models.company_model import CompanyModel
        co = CompanyModel(name='ACME', status='processing')
        mock_get_session.add(co)
        mock_get_session.commit()
        co_id = co.id
        await api.cancel_job('sid', {'id': co_id, 'entity_type': 'company'})
        row = mock_get_session.query(CompanyModel).filter(CompanyModel.id == co_id).first()
        assert row.status == 'cancelled'


class TestResetJob:
    @pytest.mark.asyncio
    async def test_reset_job_entity(self, mock_get_session):
        from jobs.infrastructure.models.job_model import JobModel
        job = JobModel(num=2002, url='https://ex.com/2', status='failed', error='x')
        mock_get_session.add(job)
        mock_get_session.commit()
        await api.reset_job('sid', {'id': 2002, 'entity_type': 'job'})
        row = mock_get_session.query(JobModel).filter(JobModel.num == 2002).first()
        assert row.status == 'created'
        assert row.error is None

    @pytest.mark.asyncio
    async def test_reset_company_entity(self, mock_get_session):
        from companies.infrastructure.models.company_model import CompanyModel
        co = CompanyModel(name='ACME', status='failed', error='x')
        mock_get_session.add(co)
        mock_get_session.commit()
        co_id = co.id
        await api.reset_job('sid', {'id': co_id, 'entity_type': 'company'})
        row = mock_get_session.query(CompanyModel).filter(CompanyModel.id == co_id).first()
        assert row.status == 'created'
        assert row.error is None


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
        job_repo.get_processing_items.return_value = [{'num': 1}]
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
        transport = httpx.ASGITransport(app=api.app)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            response = await client.get('/api/health')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok'}

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_events_processing_stream(self):
        from shared.presentation.api import processing_events_router as router_mod
        from fastapi import Request
        from fastapi.responses import StreamingResponse

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
            transport = httpx.ASGITransport(app=api.app)
            async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
                response = await client.get('/events/processing')
        finally:
            router_mod.router.routes[0].endpoint = original_endpoint

        assert response.status_code == 200
        assert 'text/event-stream' in response.headers['content-type']
        assert response.text == 'data: ping\n\n'
