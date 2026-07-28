"""Tests for PendingJobRepository — SQLAlchemy persistence layer."""

import pytest
from sqlalchemy.orm import Session
from shared.infrastructure.process.repository import PendingJobRepository, JobRepository
from shared.infrastructure.process.models import ItemStatus, WorkflowLogEntry
from processing.infrastructure.models.pending_model import PendingJobModel
from jobs.infrastructure.models.job_model import JobModel
from shared.infrastructure.database.models.misc_models import SummaryModel, ResumeModel


@pytest.fixture
def pending_repo(sa_session: Session):
    return PendingJobRepository(sa_session)


@pytest.fixture
def job_repo(sa_session: Session):
    return JobRepository(sa_session)


class TestPendingJobRepository:
    def test_insert_and_get(self, pending_repo, sa_session: Session):
        m = PendingJobModel(url='https://example.com', status='queued')
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)

        item = pending_repo.get(m.id)
        assert item is not None
        assert item['url'] == 'https://example.com'
        assert item['status'] == 'queued'

    def test_get_nonexistent(self, pending_repo):
        assert pending_repo.get(999) is None

    def test_update_status(self, pending_repo, sa_session: Session):
        m = PendingJobModel(url='https://example.com', status='queued')
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)

        pending_repo.update_status(m.id, ItemStatus.PROCESSING)
        item = pending_repo.get(m.id)
        assert item['status'] == 'processing'

    def test_update_step(self, pending_repo, sa_session: Session):
        m = PendingJobModel(url='https://example.com', status='processing')
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)

        pending_repo.update_step(m.id, 'step_fetch', 1)
        item = pending_repo.get(m.id)
        assert item['step_fetch'] == 1

    def test_append_log(self, pending_repo, sa_session: Session):
        m = PendingJobModel(url='https://example.com', status='processing')
        sa_session.add(m)
        sa_session.commit()
        sa_session.refresh(m)

        entry = WorkflowLogEntry(step='fetch', msg='Fetched 1000 chars', ts='12:00:00')
        pending_repo.append_log(m.id, entry)

        logs = pending_repo.get_logs(m.id)
        assert len(logs) == 1
        assert logs[0].msg == 'Fetched 1000 chars'

    def test_claim_next(self, pending_repo, sa_session: Session):
        a = PendingJobModel(url='https://a.com', status='queued', queue_order=1)
        b = PendingJobModel(url='https://b.com', status='queued', queue_order=2)
        sa_session.add_all([a, b])
        sa_session.commit()
        sa_session.refresh(a)

        claimed = pending_repo.claim_next()
        assert claimed is not None
        assert claimed['url'] == 'https://a.com'

        item = pending_repo.get(claimed['id'])
        assert item['status'] == 'processing'

    def test_claim_next_empty(self, pending_repo):
        assert pending_repo.claim_next() is None

    def test_count_by_status(self, pending_repo, sa_session: Session):
        sa_session.add_all([
            PendingJobModel(url='https://a.com', status='queued'),
            PendingJobModel(url='https://b.com', status='processing'),
            PendingJobModel(url='https://c.com', status='done'),
        ])
        sa_session.commit()

        counts = pending_repo.count_by_status()
        assert counts[ItemStatus.QUEUED] == 1
        assert counts[ItemStatus.PROCESSING] == 1
        assert counts[ItemStatus.DONE] == 1
        assert counts[ItemStatus.PENDING] == 0


class TestJobRepository:
    def test_get_next_num(self, job_repo, sa_session: Session):
        assert job_repo.get_next_num() == 1

        m = JobModel(num=5, company='Corp', url='https://x.com')
        sa_session.add(m)
        sa_session.commit()

        assert job_repo.get_next_num() == 6

    def test_get_by_url(self, job_repo, sa_session: Session):
        m = JobModel(num=1, company='Corp', url='https://x.com', score='A', match='High', deleted=0)
        sa_session.add(m)
        sa_session.commit()

        job = job_repo.get_by_url('https://x.com')
        assert job is not None
        assert job['company'] == 'Corp'

    def test_get_by_url_deleted(self, job_repo, sa_session: Session):
        m = JobModel(num=1, company='Corp', url='https://x.com', score='A', match='High', deleted=1)
        sa_session.add(m)
        sa_session.commit()

        assert job_repo.get_by_url('https://x.com') is None
