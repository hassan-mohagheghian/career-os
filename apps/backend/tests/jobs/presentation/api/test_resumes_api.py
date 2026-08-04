"""Tests for /api/resumes and /api/linkedin upload/list/delete flows."""

from shared.infrastructure.database.models.misc_models import ResumeModel


class TestResumeUpload:
    def test_upload_resume_creates_versioned_row(self, client, test_db):
        response = client.post("/api/resumes", json={"raw_text": "Jane Doe\nPython engineer"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["version"] == 1
        assert data["id"] == "original_1"

        row = test_db.query(ResumeModel).filter(ResumeModel.id == "original_1").first()
        assert row is not None
        assert row.version == 1
        assert "[NAME]" in row.raw_text
        assert "<p " in row.content

    def test_upload_resume_increments_version(self, client):
        first = client.post("/api/resumes", json={"raw_text": "First resume"})
        assert first.json()["version"] == 1
        second = client.post("/api/resumes", json={"raw_text": "Second resume"})
        assert second.json()["version"] == 2
        assert second.json()["id"] == "original_2"

    def test_upload_resume_masks_pii(self, client, test_db):
        response = client.post(
            "/api/resumes",
            json={"raw_text": "Senior backend engineer with extensive experience\nada@example.com\n+49 123 456 7890"},
        )
        assert response.status_code == 200
        row = test_db.query(ResumeModel).filter(ResumeModel.id == "original_1").first()
        assert "[EMAIL]" in row.raw_text
        assert "[PHONE]" in row.raw_text

    def test_upload_resume_supports_legacy_content_key(self, client):
        response = client.post("/api/resumes", json={"content": "Legacy upload"})
        assert response.status_code == 200
        assert response.json()["id"] == "original_1"


class TestResumeDelete:
    def test_delete_resume_by_id(self, client, test_db):
        client.post("/api/resumes", json={"raw_text": "Resume to delete"})
        response = client.delete("/api/resumes/original_1")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"
        assert test_db.query(ResumeModel).filter(ResumeModel.id == "original_1").count() == 0

    def test_delete_missing_resume_returns_404(self, client):
        response = client.delete("/api/resumes/original_999")
        assert response.status_code == 404


class TestLinkedinUpload:
    def test_upload_linkedin_creates_versioned_row(self, client, test_db):
        response = client.post("/api/linkedin", json={"raw_text": "John Doe\nSenior Backend"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["version"] == 1
        assert data["id"] == "linkedin_1"

        row = test_db.query(ResumeModel).filter(ResumeModel.id == "linkedin_1").first()
        assert row is not None
        assert row.version == 1

    def test_upload_linkedin_increments_version(self, client):
        client.post("/api/linkedin", json={"raw_text": "Profile one"})
        second = client.post("/api/linkedin", json={"raw_text": "Profile two"})
        assert second.json()["version"] == 2
        assert second.json()["id"] == "linkedin_2"

    def test_list_linkedin_newest_first(self, client):
        client.post("/api/linkedin", json={"raw_text": "Profile one"})
        client.post("/api/linkedin", json={"raw_text": "Profile two"})
        response = client.get("/api/linkedin")
        assert response.status_code == 200
        ids = [r["id"] for r in response.json()]
        assert ids == ["linkedin_2", "linkedin_1"]

    def test_delete_linkedin_by_id(self, client, test_db):
        client.post("/api/linkedin", json={"raw_text": "Profile to delete"})
        response = client.delete("/api/linkedin/linkedin_1")
        assert response.status_code == 200
        assert test_db.query(ResumeModel).filter(ResumeModel.id == "linkedin_1").count() == 0

    def test_delete_missing_linkedin_returns_404(self, client):
        response = client.delete("/api/linkedin/linkedin_999")
        assert response.status_code == 404


class TestScoringLatestSelection:
    def test_get_latest_linkedin_uses_version(self, client, test_db):
        client.post("/api/linkedin", json={"raw_text": "Profile one text that is definitely long enough to avoid masking"})
        client.post("/api/linkedin", json={"raw_text": "Profile two text that is definitely long enough to avoid masking"})
        rows = test_db.query(ResumeModel).filter(
            ResumeModel.id.like("linkedin_%")
        ).order_by(ResumeModel.version.desc()).all()
        assert rows[0].version == 2
        assert rows[0].raw_text == "Profile two text that is definitely long enough to avoid masking"
