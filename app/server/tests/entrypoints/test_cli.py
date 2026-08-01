"""Tests for the Job Search CLI entrypoint (app/server/entrypoints/cli.py)."""

import json
import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from app.server.entrypoints import cli
from jobs.infrastructure.models.job_model import JobModel

runner = CliRunner()


def pending_row(pid=1, status='queued', source='cli', company='ACME', url='https://ex.com/job/1',
                error=None, created_at='2024-01-01', **kw):
    row = {
        'id': pid, 'status': status, 'source': source, 'company': company,
        'step_fetch': 0, 'step_analyze': 0, 'step_db': 0, 'step_done': 0,
        'url': url, 'error': error, 'created_at': created_at,
    }
    row.update(kw)
    return row


def job_row(num=1, **kw):
    row = {
        'num': num, 'company': 'ACME', 'role': 'Engineer', 'url': f'https://ex.com/job/{num}',
        'created_at': '2024-01-01', 'deleted': 0,
        'raw_description': 'raw', 'structured_description': '{"fit_score": 5}',
    }
    row.update(kw)
    return row


# ── Helper functions ──────────────────────────────────────────────

class TestNormalizeUrl:
    def test_empty_returns_as_is(self):
        assert cli.normalize_url(None) is None
        assert cli.normalize_url('') == ''

    def test_strips_query_and_trailing_slash(self):
        assert cli.normalize_url('https://ex.com/jobs/123?utm=x&ref=y/') == 'https://ex.com/jobs/123'

    def test_no_query_or_slash(self):
        assert cli.normalize_url('https://ex.com/jobs/123') == 'https://ex.com/jobs/123'


class TestGetNextNum:
    def test_returns_repo_value(self):
        repo = MagicMock()
        repo.get_next_num.return_value = 7
        sess = MagicMock()
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)):
            assert cli.get_next_num() == 7
        sess.close.assert_called_once()


class TestGetPending:
    def _patch(self, rows):
        sess = MagicMock()
        repo = MagicMock()
        repo.list_pending.return_value = rows
        patch_target = patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess, repo))
        return patch_target, sess

    def test_filters_done_and_sorts(self):
        rows = [
            pending_row(pid=2, status='processing', created_at='2024-01-02'),
            pending_row(pid=1, status='done', created_at='2024-01-01'),
            pending_row(pid=3, status='queued', created_at='2024-01-03'),
        ]
        p, sess = self._patch(rows)
        with p:
            result = cli.get_pending()
        assert [r['id'] for r in result] == [2, 3]

    def test_status_filter(self):
        rows = [
            pending_row(pid=1, status='failed', created_at='2024-01-01'),
            pending_row(pid=2, status='queued', created_at='2024-01-02'),
        ]
        p, sess = self._patch(rows)
        with p:
            result = cli.get_pending(status='queued')
        assert [r['id'] for r in result] == [2]

    def test_empty(self):
        p, sess = self._patch([])
        with p:
            assert cli.get_pending() == []


class TestAddPending:
    def test_existing_url_returns_none(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.get_by_url.return_value = {'id': 1}
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess, repo)):
            assert cli.add_pending('https://ex.com/x') is None

    def test_create_returns_id(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.get_by_url.return_value = None
        repo.create.return_value = {'id': 42}
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess, repo)):
            assert cli.add_pending('https://ex.com/x', source='cli', company='ACME') == 42
        repo.create.assert_called_once()

    def test_create_raises_returns_none(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.get_by_url.return_value = None
        repo.create.side_effect = RuntimeError('boom')
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess, repo)):
            assert cli.add_pending('https://ex.com/x') is None


class TestResetPending:
    def test_calls_update_fields(self):
        sess = MagicMock()
        repo = MagicMock()
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess, repo)):
            cli.reset_pending(9)
        repo.update_fields.assert_called_once()
        assert repo.update_fields.call_args[0][0] == 9
        sess.close.assert_called_once()


