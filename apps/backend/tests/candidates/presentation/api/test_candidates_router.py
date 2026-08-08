"""API tests for the /api/candidates router."""

from unittest.mock import patch

from candidates.infrastructure import (
    SQLAlchemyCandidateProfileRepository,
    SQLAlchemyCandidateSourceRepository,
)


def _seed_profile(sa_session) -> str:
    profile_repo = SQLAlchemyCandidateProfileRepository(sa_session)
    profile = profile_repo.get_or_create_current()
    profile_repo.update_core(
        profile["id"],
        {"name": "Jane Doe", "title": "Backend Engineer", "headline": "Go + Python", "summary": "8y exp.", "location": "Berlin"},
    )
    profile_repo.replace_children(
        profile["id"],
        "skills",
        [{"name": "Python", "level": 4, "category": "language", "confidence": 0.96, "origin": "explicit", "evidence": {"sources": ["resume v1"]}}],
    )
    profile_repo.replace_children(
        profile["id"],
        "experiences",
        [{"company": "Acme", "role": "Backend Engineer", "start_date": "2021", "end_date": "2024", "summary": "Payments platform."}],
    )
    profile_repo.replace_children(
        profile["id"],
        "projects",
        [{"name": "CLI tool", "description": "A dev CLI.", "url": "https://example.com"}],
    )
    profile_repo.create_version(
        profile["id"],
        version=1,
        snapshot={"name": "Jane Doe", "skills": [{"name": "Python", "level": 4}]},
        source_versions={"resume": 1},
        change_summary="initial import",
    )
    source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
    source_repo.create(
        {"profile_id": profile["id"], "source_type": "resume", "version": 1, "status": "processed"}
    )
    return profile["id"]


class TestGetProfile:
    def test_no_profile_returns_404(self, client):
        response = client.get("/api/candidates/profile")
        assert response.status_code == 404

    def test_returns_current_profile(self, client, sa_session):
        _seed_profile(sa_session)
        response = client.get("/api/candidates/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["title"] == "Backend Engineer"
        assert data["version"] == 1
        assert data["skills"][0]["name"] == "Python"
        assert data["experiences"][0]["company"] == "Acme"
        assert data["projects"][0]["name"] == "CLI tool"


class TestGetSources:
    def test_empty_when_no_profile(self, client):
        response = client.get("/api/candidates/sources")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_lists_sources_newest_first(self, client, sa_session):
        profile_id = _seed_profile(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        source_repo.create({"profile_id": profile_id, "source_type": "linkedin", "version": 1, "status": "processed"})

        response = client.get("/api/candidates/sources")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 2
        assert items[0]["source_type"] == "linkedin"
        assert items[1]["source_type"] == "resume"


class TestGetVersions:
    def test_empty_when_no_profile(self, client):
        response = client.get("/api/candidates/versions")
        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_lists_versions_newest_first(self, client, sa_session):
        _seed_profile(sa_session)
        response = client.get("/api/candidates/versions")
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["version"] == 1
        assert items[0]["source_versions"] == {"resume": 1}


class TestUploadSource:
    def test_upload_resume_creates_pending_masked_source(self, client, sa_session):
        response = client.post(
            "/api/candidates/sources",
            json={"source_type": "resume", "raw_text": "Jane Doe\nSenior backend\nada@example.com"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source_type"] == "resume"
        assert data["version"] == 1
        assert data["status"] == "pending"
        assert data["id"]

        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        profile = SQLAlchemyCandidateProfileRepository(sa_session).get_current_profile()
        row = source_repo.get_by_type_and_version(profile["id"], "resume", 1)
        assert row is not None
        assert row["status"] == "pending"
        assert "[EMAIL]" in row["raw_text"]
        assert "[NAME]" in row["raw_text"]

    def test_upload_increments_version_per_type(self, client, sa_session):
        first = client.post("/api/candidates/sources", json={"source_type": "resume", "raw_text": "Resume one"})
        assert first.json()["version"] == 1
        second = client.post("/api/candidates/sources", json={"source_type": "resume", "raw_text": "Resume two"})
        assert second.json()["version"] == 2
        li = client.post("/api/candidates/sources", json={"source_type": "linkedin", "raw_text": "Profile one"})
        assert li.json()["version"] == 1

    def test_upload_rejects_unknown_source_type(self, client):
        response = client.post("/api/candidates/sources", json={"source_type": "github", "raw_text": "x"})
        assert response.status_code == 400

    def test_upload_rejects_empty_raw_text(self, client):
        response = client.post("/api/candidates/sources", json={"source_type": "resume", "raw_text": "  "})
        assert response.status_code == 400

    def test_upload_creates_profile_when_missing(self, client, sa_session):
        assert SQLAlchemyCandidateProfileRepository(sa_session).get_current_profile() is None
        response = client.post("/api/candidates/sources", json={"source_type": "resume", "raw_text": "New profile"})
        assert response.status_code == 201
        assert SQLAlchemyCandidateProfileRepository(sa_session).get_current_profile() is not None


class TestAnalyze:
    def test_dispatches_candidate_processing(self, client, sa_session):
        profile_id = _seed_profile(sa_session)
        source_repo = SQLAlchemyCandidateSourceRepository(sa_session)
        source_repo.create(
            {"profile_id": profile_id, "source_type": "resume", "version": 2, "status": "pending"}
        )
        with (
            patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
            patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
        ):
            response = client.post("/api/candidates/analyze")

        assert response.status_code == 202
        data = response.json()
        assert "execution_id" in data
        assert data["status"] == "queued"
        enqueue.assert_called_once_with(data["execution_id"])
        publish.assert_called_once()

    def test_noop_when_all_sources_processed(self, client, sa_session):
        _seed_profile(sa_session)
        with (
            patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
            patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
        ):
            response = client.post("/api/candidates/analyze")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "noop"
        assert data["reason"] == "no_new_sources"
        assert data["execution_id"] is None
        enqueue.assert_not_called()
        publish.assert_not_called()

    def test_noop_when_no_profile(self, client):
        with (
            patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
            patch("shared.infrastructure.events.processing_events.publish_sync") as publish,
        ):
            response = client.post("/api/candidates/analyze")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "noop"
        assert data["reason"] == "no_new_sources"
        enqueue.assert_not_called()
        publish.assert_not_called()
