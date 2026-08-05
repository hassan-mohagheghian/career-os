"""Tests for shared.infrastructure.stream_server."""

import asyncio
import json
import sys
import os
import types
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import websockets
from websockets import frames

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.infrastructure import stream_server
from rules.infrastructure.models.rule_model import RuleModel
from jobs.infrastructure.models.misc_models import SummaryModel, ResumeModel
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
from jobs.infrastructure.models.job_model import JobModel


def _insert_pending(session, url='https://ex.com/p', status='created', source='cli', workflow_log='[]'):
    job_id = str(uuid.uuid7())
    m = JobModel(id=job_id, url=url, status=status, source=source,
                 notes='[]', links='[]', workflow_log=workflow_log)
    session.add(m)
    session.commit()
    return job_id


def _job_dict(job_id, **overrides):
    d = {
        'id': job_id, 'company': 'Acme', 'role': 'Engineer', 'location': 'Berlin',
        'match': 'High', 'score': 'A', 'salary': '100k', 'stack': 'Python',
        'visa': 'Yes', 'applicants': '10', 'posted': '3 days ago',
        'industry': 'Tech', 'domain': 'web', 'notes': 'note', 'action': 'Apply Now',
        'url': f'https://ex.com/{job_id}',
    }
    d.update(overrides)
    return d


def _install_fake_dateutil():
    fake = types.ModuleType('dateutil')
    fake_rel = types.ModuleType('dateutil.relativedelta')
    fake_rel.relativedelta = lambda months=0, **kw: timedelta(days=months * 30)
    fake.relativedelta = fake_rel
    sys.modules['dateutil'] = fake
    sys.modules['dateutil.relativedelta'] = fake_rel


class _FakeLoop:
    """Replaces asyncio.get_event_loop so run_in_executor runs inline."""

    async def run_in_executor(self, executor, fn, *args):
        return fn(*args)

    def create_task(self, coro, *args, **kwargs):
        return asyncio.get_running_loop().create_task(coro)


class FakeWS:
    """Minimal async websocket stub."""

    def __init__(self, messages):
        self._messages = messages
        self._index = 0
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index < len(self._messages):
            msg = self._messages[self._index]
            self._index += 1
            if isinstance(msg, BaseException):
                raise msg
            return msg
        raise StopAsyncIteration

    async def send(self, msg):
        self.sent.append(msg)


@pytest.fixture
def clear_state():
    stream_server.clients.clear()
    stream_server.processes.clear()
    yield
    stream_server.clients.clear()
    stream_server.processes.clear()


# ── _parse_adv_at ─────────────────────────────────────────────────