class TestDeletePending:
    def test_marks_deleted_in_db(self, mock_get_session):
        job = JobModel(num=1001, url='https://ex.com/job/1', status='queued', deleted=0)
        mock_get_session.add(job)
        mock_get_session.commit()
        cli.delete_pending(1001)
        row = mock_get_session.query(JobModel).filter(JobModel.num == 1001).first()
        assert row.deleted == 1


class TestProcessPendingSync:
    def test_imports_worker_and_calls_process_job(self):
        fake_worker = types.ModuleType('jobs.infrastructure.workers.worker')
        fake_worker.process_job = MagicMock()
        with patch.dict(sys.modules, {'jobs.infrastructure.workers.worker': fake_worker}):
            cli.process_pending_sync(42)
        fake_worker.process_job.assert_called_once_with(42)


class TestEnqueuePending:
    def test_calls_enqueue_job_sync(self):
        fake_client = types.ModuleType('shared.infrastructure.taskiq.client')
        fake_client.enqueue_job_sync = MagicMock()
        with patch.dict(sys.modules, {'shared.infrastructure.taskiq.client': fake_client}):
            cli.enqueue_pending(42)
        fake_client.enqueue_job_sync.assert_called_once_with(42)


# ── add ───────────────────────────────────────────────────────────

class TestAddCommand:
    def _mocks(self, pending=(), active=()):
        sess_p, sess_j = MagicMock(), MagicMock()
        pending_repo = MagicMock()
        pending_repo.list_pending.return_value = list(pending)
        job_repo = MagicMock()
        job_repo.get_all_active.return_value = list(active)
        return sess_p, sess_j, pending_repo, job_repo

    def test_duplicate_in_pending(self):
        sess_p, sess_j, p, j = self._mocks(
            pending=[pending_row(pid=5, url='https://ex.com/job/1', status='queued')]
        )
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, p)), \
             patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, j)):
            result = runner.invoke(cli.app, ['add', 'https://ex.com/job/1?x=1'])
        assert result.exit_code == 0
        assert 'Already in queue (ID:5' in result.output

    def test_duplicate_in_jobs(self):
        sess_p, sess_j, p, j = self._mocks(
            active=[{'num': 3, 'url': 'https://ex.com/job/1', 'company': 'ACME'}]
        )
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, p)), \
             patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, j)):
            result = runner.invoke(cli.app, ['add', 'https://ex.com/job/1/'])
        assert result.exit_code == 0
        assert 'Already processed as #3 (ACME)' in result.output

    def test_add_failure(self):
        sess_p, sess_j, p, j = self._mocks()
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, p)), \
             patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, j)), \
             patch('app.server.entrypoints.cli.add_pending', return_value=None):
            result = runner.invoke(cli.app, ['add', 'https://ex.com/job/1'])
        assert result.exit_code == 0
        assert 'Failed to add job' in result.output

    def test_add_success_and_process(self):
        sess_p, sess_j, p, j = self._mocks()
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, p)), \
             patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, j)), \
             patch('app.server.entrypoints.cli.add_pending', return_value=42) as add_mock, \
             patch('app.server.entrypoints.cli.process_pending_sync') as proc_mock:
            result = runner.invoke(cli.app, ['add', 'https://ex.com/job/1'])
        assert result.exit_code == 0
        assert 'Added (ID:42)' in result.output
        assert 'Done!' in result.output
        add_mock.assert_called_once_with('https://ex.com/job/1', source='cli')
        proc_mock.assert_called_once_with(42)

    def test_add_process_failure(self):
        sess_p, sess_j, p, j = self._mocks()
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, p)), \
             patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, j)), \
             patch('app.server.entrypoints.cli.add_pending', return_value=42), \
             patch('app.server.entrypoints.cli.process_pending_sync',
                   side_effect=RuntimeError('boom')):
            result = runner.invoke(cli.app, ['add', 'https://ex.com/job/1'])
        assert result.exit_code == 0
        assert 'Failed: boom' in result.output

    def test_add_no_process_skips_processing(self):
        sess_p, sess_j, p, j = self._mocks()
        with patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, p)), \
             patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, j)), \
             patch('app.server.entrypoints.cli.add_pending', return_value=42), \
             patch('app.server.entrypoints.cli.process_pending_sync') as proc_mock:
            result = runner.invoke(cli.app, ['add', 'https://ex.com/job/1', '--no-process'])
        assert result.exit_code == 0
        assert 'Added (ID:42)' in result.output
        proc_mock.assert_not_called()


