"""Tests for utility classes, schemas, exceptions, and mappers."""
import pytest

from shared.infrastructure.process.models import (
    StatusUpdate, WorkflowLogEntry, ProcessingComplete, ProcessingError
)
from shared.application.exceptions import (
    AppError, NotFoundError, ConflictError, ValidationError,
)


class TestStatusUpdate:
    def test_fields(self):
        s = StatusUpdate(table='pending_jobs', pid=123, step='fetch', val=1, extra=None)
        assert s.table == 'pending_jobs'
        assert s.pid == 123


class TestWorkflowLogEntry:
    def test_fields(self):
        e = WorkflowLogEntry(step='fetch', msg='ok')
        assert e.step == 'fetch'

    def test_to_dict(self):
        e = WorkflowLogEntry(step='fetch', msg='ok')
        d = e.to_dict()
        assert d['step'] == 'fetch'


class TestProcessingComplete:
    def test_fields(self):
        p = ProcessingComplete(table='pending_jobs', pid=1, result={})
        assert p.pid == 1


class TestProcessingError:
    def test_fields(self):
        e = ProcessingError(table='pending_jobs', pid=1, msg='fail')
        assert e.msg == 'fail'


class TestAppError:
    def test_base(self):
        e = AppError(detail='Bad request')
        assert e.status_code == 500

    def test_not_found(self):
        e = NotFoundError('Job not found')
        assert e.status_code == 404

    def test_conflict(self):
        e = ConflictError('Already exists')
        assert e.status_code == 409

    def test_validation(self):
        e = ValidationError('Invalid')
        assert e.status_code == 422


# ── Mappers ────────────────────────────────────────────────────────

class TestMappers:
    def test_job_model_to_dict(self):
        from shared.infrastructure.database.mappers import job_model_to_dict
        from jobs.infrastructure.models.job_model import JobModel
        model = JobModel(id='job-1', url='https://example.com', status='pending')
        d = job_model_to_dict(model)
        assert d['url'] == 'https://example.com'
        assert d['id'] == 'job-1'

    def test_dict_to_job_model(self):
        from shared.infrastructure.database.mappers import dict_to_job_model
        model = dict_to_job_model({'id': 'job-1', 'url': 'https://ex.com', 'status': 'pending'})
        assert model.url == 'https://ex.com'
        assert model.id == 'job-1'

    def test_company_model_to_dict(self):
        from shared.infrastructure.database.mappers import company_model_to_dict
        from companies.infrastructure.models.company_model import CompanyModel
        model = CompanyModel(name='TestCorp', status='done')
        d = company_model_to_dict(model)
        assert d['name'] == 'TestCorp'

    def test_dict_to_company_model(self):
        from shared.infrastructure.database.mappers import dict_to_company_model
        model = dict_to_company_model({'name': 'TestCorp', 'status': 'done'})
        assert model.name == 'TestCorp'
