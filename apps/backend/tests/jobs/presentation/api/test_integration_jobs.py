"""Tests for Job API endpoints."""

import pytest

from jobs.infrastructure.models.job_model import JobModel


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_jobs_empty(client):
    """Test listing jobs when database is empty."""
    response = client.get("/api/jobs/list")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert data["pagination"]["total_items"] == 0


def test_create_and_get_job(client, test_db):
    """Test creating and retrieving a job via ORM insert."""
    job = JobModel(
        url="https://example.com/job/1",
        title="Software Engineer",
        company="Tech Corp",
        location="Berlin",
        deleted=0,
        workflow_log="[]",
        locations='["Berlin"]',
        work_types='["Remote"]',
        employment_types='["Full-time"]',
        rescoring=0,
    )
    test_db.add(job)
    test_db.commit()

    response = client.get("/api/jobs/list?query=Software&page_size=25")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total_items"] == 1
    item = data["items"][0]
    assert item["id"] == job.id
    assert item["title"] == "Software Engineer"
    assert item["company_name"] == "Tech Corp"


def test_list_skills_empty(client):
    """Test listing skills when database is empty."""
    response = client.get("/api/skills")
    assert response.status_code == 200


def test_create_skill(client):
    """Test creating a skill."""
    response = client.post(
        "/api/skills",
        json={"name": "Python", "category": "technical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Python"


def test_list_companies_empty(client):
    """Test listing companies when database is empty."""
    response = client.get("/api/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_job_detail(client, test_db):
    """Test fetching a single job via the V2 detail endpoint."""
    job = JobModel(
        url="https://example.com/job/42",
        title="Backend Engineer",
        company="Example Co",
        location="London",
        deleted=0,
        workflow_log="[]",
        locations='["London"]',
        work_types='["On-site"]',
        employment_types='["Full-time"]',
        rescoring=0,
    )
    test_db.add(job)
    test_db.commit()

    response = client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job.id
    assert data["title"] == "Backend Engineer"
    assert data["company_name"] == "Example Co"
    assert data["location"] == "London"
    assert data["scores"]["overall"] is None

    missing = client.get("/api/jobs/does-not-exist")
    assert missing.status_code == 404


def test_get_job_detail_includes_company_id(client, test_db):
    """Test the V2 detail endpoint exposes the linked company_id."""
    job = JobModel(
        url="https://example.com/job/43",
        title="Frontend Engineer",
        company="Example Co",
        company_id="company-abc",
        location="Berlin",
        deleted=0,
        workflow_log="[]",
        locations='["Berlin"]',
        work_types='["On-site"]',
        employment_types='["Full-time"]',
        rescoring=0,
    )
    test_db.add(job)
    test_db.commit()

    response = client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Example Co"
    assert data["company_id"] == "company-abc"