# ── list ──────────────────────────────────────────────────────────

class TestListCommand:
    def test_no_rows(self):
        with patch('app.server.entrypoints.cli.get_pending', return_value=[]):
            result = runner.invoke(cli.app, ['list'])
        assert result.exit_code == 0
        assert 'No jobs found' in result.output

    def test_rows_table(self):
        rows = [
            pending_row(pid=1, status='queued', url='https://ex.com/job/1'),
            pending_row(pid=2, status='failed', error='something went wrong'),
        ]
        with patch('app.server.entrypoints.cli.get_pending', return_value=rows):
            result = runner.invoke(cli.app, ['list'])
        assert result.exit_code == 0
        assert 'Pending Jobs (2)' in result.output
        assert 'queued' in result.output
        assert 'failed' in result.output
        assert 'ACME' in result.output

    def test_status_filter_passes_through(self):
        with patch('app.server.entrypoints.cli.get_pending', return_value=[pending_row()]) as m:
            result = runner.invoke(cli.app, ['list', '--status', 'queued'])
        assert result.exit_code == 0
        m.assert_called_once_with(status='queued')

    def test_all_includes_done_from_db(self, mock_get_session):
        job = JobModel(num=2001, url='https://ex.com/done/1', company='DoneCo', role='SDE',
                       status='completed', deleted=0)
        mock_get_session.add(job)
        mock_get_session.commit()
        with patch('app.server.entrypoints.cli.get_pending', return_value=[]):
            result = runner.invoke(cli.app, ['list', '--all'])
        assert result.exit_code == 0
        assert 'DoneCo' in result.output


# ── process ───────────────────────────────────────────────────────

class TestProcessCommand:
    def test_success(self):
        with patch('app.server.entrypoints.cli.process_pending_sync'):
            result = runner.invoke(cli.app, ['process', '5'])
        assert result.exit_code == 0
        assert 'Processing ID:5...' in result.output
        assert 'Done!' in result.output

    def test_failure(self):
        with patch('app.server.entrypoints.cli.process_pending_sync',
                   side_effect=RuntimeError('boom')):
            result = runner.invoke(cli.app, ['process', '5'])
        assert result.exit_code == 0
        assert 'Failed: boom' in result.output

    def test_reset_flag(self):
        with patch('app.server.entrypoints.cli.reset_pending') as reset_mock, \
             patch('app.server.entrypoints.cli.process_pending_sync'):
            result = runner.invoke(cli.app, ['process', '5', '--reset'])
        assert result.exit_code == 0
        assert 'Reset ID:5 to queued' in result.output
        reset_mock.assert_called_once_with(5)


# ── process_all ───────────────────────────────────────────────────

class TestProcessAllCommand:
    def test_no_queued(self):
        with patch('app.server.entrypoints.cli.get_pending', return_value=[]):
            result = runner.invoke(cli.app, ['process-all'])
        assert result.exit_code == 0
        assert 'No queued jobs' in result.output

    def test_processes_rows(self):
        rows = [pending_row(pid=1), pending_row(pid=2, url='https://ex.com/job/2')]
        with patch('app.server.entrypoints.cli.get_pending', return_value=rows), \
             patch('app.server.entrypoints.cli.process_pending_sync',
                   side_effect=[None, RuntimeError('x')]):
            result = runner.invoke(cli.app, ['process-all'])
        assert result.exit_code == 0
        assert 'Processing 2 jobs...' in result.output
        assert '[1] Done' in result.output
        assert '[2] Failed: x' in result.output


