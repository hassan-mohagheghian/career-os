"""Tests for the application repository job-tracking lookup methods."""

from applications.infrastructure.repositories.sa_application_repository import SQLAlchemyApplicationRepository
from applications.infrastructure.models.application_model import ApplicationModel


def _create_application(sa_session, job_id: str, status: str) -> ApplicationModel:
    import uuid
    model = ApplicationModel(id=str(uuid.uuid7()), job_id=job_id, status=status)
    sa_session.add(model)
    sa_session.commit()
    return model


class TestApplicationTrackingLookups:
    def test_statuses_by_job_ids_maps_job_to_status(self, sa_session):
        _create_application(sa_session, "job-1", "applied")
        _create_application(sa_session, "job-2", "interview")

        repo = SQLAlchemyApplicationRepository(sa_session)
        assert repo.statuses_by_job_ids(["job-1", "job-2"]) == {
            "job-1": "applied",
            "job-2": "interview",
        }

    def test_statuses_by_job_ids_omits_jobs_without_application(self, sa_session):
        _create_application(sa_session, "job-1", "applied")

        repo = SQLAlchemyApplicationRepository(sa_session)
        assert repo.statuses_by_job_ids(["job-1", "missing"]) == {"job-1": "applied"}

    def test_statuses_by_job_ids_empty_input(self, sa_session):
        repo = SQLAlchemyApplicationRepository(sa_session)
        assert repo.statuses_by_job_ids([]) == {}

    def test_job_ids_with_application_lists_applied_jobs(self, sa_session):
        _create_application(sa_session, "job-1", "applied")
        _create_application(sa_session, "job-2", "accepted")

        repo = SQLAlchemyApplicationRepository(sa_session)
        assert set(repo.job_ids_with_application()) == {"job-1", "job-2"}

    def test_job_ids_with_application_empty(self, sa_session):
        repo = SQLAlchemyApplicationRepository(sa_session)
        assert repo.job_ids_with_application() == []
