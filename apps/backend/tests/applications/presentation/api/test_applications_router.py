"""Tests for the Applications API router.

Covers:
- Create / get-by-job / update application
- Follow-ups CRUD
- Document update / delete
- Generation dispatch (preparation + documents) → creates ProcessingExecution
- Invalid input handling
"""

from __future__ import annotations

import json
import uuid

import pytest

from applications.infrastructure.models.application_model import (
    ApplicationDocumentModel,
    ApplicationFollowUpModel,
    ApplicationModel,
    ApplicationPreparationModel,
)
from jobs.infrastructure.models.job_model import JobModel
from processing.infrastructure.models.processing_execution_model import ProcessingExecutionModel


def _create_job(sa_session, **kwargs) -> JobModel:
    defaults = dict(
        id=str(uuid.uuid7()),
        url="https://example.com/job",
        title="Software Engineer",
        role="SWE",
        company="Tech Corp",
        location="Berlin",
        work_types='["Remote"]',
        employment_types='["Full-time"]',
        status="imported",
        deleted=0,
        workflow_log="[]",
        locations="[]",
        rescoring=0,
    )
    defaults.update(kwargs)
    defaults.pop("num", None)
    job = JobModel(**defaults)
    sa_session.add(job)
    sa_session.commit()
    return job


def _create_application(sa_session, job_id: str, **kwargs) -> ApplicationModel:
    defaults = dict(
        id=str(uuid.uuid7()),
        job_id=job_id,
        status="recommended",
    )
    defaults.update(kwargs)
    app = ApplicationModel(**defaults)
    sa_session.add(app)
    sa_session.commit()
    return app


