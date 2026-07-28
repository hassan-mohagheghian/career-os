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
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert data["total"] == 0


def test_create_and_get_job(client, test_db):
    """Test creating and retrieving a job via ORM insert."""
    job = JobModel(
        num=1,
        url="https://example.com/job/1",
        title="Software Engineer",
        company="Tech Corp",
        location="Berlin",
        work_type="Remote",
        deleted=0,
        workflow_log="[]",
        locations='["Berlin"]',
        work_types='["Remote"]',
        employment_type="Full-time",
        rescoring=0,
    )
    test_db.add(job)
    test_db.commit()

    response = client.get("/api/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["num"] == 1
    assert data["url"] == "https://example.com/job/1"


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