# ── reset / remove ────────────────────────────────────────────────

class TestResetRemoveCommands:
    def test_reset(self):
        with patch('app.server.entrypoints.cli.reset_pending') as reset_mock:
            result = runner.invoke(cli.app, ['reset', '5'])
        assert result.exit_code == 0
        assert 'Reset ID:5 to queued' in result.output
        reset_mock.assert_called_once_with(5)

    def test_remove(self):
        with patch('app.server.entrypoints.cli.delete_pending') as del_mock:
            result = runner.invoke(cli.app, ['remove', '5'])
        assert result.exit_code == 0
        assert 'Removed ID:5' in result.output
        del_mock.assert_called_once_with(5)


# ── rescore ───────────────────────────────────────────────────────

class TestRescoreCommand:
    def test_job_not_found(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.get_by_num.return_value = None
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['rescore', '5'])
        assert result.exit_code == 0
        assert 'Job #5 not found' in result.output

    def test_existing_pending_update_then_process(self):
        sess_j, sess_p = MagicMock(), MagicMock()
        job_repo = MagicMock()
        job_repo.get_by_num.return_value = {'num': 5, 'company': 'ACME', 'url': 'https://ex.com/job/5'}
        pend = MagicMock()
        pend.get_by_url.return_value = {'id': 7}
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, job_repo)), \
             patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, pend)), \
             patch('app.server.entrypoints.cli.process_pending_sync') as proc_mock:
            result = runner.invoke(cli.app, ['rescore', '5'])
        assert result.exit_code == 0
        assert 'Rescoring #5 (ACME)...' in result.output
        assert 'Done!' in result.output
        pend.update_fields.assert_called_once()
        assert pend.update_fields.call_args[0][0] == 7
        proc_mock.assert_called_once_with(7)

    def test_no_existing_pending_create_then_process(self):
        sess_j, sess_p = MagicMock(), MagicMock()
        job_repo = MagicMock()
        job_repo.get_by_num.return_value = {'num': 5, 'company': 'ACME', 'url': 'https://ex.com/job/5'}
        pend = MagicMock()
        pend.get_by_url.return_value = None
        pend.create.return_value = {'id': 8}
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, job_repo)), \
             patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, pend)), \
             patch('app.server.entrypoints.cli.process_pending_sync') as proc_mock:
            result = runner.invoke(cli.app, ['rescore', '5'])
        assert result.exit_code == 0
        pend.create.assert_called_once()
        proc_mock.assert_called_once_with(8)

    def test_process_failure(self):
        sess_j, sess_p = MagicMock(), MagicMock()
        job_repo = MagicMock()
        job_repo.get_by_num.return_value = {'num': 5, 'company': 'ACME', 'url': 'https://ex.com/job/5'}
        pend = MagicMock()
        pend.get_by_url.return_value = {'id': 7}
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, job_repo)), \
             patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, pend)), \
             patch('app.server.entrypoints.cli.process_pending_sync',
                   side_effect=RuntimeError('boom')):
            result = runner.invoke(cli.app, ['rescore', '5'])
        assert result.exit_code == 0
        assert 'Failed: boom' in result.output


# ── rescore_all ───────────────────────────────────────────────────

class TestRescoreAllCommand:
    def test_no_jobs(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.get_all_active.return_value = []
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['rescore-all'])
        assert result.exit_code == 0
        assert 'No processed jobs' in result.output

    def test_mixed_branches(self):
        sess_j, sess_p = MagicMock(), MagicMock()
        job_repo = MagicMock()
        job_repo.get_all_active.return_value = [
            {'num': 1, 'company': 'A', 'url': 'https://ex.com/a'},
            {'num': 2, 'company': 'B', 'url': 'https://ex.com/b'},
        ]
        pend = MagicMock()
        pend.get_by_url.side_effect = [{'id': 10}, None]
        pend.create.return_value = {'id': 11}
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess_j, job_repo)), \
             patch('app.server.entrypoints.cli._get_pending_repo', return_value=(sess_p, pend)), \
             patch('app.server.entrypoints.cli.process_pending_sync',
                   side_effect=[None, RuntimeError('x')]):
            result = runner.invoke(cli.app, ['rescore-all'])
        assert result.exit_code == 0
        assert 'Rescoring 2 jobs...' in result.output
        assert 'done' in result.output
        assert 'failed: x' in result.output
        assert pend.update_fields.call_count == 1
        pend.create.assert_called_once()