class TestApplicationAPI:
    def test_create_application(self, client, sa_session):
        job = _create_job(sa_session)
        resp = client.post("/api/applications", json={"job_id": job.id})
        assert resp.status_code == 201
        body = resp.json()
        assert body["job_id"] == job.id
        assert body["status"] == "recommended"
        assert body["follow_ups"] == []
        assert body["documents"] == []
        assert body["preparation"] is None

    def test_create_is_idempotent(self, client, sa_session):
        job = _create_job(sa_session)
        first = client.post("/api/applications", json={"job_id": job.id}).json()
        second = client.post("/api/applications", json={"job_id": job.id}).json()
        assert second["id"] == first["id"]

    def test_get_application_by_job(self, client, sa_session):
        job = _create_job(sa_session)
        created = client.post("/api/applications", json={"job_id": job.id}).json()
        resp = client.get(f"/api/applications/by-job/{job.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_by_job_404_when_none(self, client):
        resp = client.get("/api/applications/by-job/some-missing-job")
        assert resp.status_code == 404

    def test_update_status(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        resp = client.patch(f"/api/applications/{app.id}", json={"status": "applied", "applied_at": "2026-08-01"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "applied"
        assert body["applied_at"] == "2026-08-01"

    def test_update_invalid_status_422(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        resp = client.patch(f"/api/applications/{app.id}", json={"status": "bogus"})
        assert resp.status_code == 422

    def test_update_missing_404(self, client):
        resp = client.patch("/api/applications/nope", json={"status": "applied"})
        assert resp.status_code == 404


class TestFollowUpAPI:
    def test_add_and_list(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        resp = client.post(
            f"/api/applications/{app.id}/follow-ups",
            json={"scheduled_at": "2026-08-10", "note": "Nudge recruiter"},
        )
        assert resp.status_code == 201
        fu = resp.json()
        assert fu["note"] == "Nudge recruiter"

        detail = client.get(f"/api/applications/by-job/{job.id}").json()
        assert len(detail["follow_ups"]) == 1

    def test_complete_follow_up(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        fu = client.post(
            f"/api/applications/{app.id}/follow-ups", json={"note": "nudge"}
        ).json()
        resp = client.patch(f"/api/applications/follow-ups/{fu['id']}", json={"completed": True})
        assert resp.status_code == 200
        assert resp.json()["completed_at"] is not None

    def test_delete_follow_up(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        fu = client.post(
            f"/api/applications/{app.id}/follow-ups", json={"note": "nudge"}
        ).json()
        resp = client.delete(f"/api/applications/follow-ups/{fu['id']}")
        assert resp.status_code == 204
        assert sa_session.query(ApplicationFollowUpModel).filter(
            ApplicationFollowUpModel.id == fu["id"]
        ).first() is None


class TestDocumentAPI:
    def test_update_document(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        doc = ApplicationDocumentModel(
            id=str(uuid.uuid7()),
            application_id=app.id,
            document_type="cover_letter",
            version=1,
            content="draft",
        )
        sa_session.add(doc)
        sa_session.commit()

        resp = client.patch(f"/api/applications/documents/{doc.id}", json={"content": "## Final letter"})
        assert resp.status_code == 200
        assert resp.json()["content"] == "## Final letter"

    def test_update_document_empty_400(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        doc = ApplicationDocumentModel(
            id=str(uuid.uuid7()),
            application_id=app.id,
            document_type="tailored_resume",
            version=1,
            content="draft",
        )
        sa_session.add(doc)
        sa_session.commit()
        resp = client.patch(f"/api/applications/documents/{doc.id}", json={"content": "  "})
        assert resp.status_code == 422

    def test_delete_document(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        doc = ApplicationDocumentModel(
            id=str(uuid.uuid7()),
            application_id=app.id,
            document_type="cover_letter",
            version=1,
            content="draft",
        )
        sa_session.add(doc)
        sa_session.commit()
        doc_id = str(doc.id)
        resp = client.delete(f"/api/applications/documents/{doc_id}")
        assert resp.status_code == 200
        sa_session.expire_all()
        assert sa_session.query(ApplicationDocumentModel).filter(
            ApplicationDocumentModel.id == doc_id
        ).first() is None


class TestGenerationDispatchAPI:
    def test_generate_preparation_queues_execution(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        resp = client.post(f"/api/applications/{app.id}/preparation/generate")
        assert resp.status_code == 202
        body = resp.json()
        assert body["artifact"] == "preparation"
        assert body["status"] == "queued"
        execution = sa_session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.id == body["execution_id"]
        ).first()
        assert execution is not None
        assert execution.execution_type == "application_preparation"
        assert execution.target_type == "application"
        assert execution.target_id == app.id

    def test_generate_documents_queues_typed_executions(self, client, sa_session):
        job1 = _create_job(sa_session)
        job2 = _create_job(sa_session, url="https://other.example")
        app1 = _create_application(sa_session, job1.id)
        app2 = _create_application(sa_session, job2.id)
        resume = client.post(f"/api/applications/{app1.id}/documents/tailored_resume/generate")
        letter = client.post(f"/api/applications/{app2.id}/documents/cover_letter/generate")
        assert resume.status_code == 202
        assert letter.status_code == 202
        resume_exec = sa_session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.id == resume.json()["execution_id"]
        ).first()
        letter_exec = sa_session.query(ProcessingExecutionModel).filter(
            ProcessingExecutionModel.id == letter.json()["execution_id"]
        ).first()
        assert resume_exec.execution_type == "application_resume"
        assert letter_exec.execution_type == "application_cover_letter"

    def test_generate_invalid_document_type_400(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        resp = client.post(f"/api/applications/{app.id}/documents/bogus/generate")
        assert resp.status_code == 400

    def test_generate_missing_application_404(self, client):
        resp = client.post("/api/applications/nope/preparation/generate")
        assert resp.status_code == 404


class TestPreparationDetail:
    def test_preparation_serialized_in_detail(self, client, sa_session):
        job = _create_job(sa_session)
        app = _create_application(sa_session, job.id)
        sa_session.add(ApplicationPreparationModel(
            id=str(uuid.uuid7()),
            application_id=app.id,
            version=1,
            payload=json.dumps({
                "hard_skills": [{"skill": "kubernetes", "gap_level": "missing", "priority": "high"}],
                "soft_skills": [{"skill": "communication", "priority": "medium"}],
            }),
        ))
        sa_session.commit()

        detail = client.get(f"/api/applications/by-job/{job.id}").json()
        prep = detail["preparation"]
        assert prep is not None
        assert prep["version"] == 1
        assert prep["hard_skills"][0]["skill"] == "kubernetes"
        assert prep["soft_skills"][0]["skill"] == "communication"
