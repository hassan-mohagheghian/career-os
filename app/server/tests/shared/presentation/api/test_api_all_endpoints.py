"""Comprehensive API endpoint tests for all routes."""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model
import processing.infrastructure.models.pending_model
import career.infrastructure.models.insight_model
import shared.infrastructure.database.models.misc_models


# ── Shared infrastructure (created ONCE for all tests) ─────────────

_engine = create_engine(
    "sqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=_engine)
_SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)

_DELETE_ORDER = list(reversed(Base.metadata.sorted_tables))


def _clear_tables():
    with _engine.connect() as conn:
        for tbl in _DELETE_ORDER:
            conn.execute(tbl.delete())
        conn.commit()


def _make_app():
    from dependencies import get_session
    from exceptions import AppError
    from shared.presentation.api.root_router import api_router

    app = FastAPI(title="Test")

    @app.exception_handler(AppError)
    async def app_error_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.detail, "details": getattr(exc, "details", None)}},
        )

    app.include_router(api_router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    return app


_app = _make_app()
_client = TestClient(_app)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def sa_session():
    _clear_tables()
    session = _SessionFactory()
    yield session
    session.close()


@pytest.fixture
def client(sa_session):
    from dependencies import get_session, get_session_sync

    def _override_get_session():
        yield sa_session

    def _override_get_session_sync():
        return sa_session

    saved_overrides = dict(_app.dependency_overrides)

    _app.dependency_overrides[get_session] = _override_get_session
    _app.dependency_overrides[get_session_sync] = _override_get_session_sync

    with patch("dependencies.get_session_sync", return_value=sa_session), \
         patch("shared.presentation.api.root_router.get_session_sync", return_value=sa_session):
        yield _client

    _app.dependency_overrides.clear()
    _app.dependency_overrides.update(saved_overrides)


@pytest.fixture
async def async_client(sa_session):
    from dependencies import get_session, get_session_sync

    def _override_get_session():
        yield sa_session

    def _override_get_session_sync():
        return sa_session

    _app.dependency_overrides[get_session] = _override_get_session
    _app.dependency_overrides[get_session_sync] = _override_get_session_sync

    with patch("dependencies.get_session_sync", return_value=sa_session), \
         patch("shared.presentation.api.root_router.get_session_sync", return_value=sa_session):
        transport = ASGITransport(app=_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    _app.dependency_overrides.pop(get_session, None)
    _app.dependency_overrides.pop(get_session_sync, None)


# ── Health ────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── Jobs ──────────────────────────────────────────────────────────

class TestJobsEndpoints:
    def test_list_jobs_empty(self, client):
        r = client.get("/api/jobs")
        assert r.status_code == 200
        data = r.json()
        assert data["jobs"] == []
        assert data["total"] == 0

    def test_list_jobs_with_data(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, company="Google", role="Engineer", url="https://example.com/1", match="High", score="A"))
        sa_session.add(JobModel(num=2, company="Meta", role="Dev", url="https://example.com/2", match="Medium", score="B"))
        sa_session.commit()
        r = client.get("/api/jobs")
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_list_jobs_pagination(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        for i in range(5):
            sa_session.add(JobModel(num=i+1, url=f"https://ex.com/{i}", company=f"Co{i}"))
        sa_session.commit()
        r = client.get("/api/jobs?offset=0&limit=2")
        assert r.status_code == 200
        assert len(r.json()["jobs"]) == 2
        assert r.json()["total"] == 5

    def test_list_jobs_filter_cities(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", location="Berlin", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", location="Munich", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_cities=Berlin")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_companies(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="Google"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", company="Meta"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_companies=Google")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_tech(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", stack="Python", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", stack="Java", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_tech=Python")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_matches(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", match="High", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", match="Low", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_matches=High")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_work_types(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", work_type="Remote", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", work_type="On-site", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_work_types=Remote")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_employment_types(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", employment_type="Full-time", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", employment_type="Part-time", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_employment_types=Full-time")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_response_status(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", response_status="applied", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", response_status="pending", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_response_status=applied")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_applied(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", apply_time="2024-01-01", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_applied=true")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_filter_scores(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", score="A", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", score="B", company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?filter_scores=A")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_list_jobs_sort_by(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", overall_score=50, company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", overall_score=90, company="B"))
        sa_session.commit()
        r = client.get("/api/jobs?sort_by=overall_score&sort_dir=desc")
        assert r.status_code == 200
        assert r.json()["jobs"][0]["overall_score"] == 90

    def test_list_jobs_deleted_excluded(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", deleted=1, company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", deleted=0, company="B"))
        sa_session.commit()
        r = client.get("/api/jobs")
        assert r.json()["total"] == 1

    def test_get_job(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="Google", role="Engineer"))
        sa_session.commit()
        r = client.get("/api/jobs/1")
        assert r.status_code == 200
        assert r.json()["num"] == 1

    def test_get_job_not_found(self, client):
        r = client.get("/api/jobs/999")
        assert r.status_code == 404

    def test_update_job(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        r = client.put("/api/jobs/1", json={"notes": "test note"})
        assert r.status_code == 200
        assert r.json()["notes"] == "test note"

    def test_update_job_not_found(self, client):
        r = client.put("/api/jobs/999", json={"notes": "test"})
        assert r.status_code == 404

    def test_delete_job(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        r = client.delete("/api/jobs/1")
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    def test_get_summaries(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SummaryModel
        sa_session.add(SummaryModel(num=1, company="Google", score="A", summary="Good"))
        sa_session.commit()
        r = client.get("/api/jobs/summaries")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_job_generation_history(self, client, sa_session):
        r = client.get("/api/jobs/1/generation-history")
        assert r.status_code == 200
        assert r.json() == []

    def test_rescore_job(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.get_by_url.return_value = None
        mock_pending.create.return_value = {"id": "p1", "url": "https://ex.com/1"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/1/rescore")
            assert r.status_code == 200
            assert r.json()["status"] == "queued"

    def test_rescore_job_not_found(self, client):
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/999/rescore")
            assert r.status_code == 404

    def test_rescore_job_existing_pending(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.get_by_url.return_value = {"id": "p1", "url": "https://ex.com/1", "status": "done"}
        mock_pending.create.return_value = {"id": "p2", "url": "https://ex.com/1"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/1/rescore")
            assert r.status_code == 200

    def test_rescore_all(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", company="B"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.create.return_value = {"id": "p1"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/rescore-all")
            assert r.status_code == 200
            assert r.json()["count"] == 2

    def test_rescore_all_empty(self, client):
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/rescore-all")
            assert r.status_code == 200
            assert r.json()["count"] == 0

    def test_reprocess_all(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.create.return_value = {"id": "p1"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/reprocess-all")
            assert r.status_code == 200
            assert r.json()["status"] == "reprocessing"

    def test_reprocess_all_with_existing_pending(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.add(PendingJobModel(url="https://ex.com/1", status="done"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.get_by_url.return_value = {"id": "p1", "url": "https://ex.com/1", "status": "done"}
        mock_pending.create.return_value = {"id": "p2"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/reprocess-all")
            assert r.status_code == 200

    def test_requeue_job(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.get_by_url.return_value = None
        mock_pending.create.return_value = {"id": "p1"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/1/requeue")
            assert r.status_code == 200
            assert r.json()["status"] == "queued"

    def test_requeue_job_not_found(self, client):
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/999/requeue")
            assert r.status_code == 404

    def test_requeue_job_existing_pending(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from dependencies import get_pending_repo
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        mock_pending = MagicMock()
        mock_pending.get_by_url.return_value = {"id": "p1", "url": "https://ex.com/1", "status": "done"}
        mock_pending.create.return_value = {"id": "p2"}
        client.app.dependency_overrides[get_pending_repo] = lambda: mock_pending
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/jobs/1/requeue")
            assert r.status_code == 200

    def test_generate_resume(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        with patch("dependencies.get_session_sync", return_value=sa_session), \
             patch("threading.Thread"):
            r = client.post("/api/jobs/1/generate-resume")
            assert r.status_code == 200
            assert r.json()["status"] == "queued"

    def test_generate_resume_not_found(self, client):
        r = client.post("/api/jobs/999/generate-resume")
        assert r.status_code == 404

    def test_generate_resume_already_running(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.add(PendingGenerationModel(job_num=1, type="resume", status="processing"))
        sa_session.commit()
        with patch("dependencies.get_session_sync", return_value=sa_session):
            r = client.post("/api/jobs/1/generate-resume")
            assert r.status_code == 400

    def test_generate_cover(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        with patch("dependencies.get_session_sync", return_value=sa_session), \
             patch("threading.Thread"):
            r = client.post("/api/jobs/1/generate-cover")
            assert r.status_code == 200
            assert r.json()["status"] == "queued"

    def test_generate_cover_not_found(self, client):
        r = client.post("/api/jobs/999/generate-cover")
        assert r.status_code == 404

    def test_generate_cover_already_running(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.add(PendingGenerationModel(job_num=1, type="cover", status="processing"))
        sa_session.commit()
        with patch("dependencies.get_session_sync", return_value=sa_session):
            r = client.post("/api/jobs/1/generate-cover")
            assert r.status_code == 400


# ── Skills ────────────────────────────────────────────────────────

class TestSkillsEndpoints:
    def test_list_skills_empty(self, client):
        r = client.get("/api/skills")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_skills_with_data(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8, source="user"))
        sa_session.add(SkillModel(name="Java", level=5, source="user"))
        sa_session.commit()
        r = client.get("/api/skills")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_list_skills_hidden_excluded(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8, hidden=0))
        sa_session.add(SkillModel(name="Java", level=5, hidden=1))
        sa_session.commit()
        r = client.get("/api/skills")
        assert len(r.json()) == 1

    def test_list_skills_by_category(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8, category="technical"))
        sa_session.add(SkillModel(name="Leadership", level=5, category="professional"))
        sa_session.commit()
        r = client.get("/api/skills?category=technical")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_list_hidden_skills(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="OldSkill", level=3, hidden=1))
        sa_session.commit()
        r = client.get("/api/skills/hidden")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_categories(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8, category="technical"))
        sa_session.add(SkillModel(name="Java", level=5, category="technical"))
        sa_session.commit()
        r = client.get("/api/skills/categories")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["count"] == 2

    def test_get_stats(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8, source="user", market_relevance=9.0))
        sa_session.commit()
        r = client.get("/api/skills/stats")
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_create_skill(self, client):
        r = client.post("/api/skills", json={"name": "Rust", "level": 5})
        assert r.status_code == 200

    def test_create_skill_already_exists(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8))
        sa_session.commit()
        r = client.post("/api/skills", json={"name": "Python", "level": 5})
        assert r.status_code == 200
        assert "already exists" in r.json().get("message", "")

    def test_update_skill(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.put(f"/api/skills/{skill_id}", json={"level": 10})
        assert r.status_code == 200
        assert r.json()["level"] == 10

    def test_update_skill_not_found(self, client):
        r = client.put("/api/skills/999", json={"level": 10})
        assert r.status_code == 404

    def test_update_skill_empty(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.put(f"/api/skills/{skill_id}", json={})
        assert r.status_code == 400

    def test_rename_skill(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", level=8))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.patch(f"/api/skills/{skill_id}/rename", json={"name": "Python3"})
        assert r.status_code == 200
        assert r.json()["name"] == "Python3"

    def test_rename_skill_not_found(self, client):
        r = client.patch("/api/skills/999/rename", json={"name": "New"})
        assert r.status_code == 404

    def test_rename_skill_conflict(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.add(SkillModel(name="Java"))
        sa_session.commit()
        java_id = sa_session.query(SkillModel).filter(SkillModel.name == "Java").first().id
        r = client.patch(f"/api/skills/{java_id}/rename", json={"name": "Python"})
        assert r.status_code == 409

    def test_delete_skill(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.delete(f"/api/skills/{skill_id}")
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    def test_delete_skill_not_found(self, client):
        r = client.delete("/api/skills/999")
        assert r.status_code == 404

    def test_hide_skill(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.patch(f"/api/skills/{skill_id}/hide", json={"hidden": 1})
        assert r.status_code == 200

    def test_hide_skill_not_found(self, client):
        r = client.patch("/api/skills/999/hide", json={"hidden": 1})
        assert r.status_code == 404

    def test_restore_skill(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", hidden=1))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.patch(f"/api/skills/{skill_id}/restore")
        assert r.status_code == 200
        assert r.json()["hidden"] == 0

    def test_restore_skill_not_found(self, client):
        r = client.patch("/api/skills/999/restore")
        assert r.status_code == 404

    def test_merge_skills(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.add(SkillModel(name="Python3"))
        sa_session.commit()
        target_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        source_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python3").first().id
        r = client.post("/api/skills/merge", json={"target_id": target_id, "source_ids": [source_id]})
        assert r.status_code == 200
        assert r.json()["status"] == "merged"

    def test_merge_skills_target_not_found(self, client):
        r = client.post("/api/skills/merge", json={"target_id": 999, "source_ids": []})
        assert r.status_code == 404

    def test_get_skill_relationships(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        sa_session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        sa_session.commit()
        r = client.get("/api/skills/skill-relationships/Python")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_create_skill_relationship(self, client):
        r = client.post("/api/skills/skill-relationships", json={"skill_name": "Python", "related_name": "Django", "relation_type": "related"})
        assert r.status_code == 200
        assert r.json()["status"] == "created"

    def test_delete_skill_relationship(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        sa_session.add(SkillRelationshipModel(skill_name="Python", related_name="Django", relation_type="related"))
        sa_session.commit()
        rel_id = sa_session.query(SkillRelationshipModel).first().id
        r = client.delete(f"/api/skills/skill-relationships/{rel_id}")
        assert r.status_code == 200

    def test_bulk_hide(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.add(SkillModel(name="Java"))
        sa_session.commit()
        ids = [s.id for s in sa_session.query(SkillModel).all()]
        r = client.post("/api/skills/bulk-hide", json={"ids": ids})
        assert r.status_code == 200
        assert r.json()["count"] == 2

    def test_bulk_hide_empty(self, client):
        r = client.post("/api/skills/bulk-hide", json={"ids": []})
        assert r.status_code == 400

    def test_bulk_categorize(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.commit()
        ids = [s.id for s in sa_session.query(SkillModel).all()]
        r = client.post("/api/skills/bulk-categorize", json={"ids": ids, "category": "technical"})
        assert r.status_code == 200
        assert r.json()["count"] == 1

    def test_bulk_categorize_invalid(self, client):
        r = client.post("/api/skills/bulk-categorize", json={"ids": [1], "category": "invalid"})
        assert r.status_code == 400

    def test_update_category(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.put(f"/api/skills/{skill_id}/category", json={"category": "technical"})
        assert r.status_code == 200
        assert r.json()["category"] == "technical"

    def test_update_category_invalid(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python"))
        sa_session.commit()
        skill_id = sa_session.query(SkillModel).filter(SkillModel.name == "Python").first().id
        r = client.put(f"/api/skills/{skill_id}/category", json={"category": "bad"})
        assert r.status_code == 400

    def test_update_category_not_found(self, client):
        r = client.put("/api/skills/999/category", json={"category": "technical"})
        assert r.status_code == 404


# ── Companies ─────────────────────────────────────────────────────

class TestCompaniesEndpoints:
    def test_list_companies_empty(self, client):
        r = client.get("/api/companies")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_companies(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        sa_session.add(CompanyModel(name="Google"))
        sa_session.commit()
        r = client.get("/api/companies")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_list_companies_with_intelligence(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyIntelligenceModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(CompanyIntelligenceModel(company_id=co.id, scores='{"culture": 9}'))
        sa_session.commit()
        r = client.get("/api/companies")
        assert r.status_code == 200
        assert r.json()[0]["scores"]["culture"] == 9

    def test_list_companies_intelligence_bad_json(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyIntelligenceModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(CompanyIntelligenceModel(company_id=co.id, scores='not-json'))
        sa_session.commit()
        r = client.get("/api/companies")
        assert r.status_code == 200

    def test_get_company(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}")
        assert r.status_code == 200
        assert r.json()["name"] == "Google"

    def test_get_company_with_intelligence(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyIntelligenceModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(CompanyIntelligenceModel(company_id=co.id, overview="Great"))
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}")
        assert r.status_code == 200
        assert r.json()["intelligence"]["overview"] == "Great"

    def test_get_company_not_found(self, client):
        r = client.get("/api/companies/999")
        assert r.status_code == 404

    def test_create_company(self, client):
        r = client.post("/api/companies", json={"name": "Google", "industry": "Tech"})
        assert r.status_code == 200
        assert r.json()["name"] == "Google"

    def test_update_company(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        r = client.put(f"/api/companies/{co.id}", json={"industry": "Tech"})
        assert r.status_code == 200
        assert r.json()["industry"] == "Tech"

    def test_update_company_not_found(self, client):
        r = client.put("/api/companies/999", json={"name": "X"})
        assert r.status_code == 404

    def test_delete_company(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        r = client.delete(f"/api/companies/{co.id}")
        assert r.status_code == 200

    def test_get_company_intelligence(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyIntelligenceModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(CompanyIntelligenceModel(company_id=co.id, overview="Great"))
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}/intelligence")
        assert r.status_code == 200
        assert r.json()["overview"] == "Great"

    def test_get_company_intelligence_none(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}/intelligence")
        assert r.status_code == 200
        assert r.json()["overview"] is None

    def test_get_company_jobs(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        from shared.infrastructure.database.models.job_model import JobModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company_id=co.id))
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}/jobs")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_company_links(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyLinkModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(CompanyLinkModel(company_id=co.id, url="https://google.com", title="Main"))
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}/links")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_add_company_link(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        r = client.post(f"/api/companies/{co.id}/links", json={"url": "https://google.com", "title": "Main"})
        assert r.status_code == 200

    def test_delete_company_link(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyLinkModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        link = CompanyLinkModel(company_id=co.id, url="https://google.com")
        sa_session.add(link)
        sa_session.commit()
        r = client.delete(f"/api/companies/{co.id}/links/{link.id}")
        assert r.status_code == 200

    def test_add_note(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        r = client.post(f"/api/companies/{co.id}/notes", json={"content": "Great company"})
        assert r.status_code == 200

    def test_get_company_notes(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyLinkModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        sa_session.add(CompanyLinkModel(company_id=co.id, url="", title="note:Great company"))
        sa_session.commit()
        r = client.get(f"/api/companies/{co.id}/notes")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_delete_company_note(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel, CompanyLinkModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        link = CompanyLinkModel(company_id=co.id, url="", title="note:Test")
        sa_session.add(link)
        sa_session.commit()
        r = client.delete(f"/api/companies/{co.id}/notes/{link.id}")
        assert r.status_code == 200


# ── Insights ──────────────────────────────────────────────────────

class TestInsightsEndpoints:
    def test_get_insights(self, client, sa_session):
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        sa_session.add(CareerInsightModel(insight_type="skills", data_json='{"key": "val"}'))
        sa_session.commit()
        r = client.get("/api/insights")
        assert r.status_code == 200
        assert "skills" in r.json()

    def test_get_insights_empty(self, client):
        r = client.get("/api/insights")
        assert r.status_code == 200
        assert r.json() == {}

    def test_get_insights_status(self, client, sa_session):
        from shared.infrastructure.database.models.insight_model import CareerInsightModel, CareerInsightRunModel
        sa_session.add(CareerInsightModel(insight_type="skills", data_json='{}'))
        sa_session.add(CareerInsightRunModel(insight_type="skills", status="completed"))
        sa_session.commit()
        r = client.get("/api/insights/status")
        assert r.status_code == 200
        assert len(r.json()["sections"]) >= 1

    def test_get_insights_status_no_runs(self, client, sa_session):
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        sa_session.add(CareerInsightModel(insight_type="market", data_json='{}'))
        sa_session.commit()
        r = client.get("/api/insights/status")
        assert r.status_code == 200

    def test_get_insights_progress(self, client):
        r = client.get("/api/insights/progress")
        assert r.status_code == 200
        assert r.json()["running"] is False

    def test_get_skills_intelligence(self, client, sa_session):
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        sa_session.add(CareerInsightModel(insight_type="skills", data_json='{"skills": [{"name": "Python"}]}'))
        sa_session.commit()
        r = client.get("/api/insights/skills-intel")
        assert r.status_code == 200

    def test_get_skills_intelligence_empty(self, client):
        r = client.get("/api/insights/skills-intel")
        assert r.status_code == 200
        assert r.json()["skills"] == []

    def test_get_insight_section(self, client, sa_session):
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        sa_session.add(CareerInsightModel(insight_type="market", data_json='{"data": 1}'))
        sa_session.commit()
        r = client.get("/api/insights/market")
        assert r.status_code == 200

    def test_get_insight_section_not_found(self, client):
        r = client.get("/api/insights/nonexistent")
        assert r.status_code == 200
        assert r.json()["data"] is None

    def test_cancel_insights(self, client):
        with patch("career.presentation.api.insights_router.get_task_manager") as mock_tm:
            mock_tm.return_value = MagicMock(cancel=MagicMock(return_value=True))
            r = client.post("/api/insights/cancel")
            assert r.status_code == 200
            assert r.json()["status"] == "cancelled"

    def test_refresh_insights(self, client):
        with patch("career.presentation.api.insights_router.get_task_manager") as mock_tm:
            mock_tm.return_value = MagicMock(run=AsyncMock())
            r = client.post("/api/insights/refresh")
            assert r.status_code == 200
            assert r.json()["status"] == "started"

    def test_refresh_insight_section(self, client):
        with patch("career.presentation.api.insights_router.get_task_manager") as mock_tm:
            mock_tm.return_value = MagicMock(run=AsyncMock())
            r = client.post("/api/insights/skills/refresh")
            assert r.status_code == 200
            assert r.json()["section"] == "skills"


# ── Pending ───────────────────────────────────────────────────────

class TestPendingEndpoints:
    def test_list_pending_empty(self, client):
        r = client.get("/api/pending")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_pending(self, client):
        r = client.post("/api/pending", json={"url": "https://example.com/job1", "source": "api"})
        assert r.status_code == 200

    def test_get_pending(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://example.com/job1", status="pending")
        sa_session.add(pj)
        sa_session.commit()
        r = client.get(f"/api/pending/{pj.id}")
        assert r.status_code == 200

    def test_get_pending_not_found(self, client):
        r = client.get("/api/pending/999")
        assert r.status_code == 404

    def test_cancel_pending(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://example.com/job1", status="pending")
        sa_session.add(pj)
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.delete(f"/api/pending/{pj.id}")
            assert r.status_code == 200

    def test_reset_pending(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://example.com/job1", status="failed")
        sa_session.add(pj)
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post(f"/api/pending/{pj.id}/reset")
            assert r.status_code == 200

    def test_queue_all(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        sa_session.add(PendingJobModel(url="https://ex.com/1", status="created"))
        sa_session.add(PendingJobModel(url="https://ex.com/2", status="created"))
        sa_session.commit()
        r = client.post("/api/pending/process-all")
        assert r.status_code == 200
        assert r.json()["queued"] == 2


# ── Pending Companies ─────────────────────────────────────────────

class TestPendingCompaniesEndpoints:
    def test_list_pending_companies_empty(self, client):
        r = client.get("/api/pending-companies")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_pending_company(self, client):
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/pending-companies", json={"name": "Google", "input_text": "google.com"})
            assert r.status_code == 200

    def test_create_pending_company_with_notes_and_links(self, client):
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/pending-companies", json={
                "name": "Google",
                "notes": ["note1"],
                "links": [{"url": "https://google.com", "title": "Main"}]
            })
            assert r.status_code == 200

    def test_get_pending_company(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending")
        sa_session.add(pc)
        sa_session.commit()
        r = client.get(f"/api/pending-companies/{pc.id}")
        assert r.status_code == 200

    def test_get_pending_company_not_found(self, client):
        r = client.get("/api/pending-companies/999")
        assert r.status_code == 404

    def test_cancel_pending_company(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending")
        sa_session.add(pc)
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.delete(f"/api/pending-companies/{pc.id}")
            assert r.status_code == 200

    def test_add_company_notes(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending", notes="[]")
        sa_session.add(pc)
        sa_session.commit()
        r = client.post(f"/api/pending-companies/{pc.id}/notes", json={"note": "Great company", "note_type": "text"})
        assert r.status_code == 200

    def test_add_company_notes_not_found(self, client):
        r = client.post("/api/pending-companies/999/notes", json={"note": "test"})
        assert r.status_code == 404

    def test_add_company_links(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending", notes="[]")
        sa_session.add(pc)
        sa_session.commit()
        r = client.post(f"/api/pending-companies/{pc.id}/links", json={"links": [{"url": "https://google.com", "title": "Main"}]})
        assert r.status_code == 200

    def test_add_company_links_not_found(self, client):
        r = client.post("/api/pending-companies/999/links", json={"links": []})
        assert r.status_code == 404


# ── Resumes ───────────────────────────────────────────────────────

class TestResumesEndpoints:
    def test_list_resumes_empty(self, client):
        r = client.get("/api/resumes")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_resumes(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original", title="My Resume", content="Content"))
        sa_session.commit()
        r = client.get("/api/resumes")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_active_generations(self, client):
        r = client.get("/api/resumes/active-generations")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_resume(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original", title="My Resume"))
        sa_session.commit()
        r = client.get("/api/resumes/original")
        assert r.status_code == 200

    def test_get_resume_not_found(self, client):
        r = client.get("/api/resumes/nonexistent")
        assert r.status_code == 404

    def test_create_resume(self, client):
        r = client.post("/api/resumes", json={"title": "New Resume", "content": "Content"})
        assert r.status_code == 200

    def test_update_resume(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original", title="Old Title"))
        sa_session.commit()
        r = client.put("/api/resumes/original", json={"title": "New Title"})
        assert r.status_code == 200

    def test_update_resume_not_found(self, client):
        r = client.put("/api/resumes/nonexistent", json={"title": "X"})
        assert r.status_code == 404

    def test_update_resume_empty_fields(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original", title="Old"))
        sa_session.commit()
        r = client.put("/api/resumes/original", json={"irrelevant": "value"})
        assert r.status_code == 200

    def test_delete_resume(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original"))
        sa_session.commit()
        r = client.delete("/api/resumes/original")
        assert r.status_code == 200

    def test_generate_cover_letter(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original"))
        sa_session.commit()
        r = client.post("/api/resumes/original/generate-cover", json={"job_num": 1})
        assert r.status_code == 200
        assert r.json()["status"] == "started"


# ── Rules ─────────────────────────────────────────────────────────

class TestRulesEndpoints:
    def test_get_rules(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        sa_session.add(PreferenceModel(category="fit", key="remote", value="true", scope="JOB"))
        sa_session.commit()
        r = client.get("/api/rules")
        assert r.status_code == 200

    def test_get_rules_empty(self, client):
        r = client.get("/api/rules")
        assert r.status_code == 200
        assert r.json() == {}

    def test_create_rule(self, client):
        r = client.post("/api/rules", json={"category": "fit", "key": "remote", "value": "true"})
        assert r.status_code == 200

    def test_create_rule_batch(self, client):
        r = client.post("/api/rules", json={"rules": [{"key": "a", "value": "1"}, {"key": "b", "value": "2"}]})
        assert r.status_code == 200

    def test_update_rule(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        sa_session.add(PreferenceModel(category="fit", key="remote", value="true"))
        sa_session.commit()
        pref_id = sa_session.query(PreferenceModel).first().id
        r = client.put(f"/api/rules/{pref_id}", json={"value": "false"})
        assert r.status_code == 200

    def test_delete_rule(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        sa_session.add(PreferenceModel(category="fit", key="remote", value="true"))
        sa_session.commit()
        pref_id = sa_session.query(PreferenceModel).first().id
        r = client.delete(f"/api/rules/{pref_id}")
        assert r.status_code == 200

    def test_bulk_update_rules(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import PreferenceModel
        sa_session.add(PreferenceModel(category="fit", key="remote", value="true", priority=1))
        sa_session.commit()
        pref_id = sa_session.query(PreferenceModel).first().id
        r = client.put("/api/rules", json={"rules": [{"id": pref_id, "priority": 10}]})
        assert r.status_code == 200


# ── Dashboard ─────────────────────────────────────────────────────

class TestDashboardEndpoints:
    def test_get_dashboard(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        from shared.infrastructure.database.models.skill_model import SkillModel
        from shared.infrastructure.database.models.company_model import CompanyModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", match="High", company="A"))
        sa_session.add(SkillModel(name="Python", hidden=0))
        sa_session.add(CompanyModel(name="Google"))
        sa_session.commit()
        r = client.get("/api/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert data["jobs_total"] == 1
        assert data["companies_total"] == 1

    def test_get_cities(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", location="Berlin", company="A"))
        sa_session.add(JobModel(num=2, url="https://ex.com/2", location="Berlin", company="B"))
        sa_session.add(JobModel(num=3, url="https://ex.com/3", location="Munich", company="C"))
        sa_session.commit()
        r = client.get("/api/cities")
        assert r.status_code == 200
        assert len(r.json()["items"]) == 2

    def test_get_cities_with_locations_json(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", location="Berlin", locations='["Berlin", "Remote"]', company="A"))
        sa_session.commit()
        r = client.get("/api/cities")
        assert r.status_code == 200
        assert len(r.json()["items"]) == 2

    def test_get_cities_not_specified_excluded(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", location="Not specified", company="A"))
        sa_session.commit()
        r = client.get("/api/cities")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_get_generation_history(self, client):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = MagicMock()
            r = client.get("/api/generation-history")
            assert r.status_code == 200
            assert "items" in r.json()

    def test_get_local_history_job(self, client, sa_session):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = sa_session
            r = client.get("/api/local-history?context=job&job_num=1")
            assert r.status_code == 200

    def test_get_local_history_company(self, client):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = MagicMock()
            r = client.get("/api/local-history?context=company&company_id=1")
            assert r.status_code == 200

    def test_get_local_history_skill(self, client):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = MagicMock()
            r = client.get("/api/local-history?context=skill&skill_name=Python")
            assert r.status_code == 200

    def test_get_local_history_insight(self, client):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = MagicMock()
            r = client.get("/api/local-history?context=insight&insight_type=market")
            assert r.status_code == 200

    def test_get_local_history_invalid_context(self, client):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = MagicMock()
            r = client.get("/api/local-history?context=bad")
            assert r.status_code == 200
            assert r.json()["total"] == 0

    def test_get_local_active_count(self, client, sa_session):
        with patch("dependencies.get_session_sync") as mock_sess:
            mock_sess.return_value = sa_session
            r = client.get("/api/local-history/active?context=job&job_num=1")
            assert r.status_code == 200
            assert "active_count" in r.json()


# ── Skill Roadmaps ────────────────────────────────────────────────

class TestSkillRoadmapsEndpoints:
    def test_list_roadmaps_empty(self, client):
        r = client.get("/api/skill-roadmaps")
        assert r.status_code == 200
        assert r.json() == []

    def test_list_roadmaps_by_skill(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        sa_session.add(SkillRoadmapModel(skill_name="Python", title="Basics", level=0))
        sa_session.commit()
        r = client.get("/api/skill-roadmaps?skill=Python")
        assert r.status_code == 200
        data = r.json()
        assert data["skill_name"] == "Python"
        assert len(data["roadmap"]) == 1

    def test_list_roadmaps_all(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        sa_session.add(SkillRoadmapModel(skill_name="Python", title="Basics"))
        sa_session.commit()
        r = client.get("/api/skill-roadmaps")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_get_roadmap(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        sa_session.add(rm)
        sa_session.commit()
        r = client.get(f"/api/skill-roadmaps/{rm.id}")
        assert r.status_code == 200

    def test_get_roadmap_not_found(self, client):
        r = client.get("/api/skill-roadmaps/999")
        assert r.status_code == 404

    def test_get_roadmap_job_progress(self, client):
        r = client.get("/api/skill-roadmaps/progress")
        assert r.status_code == 200

    def test_get_roadmap_job_progress_by_skill(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        sa_session.add(SkillRoadmapJobModel(skill_name="Python", status="done"))
        sa_session.commit()
        r = client.get("/api/skill-roadmaps/progress?skill=Python")
        assert r.status_code == 200

    def test_get_roadmap_job_progress_by_skill_not_found(self, client):
        r = client.get("/api/skill-roadmaps/progress?skill=Nonexistent")
        assert r.status_code == 200
        assert r.json()["status"] == "idle"

    def test_get_roadmap_jobs(self, client):
        r = client.get("/api/skill-roadmaps/jobs")
        assert r.status_code == 200

    def test_get_roadmap_jobs_by_skill(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
        sa_session.add(SkillRoadmapJobModel(skill_name="Python", status="done"))
        sa_session.commit()
        r = client.get("/api/skill-roadmaps/jobs?skill=Python")
        assert r.status_code == 200

    def test_get_all_progress(self, client):
        r = client.get("/api/skill-roadmaps/progress/all")
        assert r.status_code == 200

    def test_generate_roadmap(self, client):
        with patch("skills.presentation.api.skill_roadmaps_router.get_task_manager") as mock_tm:
            mock_tm.return_value = MagicMock(run=AsyncMock())
            r = client.post("/api/skill-roadmaps/generate", json={"skill_name": "Python"})
            assert r.status_code == 200

    def test_extend_roadmap(self, client):
        with patch("skills.presentation.api.skill_roadmaps_router.get_task_manager") as mock_tm:
            mock_tm.return_value = MagicMock(run=AsyncMock())
            r = client.post("/api/skill-roadmaps/extend", json={"skill_name": "Python"})
            assert r.status_code == 200

    def test_finegrain_roadmap(self, client):
        with patch("skills.presentation.api.skill_roadmaps_router.get_task_manager") as mock_tm:
            mock_tm.return_value = MagicMock(run=AsyncMock())
            r = client.post("/api/skill-roadmaps/finegrain", json={"skill_name": "Python"})
            assert r.status_code == 200

    def test_cancel_roadmap(self, client):
        r = client.post("/api/skill-roadmaps/cancel?skill=Python")
        assert r.status_code == 200

    def test_build_roadmap_tree(self):
        from skills.presentation.api.skill_roadmaps_router import build_roadmap_tree
        rows = [
            {"id": 1, "skill_name": "Python", "title": "Root", "parent_id": None},
            {"id": 2, "skill_name": "Python", "title": "Child", "parent_id": 1},
        ]
        tree = build_roadmap_tree(rows)
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 1

    def test_build_roadmap_tree_no_parent(self):
        from skills.presentation.api.skill_roadmaps_router import build_roadmap_tree
        rows = [
            {"id": 1, "skill_name": "Python", "title": "A", "parent_id": None},
            {"id": 2, "skill_name": "Python", "title": "B", "parent_id": 999},
        ]
        tree = build_roadmap_tree(rows)
        assert len(tree) == 2


# ── Router compat routes ──────────────────────────────────────────

class TestRouterCompatRoutes:
    def test_summaries_compat(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SummaryModel
        sa_session.add(SummaryModel(num=1, company="A", score="A"))
        sa_session.commit()
        r = client.get("/api/summaries")
        assert r.status_code == 200

    def test_linkedin_compat(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import ResumeModel
        sa_session.add(ResumeModel(id="original", title="Resume"))
        sa_session.add(ResumeModel(id="linkedin_123", title="LinkedIn"))
        sa_session.commit()
        r = client.get("/api/linkedin")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_tech_stack_compat(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillModel
        sa_session.add(SkillModel(name="Python", hidden=0))
        sa_session.commit()
        r = client.get("/api/tech-stack")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_skills_intel_dashboard_compat(self, client, sa_session):
        from shared.infrastructure.database.models.insight_model import CareerInsightModel
        sa_session.add(CareerInsightModel(insight_type="skills", data_json='{"skills": []}'))
        sa_session.commit()
        r = client.get("/api/skills-intelligence/dashboard")
        assert r.status_code == 200

    def test_skills_intel_dashboard_empty(self, client):
        r = client.get("/api/skills-intelligence/dashboard")
        assert r.status_code == 200
        assert r.json()["skills"] == []

    def test_skill_roadmap_progress_all(self, client):
        r = client.get("/api/skill-roadmap-progress/all")
        assert r.status_code == 200

    def test_skill_roadmap_progress_compat(self, client):
        r = client.get("/api/skill-roadmap-progress")
        assert r.status_code == 200

    def test_skill_roadmap_progress_compat_by_skill(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel, SkillRoadmapProgressModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        sa_session.add(rm)
        sa_session.commit()
        sa_session.add(SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name="Python", completed=1))
        sa_session.commit()
        r = client.get("/api/skill-roadmap-progress?skill=Python")
        assert r.status_code == 200

    def test_toggle_roadmap_progress(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        sa_session.add(rm)
        sa_session.commit()
        r = client.patch(f"/api/skill-roadmap-progress/{rm.id}")
        assert r.status_code == 200

    def test_update_roadmap_progress(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        sa_session.add(rm)
        sa_session.commit()
        r = client.put(f"/api/skill-roadmap-progress/{rm.id}", json={"completed": True})
        assert r.status_code == 200

    def test_update_roadmap_progress_empty_data(self, client, sa_session):
        from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
        rm = SkillRoadmapModel(skill_name="Python", title="Basics")
        sa_session.add(rm)
        sa_session.commit()
        r = client.put(f"/api/skill-roadmap-progress/{rm.id}")
        assert r.status_code == 200

    def test_skill_roadmap_jobs_compat(self, client):
        r = client.get("/api/skill-roadmap-jobs")
        assert r.status_code == 200

    def test_get_skill_relationships_compat(self, client):
        r = client.get("/api/skill-relationships/Python")
        assert r.status_code == 200

    def test_create_skill_relationship_compat(self, client):
        r = client.post("/api/skill-relationships", json={"skill_name": "Python", "related_name": "Django", "relation_type": "related"})
        assert r.status_code == 200

    def test_delete_skill_relationship_compat(self, client, sa_session):
        from shared.infrastructure.database.models.skill_model import SkillRelationshipModel
        sa_session.add(SkillRelationshipModel(skill_name="A", related_name="B", relation_type="related"))
        sa_session.commit()
        rel_id = sa_session.query(SkillRelationshipModel).first().id
        r = client.delete(f"/api/skill-relationships/{rel_id}")
        assert r.status_code == 200

    def test_process_pending(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingJobModel
        pj = PendingJobModel(url="https://ex.com/1", status="pending")
        sa_session.add(pj)
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post(f"/api/pending/{pj.id}/process")
            assert r.status_code == 200

    def test_delete_company_note_compat(self, client):
        r = client.delete("/api/pending-companies/1/notes/1")
        assert r.status_code == 200

    def test_add_pending_company_link_compat(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending", notes="[]")
        sa_session.add(pc)
        sa_session.commit()
        r = client.post(f"/api/pending-companies/{pc.id}/links", json={"url": "https://example.com"})
        assert r.status_code == 200

    def test_delete_pending_company_link_compat(self, client):
        r = client.delete("/api/pending-companies/1/links/1")
        assert r.status_code == 200

    def test_process_pending_company(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        pc = PendingCompanyModel(input_text="Google", status="pending")
        sa_session.add(pc)
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post(f"/api/pending-companies/{pc.id}/process")
            assert r.status_code == 200

    def test_queue_all_pending_companies(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingCompanyModel
        sa_session.add(PendingCompanyModel(input_text="A", status="created"))
        sa_session.add(PendingCompanyModel(input_text="B", status="created"))
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/pending-companies/queue-all")
            assert r.status_code == 200
            assert r.json()["count"] == 2

    def test_link_job_to_company(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1", company="A"))
        sa_session.commit()
        r = client.post("/api/jobs/1/link-company", json={"company_id": 1})
        assert r.status_code == 200

    def test_link_job_to_company_no_id(self, client, sa_session):
        from shared.infrastructure.database.models.job_model import JobModel
        sa_session.add(JobModel(num=1, url="https://ex.com/1"))
        sa_session.commit()
        r = client.post("/api/jobs/1/link-company", json={})
        assert r.status_code == 200

    def test_reprocess_company(self, client, sa_session):
        from shared.infrastructure.database.models.company_model import CompanyModel
        co = CompanyModel(name="Google")
        sa_session.add(co)
        sa_session.commit()
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post(f"/api/companies/{co.id}/reprocess")
            assert r.status_code == 200

    def test_reprocess_company_not_found(self, client):
        with patch("shared.infrastructure.config.queue.get_queue_manager") as mock_qm:
            mock_qm.return_value = MagicMock()
            r = client.post("/api/companies/999/reprocess")
            assert r.status_code == 200
            assert "error" in r.json()

    def test_cancel_generation(self, client, sa_session):
        from shared.infrastructure.database.models.pending_model import PendingGenerationModel
        gen = PendingGenerationModel(job_num=1, type="resume", status="processing")
        sa_session.add(gen)
        sa_session.commit()
        r = client.post(f"/api/generations/{gen.id}/cancel")
        assert r.status_code == 200

    def test_cancel_generation_not_found(self, client):
        r = client.post("/api/generations/999/cancel")
        assert r.status_code == 404