# ── status ────────────────────────────────────────────────────────

class TestStatusCommand:
    def test_counts_query(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.count.side_effect = [3, 1, 2, 4, 10]
        with patch('dependencies.get_session_sync', return_value=session):
            result = runner.invoke(cli.app, ['status'])
        assert result.exit_code != 0
        assert isinstance(result.exception, KeyError)
        assert session.query.return_value.filter.return_value.count.call_count == 5


# ── rules ─────────────────────────────────────────────────────────

class TestRulesCommand:
    def test_no_rules(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.get_all.return_value = []
        with patch('app.server.entrypoints.cli._get_rule_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['rules'])
        assert result.exit_code == 0
        assert 'No scoring rules set' in result.output

    def test_with_rules_grouped(self):
        rows = [
            {'rule_type': 'job', 'category': 'fit', 'enabled': 1, 'key': 'k1',
             'value': 'v1', 'description': 'desc1', 'priority': 1, 'score_weight': 5},
            {'rule_type': 'job', 'category': 'success', 'enabled': 0, 'key': 'k2',
             'value': 'v2', 'description': None, 'priority': 2, 'score_weight': None},
            {'rule_type': 'company', 'category': 'fit', 'enabled': 1, 'key': 'k3',
             'value': 'v3', 'description': 'd3', 'priority': 3, 'score_weight': 0},
        ]
        sess = MagicMock()
        repo = MagicMock()
        repo.get_all.return_value = rows
        with patch('app.server.entrypoints.cli._get_rule_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['rules'])
        assert result.exit_code == 0
        assert 'JOB RULES' in result.output
        assert 'COMPANY RULES' in result.output
        assert 'FIT' in result.output
        assert 'SUCCESS' in result.output
        assert 'k1 (w:5)' in result.output
        assert 'k2 (w:2)' in result.output
        assert 'desc1' in result.output


# ── add_rule ──────────────────────────────────────────────────────

class TestAddRuleCommand:
    def test_success(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.create.return_value = {'id': 1}
        with patch('app.server.entrypoints.cli._get_rule_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['add-rule', 'fit', 'python_core', 'True'])
        assert result.exit_code == 0
        assert 'Added: job/fit/python_core = True' in result.output
        repo.create.assert_called_once()

    def test_failure(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.create.side_effect = RuntimeError('boom')
        with patch('app.server.entrypoints.cli._get_rule_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['add-rule', 'fit', 'python_core', 'True'])
        assert result.exit_code == 0
        assert 'Failed: boom' in result.output


# ── generate_files ────────────────────────────────────────────────

class TestGenerateFilesCommand:
    def test_no_jobs(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.list_jobs.return_value = ([], 0)
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['generate-files'])
        assert result.exit_code == 0
        assert 'No jobs found' in result.output

    def test_job_num_deleted(self):
        sess = MagicMock()
        repo = MagicMock()
        repo.list_jobs.return_value = ([], 0)
        repo.get_by_num.return_value = {'num': 5, 'deleted': 1}
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)):
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '5'])
        assert result.exit_code == 0
        assert 'No jobs found' in result.output

    def test_writes_files(self, tmp_path):
        sess = MagicMock()
        repo = MagicMock()
        job = job_row(num=1, company='ACME Corp', role='Software/Engineer',
                      created_at='2024-01-15T10:00:00',
                      raw_description='raw text', structured_description='{"fit_score": 5}')
        repo.list_jobs.return_value = ([job], 1)
        repo.get_by_num.return_value = job
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)), \
             patch('app.server.entrypoints.cli.EXPORT_DIR', str(tmp_path)):
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '1'])
        assert result.exit_code == 0
        assert '2 files created, 0 skipped' in result.output
        base = '001_ACME_Corp_Software_Engineer_2024-01-15'
        raw_path = tmp_path / 'raw' / f'{base}.md'
        struct_path = tmp_path / 'structured' / f'{base}.json'
        assert raw_path.exists()
        assert raw_path.read_text() == 'raw text'
        assert struct_path.exists()
        assert json.loads(struct_path.read_text()) == {'fit_score': 5}

    def test_existing_files_skipped_then_forced(self, tmp_path):
        sess = MagicMock()
        repo = MagicMock()
        job = job_row(num=2)
        repo.list_jobs.return_value = ([job], 1)
        repo.get_by_num.return_value = job
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)), \
             patch('app.server.entrypoints.cli.EXPORT_DIR', str(tmp_path)):
            runner.invoke(cli.app, ['generate-files', '--job-num', '2'])
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '2'])
        assert result.exit_code == 0
        assert '0 files created, 2 skipped' in result.output
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)), \
             patch('app.server.entrypoints.cli.EXPORT_DIR', str(tmp_path)):
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '2', '--force'])
        assert result.exit_code == 0
        assert '2 files created, 0 skipped' in result.output

    def test_missing_descriptions_skipped(self, tmp_path):
        sess = MagicMock()
        repo = MagicMock()
        job = job_row(num=3, raw_description=None, structured_description=None)
        repo.list_jobs.return_value = ([job], 1)
        repo.get_by_num.return_value = job
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)), \
             patch('app.server.entrypoints.cli.EXPORT_DIR', str(tmp_path)):
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '3'])
        assert result.exit_code == 0
        assert '0 files created, 0 skipped' in result.output

    def test_bad_structured_json_skipped(self, tmp_path):
        sess = MagicMock()
        repo = MagicMock()
        job = job_row(num=4, structured_description='not-json')
        repo.list_jobs.return_value = ([job], 1)
        repo.get_by_num.return_value = job
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)), \
             patch('app.server.entrypoints.cli.EXPORT_DIR', str(tmp_path)):
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '4'])
        assert result.exit_code == 0
        assert '1 files created, 1 skipped' in result.output

    def test_non_string_created_at(self, tmp_path):
        sess = MagicMock()
        repo = MagicMock()
        job = job_row(num=5, created_at=20240101)
        repo.list_jobs.return_value = ([job], 1)
        repo.get_by_num.return_value = job
        with patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo)), \
             patch('app.server.entrypoints.cli.EXPORT_DIR', str(tmp_path)):
            result = runner.invoke(cli.app, ['generate-files', '--job-num', '5'])
        assert result.exit_code == 0
        assert '2 files created, 0 skipped' in result.output


