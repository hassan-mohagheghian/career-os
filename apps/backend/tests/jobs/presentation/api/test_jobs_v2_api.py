"""Tests for the new Jobs V2 API (GET /api/jobs/list)."""

import pytest
from jobs.infrastructure.models.job_model import JobModel


def _create_job(test_db, **kwargs) -> JobModel:
    defaults = dict(
        id=None,
        url="https://example.com/job",
        title="Software Engineer",
        company="Tech Corp",
        location="Berlin",
        work_type="Remote",
        visa="Yes",
        status="imported",
        deleted=0,
        workflow_log="[]",
        locations="[]",
        work_types="[]",
        employment_type="Full-time",
        rescoring=0,
        overall_score=85,
        fit_score=80,
        success_score=90,
    )
    defaults.update(kwargs)
    if defaults["id"] is None:
        import uuid
        defaults["id"] = str(uuid.uuid7())
    job = JobModel(**defaults)
    test_db.add(job)
    test_db.commit()
    return job


class TestJobListV2API:
    def test_list_empty(self, client):
        resp = client.get("/api/jobs/list")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["pagination"]["total_items"] == 0
        assert data["pagination"]["page"] == 1

    def test_list_with_jobs(self, client, test_db):
        _create_job(test_db, id=1, title="Engineer One", company="Alpha Corp")
        _create_job(test_db, id=2, title="Engineer Two", company="Beta Inc")

        resp = client.get("/api/jobs/list")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["pagination"]["total_items"] == 2

    def test_pagination(self, client, test_db):
        for i in range(5):
            _create_job(test_db, id=i + 1, title=f"Job {i}")

        resp = client.get("/api/jobs/list?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["pagination"]["total_items"] == 5
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2
        assert data["pagination"]["total_pages"] == 3

        resp2 = client.get("/api/jobs/list?page=3&page_size=2")
        data2 = resp2.json()
        assert len(data2["items"]) == 1

    def test_search_by_title(self, client, test_db):
        _create_job(test_db, id=1, title="Senior Backend Engineer")
        _create_job(test_db, id=2, title="Junior Frontend Developer")
        _create_job(test_db, id=3, title="DevOps Engineer")

        resp = client.get("/api/jobs/list?query=Backend")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Senior Backend Engineer"

    def test_search_by_company(self, client, test_db):
        _create_job(test_db, id=1, title="Engineer", company="Google")
        _create_job(test_db, id=2, title="Engineer", company="Meta")

        resp = client.get("/api/jobs/list?query=Google")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["company_name"] == "Google"

    def test_search_by_location(self, client, test_db):
        _create_job(test_db, id=1, title="Engineer", location="Berlin")
        _create_job(test_db, id=2, title="Engineer", location="Munich")

        resp = client.get("/api/jobs/list?query=Berlin")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["location"] == "Berlin"

    def test_sort_by_created_at(self, client, test_db):
        _create_job(test_db, id=1, title="A")
        _create_job(test_db, id=2, title="B")

        resp = client.get("/api/jobs/list?sort=created_at&order=asc")
        data = resp.json()
        assert len(data["items"]) == 2
        assert isinstance(data["items"][0]["id"], str) and len(data["items"][0]["id"]) > 0
        assert data["items"][0]["title"] == "A"

        resp = client.get("/api/jobs/list?sort=created_at&order=desc")
        data = resp.json()
        assert data["items"][0]["title"] == "B"

    def test_sort_by_score(self, client, test_db):
        _create_job(test_db, id=1, title="Low", overall_score=50)
        _create_job(test_db, id=2, title="High", overall_score=99)

        resp = client.get("/api/jobs/list?sort=overall_score&order=desc")
        data = resp.json()
        assert data["items"][0]["scores"]["overall"] == 99

    def test_filter_by_processing_status(self, client, test_db):
        _create_job(test_db, id=1, title="Queued", status="queued")
        _create_job(test_db, id=2, title="Completed", status="completed")
        _create_job(test_db, id=3, title="Imported", status="imported")

        resp = client.get("/api/jobs/list?processing_status=queued")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Queued"

    def test_filter_by_remote(self, client, test_db):
        _create_job(test_db, id=1, title="Remote", work_type="Remote")
        _create_job(test_db, id=2, title="Onsite", work_type="On-site")

        resp = client.get("/api/jobs/list?remote=true")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["remote"] is True

        resp = client.get("/api/jobs/list?remote=false")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["remote"] is False

    def test_filter_by_visa(self, client, test_db):
        _create_job(test_db, id=1, title="Has Visa", visa="Yes")
        _create_job(test_db, id=2, title="No Visa", visa="")

        resp = client.get("/api/jobs/list?visa=true")
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["visa_sponsorship"] is True

    def test_filter_by_score_range(self, client, test_db):
        _create_job(test_db, id=1, title="Low", overall_score=30)
        _create_job(test_db, id=2, title="Mid", overall_score=60)
        _create_job(test_db, id=3, title="High", overall_score=95)

        resp = client.get("/api/jobs/list?overall_score_min=50&overall_score_max=100")
        data = resp.json()
        assert len(data["items"]) == 2

    def test_response_shape(self, client, test_db):
        _create_job(
            test_db, id=1, title="Engineer", company="Corp", location="Berlin",
            work_type="Remote", visa="Yes", overall_score=85, fit_score=80,
            success_score=90, status="completed",
        )

        resp = client.get("/api/jobs/list")
        data = resp.json()
        item = data["items"][0]

        assert isinstance(item["id"], str) and len(item["id"]) > 0
        assert item["title"] == "Engineer"
        assert item["company_name"] == "Corp"
        assert item["location"] == "Berlin"
        assert item["remote"] is True
        assert item["visa_sponsorship"] is True
        assert item["job_status"] == "completed"
        assert item["scores"]["overall"] == 85
        assert item["scores"]["fit"] == 80
        assert item["scores"]["success"] == 90
        assert item["latest_processing_execution"] is not None
        assert item["latest_processing_execution"]["status"] == "completed"
        assert "updated_at" in item
        assert "created_at" in item

    def test_invalid_page_returns_422(self, client):
        resp = client.get("/api/jobs/list?page=0")
        assert resp.status_code == 422

    def test_invalid_page_size_returns_422(self, client):
        resp = client.get("/api/jobs/list?page_size=0")
        assert resp.status_code == 422

    def test_page_size_greater_than_max_returns_422(self, client):
        resp = client.get("/api/jobs/list?page_size=200")
        assert resp.status_code == 422

    def test_sort_fallback(self, client, test_db):
        _create_job(test_db, id=1, title="A")
        _create_job(test_db, id=2, title="B")

        resp = client.get("/api/jobs/list?sort=invalid_field")
        assert resp.status_code == 200
        # Should fall back to updated_at desc and not error

    def test_not_found_filters_return_empty(self, client, test_db):
        _create_job(test_db, id=1, title="Engineer")

        resp = client.get("/api/jobs/list?company_id=999")
        data = resp.json()
        assert len(data["items"]) == 0
