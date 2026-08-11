"""Tests for the Applications bounded context services and domain events.

Covers:
- ApplicationService (get-by-job, idempotent create, status/applied_at update)
- FollowUpService (add/complete/update/delete)
- DocumentService (update content, delete)
- Domain event emission (best-effort, in-memory collector)
"""

from __future__ import annotations

from datetime import datetime, UTC

import pytest

from applications.application.services.application_service import ApplicationService
from applications.application.services.document_service import DocumentService
from applications.application.services.follow_up_service import FollowUpService
from applications.domain.entities.application import (
    Application,
    ApplicationDocument,
    ApplicationFollowUp,
    ApplicationPreparation,
    ApplicationStatus,
    DocumentType,
)
from applications.domain.events import (
    ApplicationCreated,
    ApplicationDocumentDeleted,
    ApplicationDocumentGenerated,
    ApplicationDocumentUpdated,
    ApplicationFollowUpAdded,
    ApplicationFollowUpDeleted,
    ApplicationFollowUpUpdated,
    ApplicationPreparationGenerated,
    ApplicationUpdated,
)
from shared.application.exceptions import NotFoundError, ValidationError


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #


class FakeApplicationRepo:
    def __init__(self):
        self._rows: dict[str, dict] = {}
        self._next = 1

    def _new(self, data):
        app = dict(data)
        app["id"] = f"app-{self._next}"
        self._next += 1
        return app

    def get_by_id(self, application_id):
        return self._rows.get(application_id)

    def get_by_job_id(self, job_id):
        return next((r for r in self._rows.values() if r["job_id"] == job_id), None)

    def list_ids_by_job(self, job_id):
        return [r["id"] for r in self._rows.values() if r["job_id"] == job_id]

    def create(self, data):
        stored = self._new(data)
        self._rows[stored["id"]] = stored
        return stored

    def update(self, application_id, data):
        row = self._rows.get(application_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete_by_job(self, job_id):
        ids = self.list_ids_by_job(job_id)
        for i in ids:
            self._rows.pop(i, None)
        return len(ids)


class FakeFollowUpRepo:
    def __init__(self):
        self._rows: dict[str, dict] = {}
        self._next = 1

    def create(self, data):
        row = dict(data)
        row["id"] = f"fu-{self._next}"
        self._next += 1
        self._rows[row["id"]] = row
        return row

    def get_by_id(self, follow_up_id):
        return self._rows.get(follow_up_id)

    def update(self, follow_up_id, data):
        row = self._rows.get(follow_up_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete(self, follow_up_id):
        return self._rows.pop(follow_up_id, None) is not None

    def list_for_application(self, application_id):
        return [r for r in self._rows.values() if r["application_id"] == application_id]


class FakeDocumentRepo:
    def __init__(self):
        self._rows: dict[str, dict] = {}
        self._next = 1

    def create(self, data):
        row = dict(data)
        row["id"] = f"doc-{self._next}"
        self._next += 1
        self._rows[row["id"]] = row
        return row

    def get_by_id(self, document_id):
        return self._rows.get(document_id)

    def update(self, document_id, data):
        row = self._rows.get(document_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete(self, document_id):
        return self._rows.pop(document_id, None) is not None

    def list_for_application(self, application_id):
        return [r for r in self._rows.values() if r["application_id"] == application_id]

    def list_by_type(self, application_id, document_type):
        return [r for r in self._rows.values()
                if r["application_id"] == application_id and r["document_type"] == document_type]

    def get_next_version(self, application_id, document_type):
        rows = self.list_by_type(application_id, document_type)
        return int(rows[0]["version"]) + 1 if rows else 1


class RecordingCollector:
    def __init__(self):
        self._events = []

    def publish(self, event):
        self._events.append(event)

    @property
    def events(self):
        return list(self._events)


# --------------------------------------------------------------------------- #
# Entities
# --------------------------------------------------------------------------- #


class TestEntities:
    def test_application_to_dict_defaults(self):
        app = Application(job_id="job-1")
        data = app.to_dict()
        assert data["job_id"] == "job-1"
        assert data["status"] == ApplicationStatus.RECOMMENDED
        assert data["applied_at"] is None

    def test_document_and_follow_up_dicts(self):
        doc = ApplicationDocument(application_id="app-1", document_type=DocumentType.TAILORED_RESUME, version=1)
        assert doc.to_dict()["document_type"] == DocumentType.TAILORED_RESUME
        fu = ApplicationFollowUp(application_id="app-1", scheduled_at="2026-01-01")
        assert fu.completed is False
        assert fu.to_dict()["scheduled_at"] == "2026-01-01"

    def test_preparation_dict(self):
        prep = ApplicationPreparation(application_id="app-1", payload={"hard_skills": []})
        assert prep.to_dict()["payload"] == {"hard_skills": []}


# --------------------------------------------------------------------------- #
# ApplicationService
# --------------------------------------------------------------------------- #


class TestApplicationService:
    def test_create_emits_created_event(self):
        collector = RecordingCollector()
        service = ApplicationService(FakeApplicationRepo(), collector)
        stored = service.create("job-1")
        assert stored["job_id"] == "job-1"
        assert stored["status"] == ApplicationStatus.RECOMMENDED
        assert any(isinstance(e, ApplicationCreated) and e.job_id == "job-1" for e in collector.events)

    def test_create_is_idempotent_per_job(self):
        service = ApplicationService(FakeApplicationRepo(), RecordingCollector())
        first = service.create("job-1")
        second = service.create("job-1")
        assert second["id"] == first["id"]

    def test_create_rejects_invalid_status(self):
        service = ApplicationService(FakeApplicationRepo(), RecordingCollector())
        with pytest.raises(ValidationError):
            service.create("job-1", status="bogus")

    def test_get_by_job(self):
        repo = FakeApplicationRepo()
        service = ApplicationService(repo, RecordingCollector())
        stored = service.create("job-1")
        assert service.get_by_job("job-1")["id"] == stored["id"]
        assert service.get_by_job("missing") is None

    def test_update_status_and_applied_at(self):
        collector = RecordingCollector()
        service = ApplicationService(FakeApplicationRepo(), collector)
        stored = service.create("job-1")
        updated = service.update(stored["id"], {"status": ApplicationStatus.APPLIED, "applied_at": "2026-08-01"})
        assert updated["status"] == ApplicationStatus.APPLIED
        assert updated["applied_at"] == "2026-08-01"
        assert any(isinstance(e, ApplicationUpdated) and e.status == ApplicationStatus.APPLIED for e in collector.events)

    def test_update_clears_applied_at_with_none(self):
        service = ApplicationService(FakeApplicationRepo(), RecordingCollector())
        stored = service.create("job-1")
        service.update(stored["id"], {"applied_at": "2026-08-01"})
        updated = service.update(stored["id"], {"applied_at": None})
        assert updated["applied_at"] is None

    def test_update_missing_raises(self):
        service = ApplicationService(FakeApplicationRepo(), RecordingCollector())
        with pytest.raises(NotFoundError):
            service.update("nope", {"status": ApplicationStatus.APPLIED})

    def test_update_rejects_invalid_status(self):
        service = ApplicationService(FakeApplicationRepo(), RecordingCollector())
        stored = service.create("job-1")
        with pytest.raises(ValidationError):
            service.update(stored["id"], {"status": "nope"})


# --------------------------------------------------------------------------- #
# FollowUpService
# --------------------------------------------------------------------------- #


class TestFollowUpService:
    def _service(self):
        collector = RecordingCollector()
        apps = FakeApplicationRepo()
        apps.create({"job_id": "job-1", "status": ApplicationStatus.RECOMMENDED})
        return FollowUpService(FakeFollowUpRepo(), apps, collector), collector

    def test_add_emits_event(self):
        service, collector = self._service()
        fu = service.add("app-1", "2026-08-10", "Send a nudge")
        assert fu["note"] == "Send a nudge"
        assert fu["completed_at"] is None
        assert any(isinstance(e, ApplicationFollowUpAdded) and e.follow_up_id == fu["id"] for e in collector.events)

    def test_add_requires_existing_application(self):
        service, _ = self._service()
        with pytest.raises(NotFoundError):
            service.add("missing", "2026-08-10", "note")

    def test_complete_and_reopen(self):
        service, _ = self._service()
        fu = service.add("app-1", "2026-08-10", "nudge")
        completed = service.complete(fu["id"], completed=True)
        assert completed["completed_at"] is not None
        reopened = service.complete(fu["id"], completed=False)
        assert reopened["completed_at"] is None

    def test_update_note(self):
        service, _ = self._service()
        fu = service.add("app-1", None, "old")
        updated = service.update(fu["id"], note="new")
        assert updated["note"] == "new"

    def test_delete_emits_event(self):
        service, collector = self._service()
        fu = service.add("app-1", None, "note")
        service.delete(fu["id"])
        assert any(isinstance(e, ApplicationFollowUpDeleted) for e in collector.events)
        with pytest.raises(NotFoundError):
            service.delete(fu["id"])


# --------------------------------------------------------------------------- #
# DocumentService
# --------------------------------------------------------------------------- #


class TestDocumentService:
    def test_update_content_and_emit(self):
        collector = RecordingCollector()
        repo = FakeDocumentRepo()
        doc = repo.create({
            "application_id": "app-1",
            "document_type": DocumentType.COVER_LETTER,
            "version": 1,
            "content": "draft",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        })
        service = DocumentService(repo, collector)
        updated = service.update_content(doc["id"], "## Final")
        assert updated["content"] == "## Final"
        assert any(isinstance(e, ApplicationDocumentUpdated) and e.document_id == doc["id"] for e in collector.events)

    def test_update_rejects_empty_content(self):
        collector = RecordingCollector()
        repo = FakeDocumentRepo()
        doc = repo.create({
            "application_id": "app-1",
            "document_type": DocumentType.COVER_LETTER,
            "version": 1,
            "content": "draft",
        })
        service = DocumentService(repo, collector)
        with pytest.raises(ValidationError):
            service.update_content(doc["id"], "   ")

    def test_delete_emits_event(self):
        collector = RecordingCollector()
        repo = FakeDocumentRepo()
        doc = repo.create({
            "application_id": "app-1",
            "document_type": DocumentType.TAILORED_RESUME,
            "version": 1,
            "content": "draft",
        })
        service = DocumentService(repo, collector)
        service.delete(doc["id"])
        assert any(isinstance(e, ApplicationDocumentDeleted) for e in collector.events)


# --------------------------------------------------------------------------- #
# Domain events
# --------------------------------------------------------------------------- #


class TestDomainEvents:
    def test_events_are_immutable_domain_events(self):
        from shared.domain.domain_event import DomainEvent
        for cls in (
            ApplicationCreated,
            ApplicationUpdated,
            ApplicationFollowUpAdded,
            ApplicationFollowUpUpdated,
            ApplicationFollowUpDeleted,
            ApplicationPreparationGenerated,
            ApplicationDocumentGenerated,
            ApplicationDocumentUpdated,
            ApplicationDocumentDeleted,
        ):
            assert issubclass(cls, DomainEvent)

    def test_preparation_generated_event_fields(self):
        e = ApplicationPreparationGenerated(application_id="app-1", preparation_id="prep-1", version=3)
        assert e.application_id == "app-1"
        assert e.preparation_id == "prep-1"
        assert e.version == 3
        assert e.event_type == "application.preparation.generated"

    def test_document_generated_event_fields(self):
        e = ApplicationDocumentGenerated(
            application_id="app-1", document_id="doc-1",
            document_type=DocumentType.COVER_LETTER, version=2,
        )
        assert e.document_type == DocumentType.COVER_LETTER
        assert e.version == 2
        assert e.event_type == "application.document.generated"
