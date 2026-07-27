"""Tests for Job API endpoints."""

import pytest


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
    """Test creating and retrieving a job via direct DB insert (matching Flask behavior)."""
    # Jobs are created through the pending queue, not directly via API
    # Insert a job directly for testing
    test_db.execute(
        "INSERT INTO jobs (num, url, title, company, location) VALUES (?, ?, ?, ?, ?)",
        (1, "https://example.com/job/1", "Software Engineer", "Tech Corp", "Berlin"),
    )
    test_db.commit()

    # Get the job
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
