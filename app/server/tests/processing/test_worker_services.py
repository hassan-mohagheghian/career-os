"""Tests for worker services (JobWorker, CompanyWorker, GenerationWorker).

TDD: Tests written BEFORE implementation.
Tests cover: WorkerBase subclassing, pipeline execution, status transitions.
"""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from processing.infrastructure.models.pending_model import (
    PendingJobModel, PendingCompanyModel, PendingGenerationModel,
)
from shared.domain.models.generation_models import GenerationSource, GenerationStatus
from shared.infrastructure.process.models import ItemStatus, WorkflowLogEntry, StatusUpdate, ProcessingComplete
from shared.infrastructure.process.worker_base import WorkerBase


# ── Concrete WorkerBase implementations for testing ──────────────

class ConcreteWorker(WorkerBase):
    """Test implementation of WorkerBase."""

    @property
    def table(self):
        return 'pending_jobs'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_analyze', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._mark_step(pid, 'step_fetch')
        self._log(pid, 'fetch', 'Fetched content')
        if self._is_cancelled(pid):
            return None
        self._mark_step(pid, 'step_analyze')
        self._log(pid, 'analyze', 'Analyzed')
        return {'result': 'ok', 'num': 42}


class FailingWorker(WorkerBase):
    """Worker that fails at step 2."""

    @property
    def table(self):
        return 'pending_jobs'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_analyze', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._mark_step(pid, 'step_fetch')
        raise RuntimeError("AI service unavailable")


class CompanyTestWorker(WorkerBase):
    """Test company worker."""

    @property
    def table(self):
        return 'pending_companies'

    @property
    def pipeline_steps(self):
        return ['step_fetch', 'step_extract', 'step_analyze', 'step_save', 'step_done']

    def _execute_pipeline(self, pid, item):
        self._mark_step(pid, 'step_fetch')
        self._mark_step(pid, 'step_extract')
        self._mark_step(pid, 'step_analyze')
        self._mark_step(pid, 'step_save')
        return {'company_id': 1, 'name': 'TestCo'}


# ── Tests ──────────────────────────────────────────────────────────

class TestWorkerBase:
    """Test the abstract WorkerBase Template Method pattern."""

    def _make_worker(self, sa_session):
        from shared.infrastructure.process.repository import PendingJobRepository

        repo = PendingJobRepository(sa_session)
        proc_mgr = MagicMock()
        temp_mgr = MagicMock()
        mimo = MagicMock()
        broadcaster = MagicMock()

        return ConcreteWorker(repo, proc_mgr, temp_mgr, mimo, broadcaster)

    def _insert_pending_job(self, sa_session, url='https://example.com', status='processing'):
        m = PendingJobModel(
            url=url,
            status=status,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)
        return m.id

    def test_successful_pipeline(self, sa_session):
        worker = self._make_worker(sa_session)
        pid = self._insert_pending_job(sa_session)

        worker.process(pid)

        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'done'
        assert row.step_fetch == 1
        assert row.step_analyze == 1
        assert row.step_done == 1

    def test_failed_pipeline(self, sa_session):
        from shared.infrastructure.process.repository import PendingJobRepository

        repo = PendingJobRepository(sa_session)
        worker = FailingWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())
        pid = self._insert_pending_job(sa_session)

        worker.process(pid)

        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.status == 'failed'
        assert row.error is not None

    def test_workflow_log_recorded(self, sa_session):
        worker = self._make_worker(sa_session)
        pid = self._insert_pending_job(sa_session)

        worker.process(pid)

        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        logs = json.loads(row.workflow_log or '[]')
        assert len(logs) >= 2
        assert logs[0]['msg'] == 'Fetched content'
        assert logs[1]['msg'] == 'Analyzed'

    def test_missing_item_returns_early(self, sa_session):
        worker = self._make_worker(sa_session)
        # Process non-existent item - should not raise
        worker.process(99999)

    def test_cancelled_item_stops(self, sa_session):
        from shared.infrastructure.process.repository import PendingJobRepository

        repo = PendingJobRepository(sa_session)
        worker = FailingWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())
        pid = self._insert_pending_job(sa_session, url='https://paused.example.com', status='paused')

        # Paused item should be detected as cancelled
        assert worker._is_cancelled(pid) is True

    def test_company_worker_table(self, sa_session):
        from shared.infrastructure.process.repository import PendingCompanyRepository

        repo = PendingCompanyRepository(sa_session)
        worker = CompanyTestWorker(repo, MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert worker.table == 'pending_companies'
        assert len(worker.pipeline_steps) == 5

    def test_reset_steps(self, sa_session):
        worker = self._make_worker(sa_session)
        pid = self._insert_pending_job(sa_session)

        # Manually set steps
        m = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        m.step_fetch = 1
        m.step_analyze = 1
        sa_session.commit()

        worker._reset_steps(pid)

        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        assert row.step_fetch == 0
        assert row.step_analyze == 0

    def test_mark_step_broadcasts(self, sa_session):
        worker = self._make_worker(sa_session)
        pid = self._insert_pending_job(sa_session)

        with patch.object(worker._broadcaster, 'step_update') as mock_broadcast:
            worker._mark_step(pid, 'step_fetch', 1)
            mock_broadcast.assert_called_once()
            event = mock_broadcast.call_args[0][0]
            assert isinstance(event, StatusUpdate)
            assert event.step == 'step_fetch'
            assert event.val == 1

    def test_log_appends_entry(self, sa_session):
        worker = self._make_worker(sa_session)
        pid = self._insert_pending_job(sa_session)

        worker._log(pid, 'test', 'Test message')

        row = sa_session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        logs = json.loads(row.workflow_log or '[]')
        assert len(logs) == 1
        assert logs[0]['step'] == 'test'
        assert logs[0]['msg'] == 'Test message'
