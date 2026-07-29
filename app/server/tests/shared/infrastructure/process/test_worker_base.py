"""Tests for WorkerBase — Template Method pattern for processing pipelines."""

import pytest
from unittest.mock import MagicMock, patch, call
from shared.infrastructure.process.worker_base import WorkerBase
from shared.infrastructure.process.models import ItemStatus, PipelineStep


class FakeWorker(WorkerBase):
    """Concrete worker for testing — simulates a 3-step pipeline with cancellation checks."""

    @property
    def table(self):
        return 'pending_jobs'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_analyze', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._log(pid, 'start', f'Processing {item.get("url", "")}')

        if self._is_cancelled(pid):
            return None
        self._start_step(pid, 'step_fetch')
        self._mark_step(pid, 'step_fetch')
        self._log(pid, 'fetch', 'Fetched')

        if self._is_cancelled(pid):
            return None
        self._start_step(pid, 'step_analyze')
        self._mark_step(pid, 'step_analyze')
        self._log(pid, 'analyze', 'Analyzed')

        if self._is_cancelled(pid):
            return None
        self._start_step(pid, 'step_done')
        self._mark_step(pid, 'step_done')

        return {'num': 42, 'company': 'TestCorp'}


class FailingWorker(WorkerBase):
    """Worker that fails on purpose."""

    @property
    def table(self):
        return 'pending_jobs'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_done']

    def _execute_pipeline(self, pid, item):
        raise RuntimeError("Pipeline exploded")


@pytest.fixture
def mocks():
    pending_repo = MagicMock()
    pending_repo.get.return_value = {'id': 1, 'url': 'https://example.com', 'status': 'processing'}
    pending_repo.update_status.return_value = None
    pending_repo.update_step.return_value = None
    pending_repo.append_log.return_value = None

    process_mgr = MagicMock()
    temp_mgr = MagicMock()
    mimo_runner = MagicMock()
    broadcaster = MagicMock()

    return {
        'pending_repo': pending_repo,
        'process_mgr': process_mgr,
        'temp_mgr': temp_mgr,
        'mimo_runner': mimo_runner,
        'broadcaster': broadcaster,
    }


class TestWorkerBase:
    def test_successful_pipeline(self, mocks):
        worker = FakeWorker(**mocks)
        worker.process(1)

        # Should mark complete
        mocks['pending_repo'].update_status.assert_called_with(
            1, 'completed'
        )
        # Should broadcast completion
        mocks['broadcaster'].complete.assert_called_once()
        # Should clean temp files
        mocks['temp_mgr'].cleanup.assert_called_with('1')

    def test_failed_pipeline(self, mocks):
        worker = FailingWorker(**mocks)
        worker.process(1)

        # Should mark failed
        status_call = mocks['pending_repo'].update_status.call_args
        assert status_call[0][1] == ItemStatus.FAILED
        assert 'Pipeline exploded' in status_call[1].get('error', status_call[0][2] if len(status_call[0]) > 2 else '')

    def test_cancelled_item_stops(self, mocks):
        # Item is paused, not processing — mock returns same status for all get() calls
        paused_item = {'id': 1, 'status': 'paused', 'url': 'https://example.com'}
        mocks['pending_repo'].get.return_value = paused_item
        worker = FakeWorker(**mocks)
        worker.process(1)

        # Should not broadcast completion (pipeline was cancelled)
        mocks['broadcaster'].complete.assert_not_called()

    def test_nonexistent_item(self, mocks):
        mocks['pending_repo'].get.return_value = None
        worker = FakeWorker(**mocks)
        worker.process(999)

        # Should not crash, should not broadcast
        mocks['broadcaster'].complete.assert_not_called()

    def test_steps_broadcast(self, mocks):
        worker = FakeWorker(**mocks)
        worker.process(1)

        # Should have broadcast step updates
        step_calls = [c for c in mocks['broadcaster'].step_update.call_args_list]
        assert len(step_calls) >= 3  # at least 3 steps

    def test_logs_broadcast(self, mocks):
        worker = FakeWorker(**mocks)
        worker.process(1)

        # Should have broadcast log entries
        log_calls = mocks['broadcaster'].log.call_args_list
        assert len(log_calls) >= 1