# ── sync_db ───────────────────────────────────────────────────────

class TestSyncDbCommand:
    def _patch(self, jobs):
        sess = MagicMock()
        repo = MagicMock()
        repo.list_jobs.return_value = (jobs, len(jobs))
        return patch('app.server.entrypoints.cli._get_job_repo', return_value=(sess, repo))

    def test_all_complete(self):
        jobs = [job_row(num=1, raw_description='x', structured_description='{}')]
        with self._patch(jobs):
            result = runner.invoke(cli.app, ['sync-db'])
        assert result.exit_code == 0
        assert 'All jobs have both raw and structured descriptions' in result.output

    def test_missing_rows_dry_run(self):
        jobs = [
            job_row(num=1, company='A', role='Dev', raw_description=None, structured_description='{}'),
            job_row(num=2, company='B', role='QA', raw_description='x', structured_description=None),
        ]
        with self._patch(jobs):
            result = runner.invoke(cli.app, ['sync-db'])
        assert result.exit_code == 0
        assert 'Found 1 jobs missing raw_description' in result.output
        assert '#1 A — Dev' in result.output
        assert 'Found 1 jobs missing structured_description' in result.output
        assert '#2 B — QA' in result.output
        assert 'Dry run' in result.output

    def test_fix_reprocesses(self):
        fake_worker = types.ModuleType('jobs.infrastructure.workers.worker')
        fake_worker.process_job = MagicMock()
        jobs = [
            job_row(num=1, company='A', role='Dev', raw_description=None, structured_description='{}'),
            job_row(num=2, company='B', role='QA', raw_description=None, structured_description='{}'),
        ]
        with self._patch(jobs), \
             patch.dict(sys.modules, {'jobs.infrastructure.workers.worker': fake_worker}), \
             patch('app.server.entrypoints.cli.add_pending', side_effect=[42, None]) as add_mock:
            result = runner.invoke(cli.app, ['sync-db', '--fix'])
        assert result.exit_code == 0
        assert 'Re-processing missing jobs...' in result.output
        assert 'Skipped #1 — URL not available in DB for re-processing' in result.output
        assert 'Skipped #2 — could not create pending entry' in result.output
        assert add_mock.call_count == 2


