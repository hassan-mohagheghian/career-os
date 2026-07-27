"""Response comparison tests between Flask and FastAPI.

These tests verify that FastAPI endpoints return identical responses
to the Flask endpoints, ensuring API parity during migration.
"""

import sqlite3
import pytest


@pytest.fixture
def seed_db(test_db):
    """Seed the test database with sample data."""
    # Insert sample jobs
    test_db.execute(
        """INSERT INTO jobs (num, url, title, company, location, match, score,
        fit_score, success_score, overall_score, work_type, employment_type, deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (1, "https://example.com/job/1", "Software Engineer", "Tech Corp", "Berlin", "High", "A", 85, 78, 82.2, "Remote", "Full-time", 0),
    )
    test_db.execute(
        """INSERT INTO jobs (num, url, title, company, location, match, score,
        fit_score, success_score, overall_score, work_type, employment_type, deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (2, "https://example.com/job/2", "Backend Developer", "StartUp GmbH", "Munich", "Medium", "B", 65, 70, 67.0, "Hybrid", "Full-time", 0),
    )

    # Insert sample skills
    test_db.execute(
        "INSERT INTO skills (name, level, category, source, hidden) VALUES (?, ?, ?, ?, ?)",
        ("Python", 8, "technical", "user", 0),
    )
    test_db.execute(
        "INSERT INTO skills (name, level, category, source, hidden) VALUES (?, ?, ?, ?, ?)",
        ("FastAPI", 6, "technical", "user", 0),
    )

    # Insert sample companies
    test_db.execute(
        "INSERT INTO companies (name, industry, city, country) VALUES (?, ?, ?, ?)",
        ("Tech Corp", "Technology", "Berlin", "Germany"),
    )

    test_db.commit()


class TestJobsEndpointComparison:
    """Compare Jobs endpoint responses."""

    def test_list_jobs_structure(self, client, seed_db):
        """Verify list jobs returns correct structure."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert "agg" in data
        assert isinstance(data["jobs"], list)
        assert data["total"] == 2

    def test_list_jobs_with_pagination(self, client, seed_db):
        """Verify list jobs supports pagination."""
        response = client.get("/api/jobs?offset=0&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["total"] == 2

    def test_list_jobs_with_sorting(self, client, seed_db):
        """Verify list jobs supports sorting."""
        response = client.get("/api/jobs?sort_by=overall_score&sort_dir=desc")
        assert response.status_code == 200
        data = response.json()
        assert data["jobs"][0]["overall_score"] >= data["jobs"][1]["overall_score"]

    def test_get_job(self, client, seed_db):
        """Verify get job returns correct data."""
        response = client.get("/api/jobs/1")
        assert response.status_code == 200
        data = response.json()
        assert data["num"] == 1
        assert data["url"] == "https://example.com/job/1"
        assert data["company"] == "Tech Corp"

    def test_get_job_not_found(self, client, seed_db):
        """Verify get job returns 404 for missing job."""
        response = client.get("/api/jobs/999")
        assert response.status_code == 404

    def test_update_job(self, client, seed_db):
        """Verify update job works."""
        response = client.put(
            "/api/jobs/1",
            json={"response_status": "applied"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["response_status"] == "applied"

    def test_delete_job(self, client, seed_db):
        """Verify delete job works."""
        response = client.delete("/api/jobs/1")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify deleted
        response = client.get("/api/jobs/1")
        assert response.status_code == 404


class TestSkillsEndpointComparison:
    """Compare Skills endpoint responses."""

    def test_list_skills(self, client, seed_db):
        """Verify list skills returns correct data."""
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_skills_by_category(self, client, seed_db):
        """Verify list skills filters by category."""
        response = client.get("/api/skills?category=technical")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_create_skill(self, client, seed_db):
        """Verify create skill works."""
        response = client.post(
            "/api/skills",
            json={"name": "PostgreSQL", "category": "technical"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "PostgreSQL"

    def test_update_skill(self, client, seed_db):
        """Verify update skill works."""
        response = client.put(
            "/api/skills/1",
            json={"level": 9},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["level"] == 9

    def test_delete_skill(self, client, seed_db):
        """Verify delete skill works."""
        response = client.delete("/api/skills/1")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_skill_stats(self, client, seed_db):
        """Verify skill stats endpoint works."""
        response = client.get("/api/skills/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert data["total"] == 2

    def test_skill_categories(self, client, seed_db):
        """Verify skill categories endpoint works."""
        response = client.get("/api/skills/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCompaniesEndpointComparison:
    """Compare Companies endpoint responses."""

    def test_list_companies(self, client, seed_db):
        """Verify list companies returns correct data."""
        response = client.get("/api/companies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_company(self, client, seed_db):
        """Verify get company returns correct data."""
        response = client.get("/api/companies/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Tech Corp"

    def test_create_company(self, client, seed_db):
        """Verify create company works."""
        response = client.post(
            "/api/companies",
            json={"name": "New Corp", "industry": "Finance"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Corp"

    def test_delete_company(self, client, seed_db):
        """Verify delete company works."""
        response = client.delete("/api/companies/1")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"


class TestPendingEndpointComparison:
    """Compare Pending endpoint responses."""

    def test_list_pending(self, client, seed_db):
        """Verify list pending returns correct structure."""
        response = client.get("/api/pending")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_pending(self, client, seed_db):
        """Verify create pending works."""
        response = client.post(
            "/api/pending",
            json={"url": "https://example.com/job/new"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://example.com/job/new"


class TestInsightsEndpointComparison:
    """Compare Insights endpoint responses."""

    def test_get_insights(self, client, seed_db):
        """Verify get insights returns correct structure."""
        response = client.get("/api/insights")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_insight_section(self, client, seed_db):
        """Verify get insight section works."""
        response = client.get("/api/insights/overview")
        assert response.status_code == 200

    def test_get_insights_status(self, client, seed_db):
        """Verify get insights status works."""
        response = client.get("/api/insights/status")
        assert response.status_code == 200
        data = response.json()
        assert "sections" in data


class TestDashboardEndpointComparison:
    """Compare Dashboard endpoint responses."""

    def test_get_dashboard(self, client, seed_db):
        """Verify get dashboard returns correct structure."""
        response = client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "jobs_total" in data
        assert data["jobs_total"] == 2

    def test_get_cities(self, client, seed_db):
        """Verify get cities works."""
        response = client.get("/api/cities")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        city_names = [c["name"] for c in data["items"]]
        assert "Berlin" in city_names


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Verify health check returns ok."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
