"""Tests for PendingJobRepository — SQLAlchemy persistence layer."""

import uuid

import pytest
from sqlalchemy.orm import Session
from shared.infrastructure.process.repository import PendingJobRepository
from shared.infrastructure.process.models import ItemStatus, JobStatus, WorkflowLogEntry
from jobs.infrastructure.models.job_model import JobModel


@pytest.fixture
def pending_repo(sa_session: Session):
    return PendingJobRepository(sa_session)


def _add(sa_session: Session, **kw) -> JobModel:
    m = JobModel(id=str(uuid.uuid7()), user_id="test-user", **kw)
    sa_session.add(m)
    sa_session.commit()
    sa_session.refresh(m)
    return m


class TestPendingJobRepository:
    def test_insert_and_get(self, pending_repo, sa_session: Session):
        m = _add(sa_session, url='https://example.com', status='queued')

        item = pending_repo.get(m.id)
        assert item is not None
        assert item['url'] == 'https://example.com'
        assert item['status'] == 'queued'

    def test_get_nonexistent(self, pending_repo):
        assert pending_repo.get('999') is None

    def test_update_status(self, pending_repo, sa_session: Session):
        m = _add(sa_session, url='https://example.com', status='queued')

        pending_repo.update_status(m.id, ItemStatus.PROCESSING)
        item = pending_repo.get(m.id)
        assert item['status'] == 'processing'

    def test_update_step(self, pending_repo, sa_session: Session):
        m = _add(sa_session, url='https://example.com', status='processing')

        pending_repo.update_step(m.id, 'workflow_log', '[]')
        item = pending_repo.get(m.id)
        assert item['workflow_log'] == '[]'

    def test_append_log(self, pending_repo, sa_session: Session):
        m = _add(sa_session, url='https://example.com', status='processing')

        entry = WorkflowLogEntry(step='fetch', msg='Fetched 1000 chars', ts='12:00:00')
        pending_repo.append_log(m.id, entry)

        logs = pending_repo.get_logs(m.id)
        assert len(logs) == 1
        assert logs[0].msg == 'Fetched 1000 chars'

    def test_claim_next(self, pending_repo, sa_session: Session):
        a = _add(sa_session, url='https://a.com', status='queued', queue_order=1)
        b = _add(sa_session, url='https://b.com', status='queued', queue_order=2)

        claimed = pending_repo.claim_next()
        assert claimed is not None
        assert claimed['url'] == 'https://a.com'

        item = pending_repo.get(claimed['id'])
        assert item['status'] == 'processing'

    def test_claim_next_empty(self, pending_repo):
        assert pending_repo.claim_next() is None

    def test_count_by_status(self, pending_repo, sa_session: Session):
        _add(sa_session, url='https://a.com', status='queued')
        _add(sa_session, url='https://b.com', status='processing')
        _add(sa_session, url='https://c.com', status='processed')

        counts = pending_repo.count_by_status()
        assert counts[JobStatus.QUEUED.value] == 1
        assert counts[JobStatus.PROCESSING.value] == 1
        assert counts[JobStatus.PROCESSED.value] == 1
        assert counts[JobStatus.PENDING.value] == 0