class TestParseAdvAt:
    def test_active(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('Active')
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60

    def test_empty(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('')
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60

    def test_none(self):
        now = datetime.now()
        res = stream_server._parse_adv_at(None)
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60

    def test_na(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('N/A')
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60

    def test_not_specified(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('Not specified')
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60

    def test_hours(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('3 hours ago')
        assert abs((now - datetime.fromisoformat(res)).total_seconds() - 3 * 3600) < 120

    def test_days(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('2 days ago')
        assert abs((now - datetime.fromisoformat(res)).total_seconds() - 2 * 86400) < 120

    def test_weeks(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('1 week ago')
        assert abs((now - datetime.fromisoformat(res)).total_seconds() - 7 * 86400) < 120

    def test_months_with_plus(self):
        _install_fake_dateutil()
        now = datetime.now()
        res = stream_server._parse_adv_at('5+ months ago')
        assert abs((now - datetime.fromisoformat(res)).total_seconds() - 5.5 * 30 * 86400) < 120

    def test_non_numeric(self):
        now = datetime.now()
        res = stream_server._parse_adv_at('recently')
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60

    def test_month_calculation_error(self):
        fake = types.ModuleType('dateutil')
        fake_rel = types.ModuleType('dateutil.relativedelta')
        fake_rel.relativedelta = lambda months=0, **kw: (_ for _ in ()).throw(ValueError('boom'))
        fake.relativedelta = fake_rel
        sys.modules['dateutil'] = fake
        sys.modules['dateutil.relativedelta'] = fake_rel
        now = datetime.now()
        res = stream_server._parse_adv_at('5+ months ago')
        assert abs((datetime.fromisoformat(res) - now).total_seconds()) < 60


# ── _normalize_job_data ───────────────────────────────────────────

class TestNormalizeJobData:
    def test_city_with_parentheses(self):
        d = {'location': 'Berlin (Germany)', 'locations': []}
        stream_server._normalize_job_data(d)
        assert d['location'] == 'Berlin'
        assert d['locations'] == ['Berlin']

    def test_city_comma(self):
        d = {'location': 'Berlin, Munich', 'locations': []}
        stream_server._normalize_job_data(d)
        assert d['location'] == 'Berlin'
        assert set(d['locations']) == {'Berlin', 'Munich'}

    def test_city_slash(self):
        d = {'location': 'Berlin/Munich', 'locations': []}
        stream_server._normalize_job_data(d)
        assert set(d['locations']) == {'Berlin', 'Munich'}

    def test_city_pipe(self):
        d = {'location': 'Berlin|Munich', 'locations': []}
        stream_server._normalize_job_data(d)
        assert set(d['locations']) == {'Berlin', 'Munich'}

    def test_locations_string(self):
        d = {'location': '', 'locations': '["Berlin", "Paris"]'}
        stream_server._normalize_job_data(d)
        assert d['locations'] == ['Berlin', 'Paris']

    def test_locations_invalid_json(self):
        d = {'location': '', 'locations': 'not json'}
        stream_server._normalize_job_data(d)
        assert d['locations'] == ['']

    def test_umlaut(self):
        d = {'location': 'München', 'locations': []}
        stream_server._normalize_job_data(d)
        assert d['location'] == 'Munich'

    def test_locations_non_city_kept(self):
        d = {'location': '', 'locations': ['Zanzibar', '']}
        stream_server._normalize_job_data(d)
        assert d['locations'] == ['Zanzibar']

    def test_no_location(self):
        d = {}
        stream_server._normalize_job_data(d)
        assert d['locations'] == ['Not specified']


# ── fetch_url ─────────────────────────────────────────────────────

class TestFetchUrl:
    def test_ok(self):
        page = MagicMock()
        page.is_ok = True
        page.plain_text = 'cleaned text'
        with patch.object(stream_server, 'fetch_page', return_value=page):
            assert stream_server.fetch_url('https://ex.com') == 'cleaned text'

    def test_error_with_message(self):
        page = MagicMock()
        page.is_ok = False
        page.error.message = 'boom'
        with patch.object(stream_server, 'fetch_page', return_value=page):
            with pytest.raises(RuntimeError, match='boom'):
                stream_server.fetch_url('https://ex.com')

    def test_error_no_message(self):
        page = MagicMock()
        page.is_ok = False
        page.error = None
        with patch.object(stream_server, 'fetch_page', return_value=page):
            with pytest.raises(RuntimeError, match='Fetch failed'):
                stream_server.fetch_url('https://ex.com')


# ── broadcast ─────────────────────────────────────────────────────

class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_sends(self, clear_state):
        pid = 1
        ws = MagicMock()
        ws.send = AsyncMock()
        stream_server.clients[pid] = {ws}
        await stream_server.broadcast(pid, {'type': 'test'})
        ws.send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_connection_closed(self, clear_state):
        pid = 1
        ws = MagicMock()
        exc = websockets.ConnectionClosed(
            frames.Close(1000, 'bye'), frames.Close(1000, 'bye'), rcvd_then_sent=True
        )
        ws.send = AsyncMock(side_effect=exc)
        stream_server.clients[pid] = {ws}
        await stream_server.broadcast(pid, {'type': 'test'})
        assert ws not in stream_server.clients[pid]

    @pytest.mark.asyncio
    async def test_broadcast_keeps_healthy(self, clear_state):
        pid = 1
        good = MagicMock()
        good.send = AsyncMock()
        dead = MagicMock()
        exc = websockets.ConnectionClosed(
            frames.Close(1000, 'bye'), frames.Close(1000, 'bye'), rcvd_then_sent=True
        )
        dead.send = AsyncMock(side_effect=exc)
        stream_server.clients[pid] = {good, dead}
        await stream_server.broadcast(pid, {'type': 'test'})
        assert good in stream_server.clients[pid]
        assert dead not in stream_server.clients[pid]

    @pytest.mark.asyncio
    async def test_broadcast_no_clients(self, clear_state):
        await stream_server.broadcast(999, {'type': 'test'})


# ── DB helper functions ───────────────────────────────────────────

class TestLogHelpers:
    def test_log_appends(self, mock_get_session):
        pid = _insert_pending(mock_get_session)
        stream_server._log(pid, 'step1', 'hello')
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        logs = json.loads(row.workflow_log or '[]')
        assert len(logs) == 1
        assert logs[0]['step'] == 'step1'
        assert logs[0]['msg'] == 'hello'

    def test_log_missing_pid(self, mock_get_session):
        stream_server._log('99999', 'step', 'msg')

    def test_log_appends_existing_log(self, mock_get_session):
        pid = _insert_pending(mock_get_session, workflow_log='[{"step": "old", "msg": "prev"}]')
        stream_server._log(pid, 'new', 'hello')
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        logs = json.loads(row.workflow_log or '[]')
        assert len(logs) == 2
        assert logs[0]['step'] == 'old'
        assert logs[1]['step'] == 'new'


class TestUpdateStep:
    def test_update_step_all_fields(self, mock_get_session):
        pid = _insert_pending(mock_get_session)
        stream_server._update_step(pid, 'step_fetch', 0, status='processing', company='Acme', job_id='job-1', error='none')
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'processing'
        assert row.company == 'Acme'
        assert row.error == 'none'
        assert row.updated_at is not None

    def test_update_step_minimal(self, mock_get_session):
        pid = _insert_pending(mock_get_session)
        stream_server._update_step(pid, 'step_fetch', 0)
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.updated_at is not None

    def test_mark(self, mock_get_session):
        pid = _insert_pending(mock_get_session)
        stream_server._mark(pid, 'step_fetch', company='Acme', job_id='job-1')
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.company == 'Acme'

    def test_fail_with_step(self, mock_get_session):
        pid = _insert_pending(mock_get_session)
        stream_server._fail(pid, 'boom', step='fetch')
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'failed'
        assert row.error == '[fetch] boom'

    def test_fail_without_step(self, mock_get_session):
        pid = _insert_pending(mock_get_session)
        stream_server._fail(pid, 'boom')
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'failed'
        assert row.error == 'boom'


class TestLoadRules:
    def test_load_rules_job(self, mock_get_session):
        session = mock_get_session
        session.add(RuleModel(category='fit', scope='JOB', key='python_backend_core',
                              value='Python required', priority=100, enabled=1))
        session.add(RuleModel(category='success', scope='SHARED', key='visa',
                              value='Visa ok', priority=90, enabled=1))
        session.commit()
        text = stream_server._load_rules('job')
        assert 'FIT' in text
        assert 'python_backend_core' in text
        assert 'visa' in text

    def test_load_rules_company(self, mock_get_session):
        session = mock_get_session
        session.add(RuleModel(category='fit', scope='COMPANY_PRODUCT', key='company_quality',
                              value='x', priority=100, enabled=1))
        session.commit()
        text = stream_server._load_rules('company')
        assert 'company_quality' in text

    def test_load_rules_none(self, mock_get_session):
        assert stream_server._load_rules('job') == 'No scoring rules set.'


class TestJobIds:
    def test_get_existing_id(self, mock_get_session):
        session = mock_get_session
        job_id = str(uuid.uuid7())
        session.add(JobModel(id=job_id, url='https://ex.com/3'))
        session.commit()
        assert stream_server._get_existing_id('https://ex.com/3') == job_id

    def test_get_existing_id_none(self, mock_get_session):
        assert stream_server._get_existing_id('https://missing.com') is None


class TestInsertJob:
    @pytest.mark.parametrize('input_et, expected', [
        ('full time', 'Full-time'),
        ('Full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('freelance', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
        ('random', 'Full-time'),
    ])
    def test_employment_types(self, mock_get_session, input_et, expected):
        stream_server._insert_job(_job_dict('8000', employment_type=input_et))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8000').first()
        assert row is not None
        assert json.loads(row.employment_types) == [expected]

    def test_work_types_string(self, mock_get_session):
        stream_server._insert_job(_job_dict('8101', work_types='["Remote", "Hybrid"]'))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8101').first()
        assert json.loads(row.work_types) == ['Remote', 'Hybrid']

    def test_work_types_invalid_json(self, mock_get_session):
        stream_server._insert_job(_job_dict('8102', work_types='not-json'))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8102').first()
        assert json.loads(row.work_types) == ['On-site']

    def test_work_type_fallback(self, mock_get_session):
        stream_server._insert_job(_job_dict('8103', work_types=[], work_type='Hybrid'))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8103').first()
        assert json.loads(row.work_types) == ['Hybrid']

    def test_empty_locations_string(self, mock_get_session):
        stream_server._insert_job(_job_dict('8201', locations=''))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8201').first()
        assert json.loads(row.locations) == ['Berlin']

    def test_adv_at_explicit(self, mock_get_session):
        stream_server._insert_job(_job_dict('8202', adv_at='2024-01-01T00:00:00'))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8202').first()
        assert row.adv_at == '2024-01-01T00:00:00'

    def test_adv_at_from_posted(self, mock_get_session):
        stream_server._insert_job(_job_dict('8203', posted='2 days ago'))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8203').first()
        now = datetime.now()
        parsed = datetime.fromisoformat(row.adv_at)
        assert abs((now - parsed).total_seconds() - 2 * 86400) < 120

    def test_see_at_default(self, mock_get_session):
        stream_server._insert_job(_job_dict('8204'))
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8204').first()
        assert row.see_at is not None

    def test_locations_string_branch(self, mock_get_session):
        d = _job_dict('8301')
        d['locations'] = 'London'
        with patch.object(stream_server, '_normalize_job_data', return_value=d):
            stream_server._insert_job(d)
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8301').first()
        assert json.loads(row.locations) == ['London']

    def test_work_types_fallback_onsite(self, mock_get_session):
        d = _job_dict('8302', work_types=[], work_type='')
        with patch.object(stream_server, '_normalize_job_data', return_value=d):
            stream_server._insert_job(d)
        row = mock_get_session.query(JobModel).filter(JobModel.id == '8302').first()
        assert json.loads(row.work_types) == ['On-site']


class TestInsertSummaryResume:
    def test_insert_summary(self, mock_get_session):
        stream_server._insert_summary({
            'job_id': '9001', 'company': 'Acme', 'match': 'High', 'score': 'A',
            'summary': 's', 'stack': 'py', 'resumeFit': 'fit', 'note': 'n',
            'url': 'https://ex.com/9001',
        })
        row = mock_get_session.query(SummaryModel).filter(SummaryModel.job_id == '9001').first()
        assert row is not None
        assert row.company == 'Acme'

    def test_insert_resume(self, mock_get_session):
        stream_server._insert_resume({
            'id': 'test_resume_1', 'title': 'T', 'company': 'Acme', 'role': 'Eng',
            'content': 'c', 'version': 1, 'raw_text': 'r', 'created_at': '2024-01-01',
            'job_id': '9001',
        })
        row = mock_get_session.query(ResumeModel).filter(ResumeModel.id == 'test_resume_1').first()
        assert row is not None
        assert row.company == 'Acme'


class TestSaveWorkflowLog:
    def test_save_job_workflow_log(self, mock_get_session):
        session = mock_get_session
        job_id = str(uuid.uuid7())
        session.add(JobModel(id=job_id, url='https://ex.com/9501'))
        session.commit()
        stream_server._save_job_workflow_log(job_id, '["a"]')
        row = session.query(JobModel).filter(JobModel.id == job_id).first()
        assert row.workflow_log == '["a"]'

    def test_mark_old_job_deleted(self, mock_get_session):
        session = mock_get_session
        id1 = str(uuid.uuid7())
        id2 = str(uuid.uuid7())
        session.add(JobModel(id=id1, url='https://ex.com/dup'))
        session.add(JobModel(id=id2, url='https://ex.com/dup'))
        session.commit()
        stream_server._mark_old_job_deleted('https://ex.com/dup', exclude_id=id1)
        assert session.query(JobModel).filter(JobModel.id == id2).first().deleted == 1
        assert session.query(JobModel).filter(JobModel.id == id1).first().deleted == 0


# ── stream_provider ───────────────────────────────────────────────

class TestStreamProvider:
    def _make_llm(self, events, content, returncode=0, on_session=False):
        class FakeLLM:
            def __init__(self):
                self.seen_session = None

            def generate_streaming(self, prompt, context=None, timeout=0, on_event=None, on_session_id=None):
                for evt in events:
                    on_event(evt)
                if on_session and on_session_id:
                    self.seen_session = 'sess-123'
                    on_session_id('sess-123')
                resp = MagicMock()
                resp.metadata = {'returncode': returncode}
                resp.content = content
                return resp

        return FakeLLM()

    @pytest.mark.asyncio
    async def test_valid_json_content(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        events = [
            {'type': 'text', 'part': {'text': 'hello world'}},
            {'type': 'tool_use', 'part': {'tool': 'bash', 'state': {
                'status': 'ok', 'input': {'command': 'ls'}, 'output': 'files', 'title': 'Run'}}},
            {'type': 'tool_use', 'part': {'tool': 'bash', 'state': {
                'status': 'ok', 'input': {'command': 'ls'}, 'metadata': {'output': 'meta'}, 'title': 'Run'}}},
            {'type': 'step_finish', 'part': {'reason': 'done', 'tokens': {'total': 5}}},
        ]
        llm = self._make_llm(events, '{"result": "ok"}', on_session=True)
        with patch.object(stream_server, 'get_llm_service', return_value=llm), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            rc, result = await stream_server.stream_provider(pid, 'prompt')
        await asyncio.sleep(0.05)
        assert rc == 0
        assert result == {'result': 'ok'}
        assert llm.seen_session == 'sess-123'
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert 'hello world' in (row.workflow_log or '')

    @pytest.mark.asyncio
    async def test_invalid_json_content(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        llm = self._make_llm([{'type': 'text', 'part': {'text': 'hi'}}], 'hello world', returncode=3)
        with patch.object(stream_server, 'get_llm_service', return_value=llm), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            rc, result = await stream_server.stream_provider(pid, 'prompt')
        await asyncio.sleep(0.05)
        assert rc == 3
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_content(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        llm = self._make_llm([], '')
        with patch.object(stream_server, 'get_llm_service', return_value=llm), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            rc, result = await stream_server.stream_provider(pid, 'prompt')
        await asyncio.sleep(0.05)
        assert rc == 0
        assert result is None

    @pytest.mark.asyncio
    async def test_no_events(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        llm = self._make_llm([], '{"x": 1}')
        with patch.object(stream_server, 'get_llm_service', return_value=llm), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            rc, result = await stream_server.stream_provider(pid, 'prompt')
        await asyncio.sleep(0.05)
        assert rc == 0
        assert result == {'x': 1}

    @pytest.mark.asyncio
    async def test_content_non_string(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        llm = self._make_llm([], 12345)
        with patch.object(stream_server, 'get_llm_service', return_value=llm), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            rc, result = await stream_server.stream_provider(pid, 'prompt')
        await asyncio.sleep(0.05)
        assert rc == 0
        assert result is None


# ── process_job_stream ────────────────────────────────────────────

class TestProcessJobStream:
    def _item(self, source='cli', url='https://ex.com/job'):
        return {
            'url': url,
            'notes': '[]',
            'links': '[]',
            'source': source,
            'workflow_log': '[]',
            'status': 'created',
        }

    def _result(self, **overrides):
        d = {
            'errors': [],
            'metadata': {
                'extract_raw': {'success': True},
                'fetch': {'length': 120},
                'extraction': {'company': 'Acme', 'title': 'Engineer'},
                'persistence': {'success': True, 'job_id': 'job-42', 'company': 'Acme'},
                'score': 'A',
            },
        }
        d.update(overrides)
        return d

    def _patch_graph(self, result):
        builder = MagicMock()
        graph = MagicMock()
        graph.invoke.return_value = result
        builder.compile.return_value = graph
        return patch('ai.infrastructure.graphs.job.graph.build_job_processing_graph', return_value=builder), \
            patch('ai.infrastructure.graphs.runtime.state.create_initial_state', return_value={'input': 'x'})

    @pytest.mark.asyncio
    async def test_success(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        graph_patch, state_patch = self._patch_graph(self._result())
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item()), \
                graph_patch, state_patch, \
                patch('jobs.infrastructure.workers.worker._save_job_workflow_log') as mock_save, \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        mock_save.assert_called_once()
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'done'

    @pytest.mark.asyncio
    async def test_success_with_errors(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        result = self._result(errors=['e1', 'e2', 'e3', 'e4'])
        graph_patch, state_patch = self._patch_graph(result)
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item()), \
                graph_patch, state_patch, \
                patch('jobs.infrastructure.workers.worker._save_job_workflow_log'), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'done'

    @pytest.mark.asyncio
    async def test_success_rescore(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        graph_patch, state_patch = self._patch_graph(self._result())
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item(source='rescore', url='https://ex.com/oldjob')), \
                graph_patch, state_patch, \
                patch('jobs.infrastructure.workers.worker._save_job_workflow_log'), \
                patch('jobs.infrastructure.workers.worker._mark_old_job_deleted') as mock_mark, \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        mock_mark.assert_called_once_with('https://ex.com/oldjob', exclude_id='job-42')

    @pytest.mark.asyncio
    async def test_success_requeue(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        graph_patch, state_patch = self._patch_graph(self._result())
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item(source='requeue')), \
                graph_patch, state_patch, \
                patch('jobs.infrastructure.workers.worker._save_job_workflow_log'), \
                patch('jobs.infrastructure.workers.worker._mark_old_job_deleted') as mock_mark, \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        mock_mark.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_with_rules(self, mock_get_session, clear_state):
        mock_get_session.add(RuleModel(category='fit', scope='JOB', key='python_backend_core',
                                       value='Python required', priority=100, enabled=1))
        mock_get_session.commit()
        pid = _insert_pending(mock_get_session)
        graph_patch, state_patch = self._patch_graph(self._result())
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item()), \
                graph_patch, state_patch, \
                patch('jobs.infrastructure.workers.worker._save_job_workflow_log'), \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'done'

    @pytest.mark.asyncio
    async def test_persistence_failure(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        result = self._result(metadata={'extraction': {}, 'persistence': {'success': False, 'error': 'boom'}})
        graph_patch, state_patch = self._patch_graph(result)
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item()), \
                graph_patch, state_patch, \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'failed'
        assert 'Persistence failed: boom' in (row.error or '')

    @pytest.mark.asyncio
    async def test_persistence_failure_unknown_error(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        result = self._result(metadata={'extraction': {}, 'persistence': {'success': False}})
        graph_patch, state_patch = self._patch_graph(result)
        with patch.object(SQLAlchemyJobRepository, 'get_by_id', return_value=self._item()), \
                graph_patch, state_patch, \
                patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            await stream_server.process_job_stream(pid)
        await asyncio.sleep(0.05)
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'failed'
        assert 'Unknown error' in (row.error or '')

    @pytest.mark.asyncio
    async def test_item_not_found(self, mock_get_session, clear_state):
        with patch.object(stream_server.asyncio, 'get_event_loop', return_value=_FakeLoop()):
            result = await stream_server.process_job_stream('99999')
        assert result is None


# ── handler ───────────────────────────────────────────────────────

class TestHandler:
    @pytest.mark.asyncio
    async def test_watch_sends_state(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session, status='processing', workflow_log='[{"step":"a","msg":"b"}]')
        ws = FakeWS([json.dumps({'action': 'watch', 'pid': pid})])
        await stream_server.handler(ws)
        assert pid in stream_server.clients
        assert ws not in stream_server.clients[pid]
        state_msgs = [m for m in ws.sent if '"type": "state"' in m]
        assert len(state_msgs) == 1
        assert '"status": "processing"' in state_msgs[0]

    @pytest.mark.asyncio
    async def test_watch_no_row(self, mock_get_session, clear_state):
        ws = FakeWS([json.dumps({'action': 'watch', 'pid': '987654'})])
        await stream_server.handler(ws)
        assert '987654' in stream_server.clients
        assert ws.sent == []

    @pytest.mark.asyncio
    async def test_process_creates_task(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        ws = FakeWS([json.dumps({'action': 'process', 'pid': pid})])
        with patch.object(stream_server, 'process_job_stream', new=AsyncMock()) as mock_proc:
            await stream_server.handler(ws)
        await asyncio.sleep(0)
        mock_proc.assert_awaited_once_with(pid)

    @pytest.mark.asyncio
    async def test_stop_terminates(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        proc = MagicMock()
        stream_server.processes[pid] = proc
        ws = FakeWS([json.dumps({'action': 'stop', 'pid': pid})])
        await stream_server.handler(ws)
        proc.terminate.assert_called_once()
        row = mock_get_session.query(JobModel).filter(JobModel.id == pid).first()
        assert row.status == 'failed'
        assert 'Terminated by user' in (row.error or '')

    @pytest.mark.asyncio
    async def test_stop_no_proc(self, mock_get_session, clear_state):
        pid = _insert_pending(mock_get_session)
        ws = FakeWS([json.dumps({'action': 'stop', 'pid': pid})])
        await stream_server.handler(ws)

    @pytest.mark.asyncio
    async def test_connection_closed_removes_ws(self, mock_get_session, clear_state):
        pid = '555'
        exc = websockets.ConnectionClosed(
            frames.Close(1000, 'bye'), frames.Close(1000, 'bye'), rcvd_then_sent=True
        )
        ws = FakeWS([json.dumps({'action': 'watch', 'pid': pid}), exc])
        await stream_server.handler(ws)
        assert pid in stream_server.clients
        assert ws not in stream_server.clients[pid]

    @pytest.mark.asyncio
    async def test_invalid_json_message(self, mock_get_session, clear_state):
        ws = FakeWS(['not json at all'])
        with pytest.raises(json.JSONDecodeError):
            await stream_server.handler(ws)


# ── main ──────────────────────────────────────────────────────────

class TestMain:
    @pytest.mark.asyncio
    async def test_main(self, clear_state):
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def fake_serve(handler, host, port):
            yield

        with patch.object(stream_server.websockets, 'serve', fake_serve), \
                patch.object(stream_server.asyncio, 'Future', side_effect=asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await stream_server.main()