# ── cleanup ───────────────────────────────────────────────────────

class TestCleanupCommand:
    def test_no_actions(self):
        result = runner.invoke(cli.app, ['cleanup'])
        assert result.exit_code == 0
        assert 'No cleanup actions specified' in result.output
        assert 'Done.' in result.output

    def test_reset_jobs_flag_alone_is_noop(self):
        result = runner.invoke(cli.app, ['cleanup', '--reset-jobs'])
        assert result.exit_code == 0
        assert 'No cleanup actions specified' not in result.output

    def test_kill_providers_with_pids(self):
        proc = MagicMock()
        proc.stdout = '123\n456\n'
        with patch('app.server.entrypoints.cli.subprocess.run', return_value=proc) as run_mock, \
             patch('app.server.entrypoints.cli.os.kill') as kill_mock:
            result = runner.invoke(cli.app, ['cleanup', '--kill-providers'])
        assert result.exit_code == 0
        assert 'Sent SIGTERM to PID 123' in result.output
        assert 'Sent SIGTERM to PID 456' in result.output
        run_mock.assert_called_once()
        assert kill_mock.call_count == 2

    def test_kill_providers_no_pids(self):
        proc = MagicMock()
        proc.stdout = ''
        with patch('app.server.entrypoints.cli.subprocess.run', return_value=proc):
            result = runner.invoke(cli.app, ['cleanup', '--kill-providers'])
        assert result.exit_code == 0
        assert 'No provider processes found' in result.output

    def test_kill_providers_oserror(self):
        proc = MagicMock()
        proc.stdout = '123\n'
        with patch('app.server.entrypoints.cli.subprocess.run', return_value=proc), \
             patch('app.server.entrypoints.cli.os.kill', side_effect=OSError('denied')):
            result = runner.invoke(cli.app, ['cleanup', '--kill-providers'])
        assert result.exit_code == 0
        assert 'Failed to kill PID 123: denied' in result.output

    def test_reset_roadmaps(self):
        session = MagicMock()
        session.query.return_value.filter.return_value.update.return_value = 3
        with patch('dependencies.get_session_sync', return_value=session):
            result = runner.invoke(cli.app, ['cleanup', '--reset-roadmaps'])
        assert result.exit_code == 0
        assert 'Reset 3 jobs' in result.output
        session.commit.assert_called_once()

    def test_all_flag(self):
        proc = MagicMock()
        proc.stdout = '123\n'
        session = MagicMock()
        session.query.return_value.filter.return_value.update.return_value = 2
        with patch('app.server.entrypoints.cli.subprocess.run', return_value=proc), \
             patch('app.server.entrypoints.cli.os.kill'), \
             patch('dependencies.get_session_sync', return_value=session):
            result = runner.invoke(cli.app, ['cleanup', '--all'])
        assert result.exit_code == 0
        assert 'Sent SIGTERM to PID 123' in result.output
        assert 'Reset 2 jobs' in result.output
