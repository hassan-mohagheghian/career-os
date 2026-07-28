"""Comprehensive API route tests — covers all endpoints via TestClient."""
import sys, os, json, tempfile, pytest
from unittest.mock import patch, MagicMock, AsyncMock
from contextlib import asynccontextmanager
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from shared.infrastructure.database.sqlalchemy_config import Base
import jobs.infrastructure.models.job_model
import skills.infrastructure.models.skill_model
import companies.infrastructure.models.company_model
import processing.infrastructure.models.pending_model
import career.infrastructure.models.insight_model
import shared.infrastructure.database.models.misc_models


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def sa_session(test_db):
    try:
        test_db.rollback()
    except Exception:
        test_db.close()
        test_db.begin()
    yield test_db


@asynccontextmanager
async def no_lifespan(app):
    yield


def _build_app(sa_session):
    from app.server.entrypoints.api import create_app
    from dependencies import (
        get_session, get_session_sync, get_job_repo, get_skill_repo,
        get_company_repo, get_pending_repo, get_insight_repo, get_preference_repo,
        get_summary_repo, get_resume_repo, get_company_link_repo, get_company_intelligence_repo,
        get_pending_generation_repo, get_career_insight_run_repo,
        get_skill_roadmap_repo, get_skill_roadmap_progress_repo, get_skill_roadmap_job_repo,
    )
    from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
    from skills.infrastructure.repositories.sa_skill_repository import SQLAlchemySkillRepository
    from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
    from processing.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
    from career.infrastructure.repositories.sa_insight_repository import SQLAlchemyInsightRepository
    from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
    from jobs.infrastructure.repositories.sa_summary_repository import SQLAlchemySummaryRepository
    from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
    from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
    from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
    from processing.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
    from career.infrastructure.repositories.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_repository import SQLAlchemySkillRoadmapRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_progress_repository import SQLAlchemySkillRoadmapProgressRepository
    from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository

    app = create_app()
    app.router.lifespan_context = no_lifespan

    def override_get_session():
        yield sa_session

    def override_get_session_sync():
        return sa_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_session_sync] = override_get_session_sync
    app.dependency_overrides[get_job_repo] = lambda: SQLAlchemyJobRepository(sa_session)
    app.dependency_overrides[get_skill_repo] = lambda: SQLAlchemySkillRepository(sa_session)
    app.dependency_overrides[get_company_repo] = lambda: SQLAlchemyCompanyRepository(sa_session)
    app.dependency_overrides[get_pending_repo] = lambda: SQLAlchemyPendingRepository(sa_session)
    app.dependency_overrides[get_insight_repo] = lambda: SQLAlchemyInsightRepository(sa_session)
    app.dependency_overrides[get_preference_repo] = lambda: SQLAlchemyPreferenceRepository(sa_session)
    app.dependency_overrides[get_summary_repo] = lambda: SQLAlchemySummaryRepository(sa_session)
    app.dependency_overrides[get_resume_repo] = lambda: SQLAlchemyResumeRepository(sa_session)
    app.dependency_overrides[get_company_link_repo] = lambda: SQLAlchemyCompanyLinkRepository(sa_session)
    app.dependency_overrides[get_company_intelligence_repo] = lambda: SQLAlchemyCompanyIntelligenceRepository(sa_session)
    app.dependency_overrides[get_pending_generation_repo] = lambda: SQLAlchemyPendingGenerationRepository(sa_session)
    app.dependency_overrides[get_career_insight_run_repo] = lambda: SQLAlchemyCareerInsightRunRepository(sa_session)
    app.dependency_overrides[get_skill_roadmap_repo] = lambda: SQLAlchemySkillRoadmapRepository(sa_session)
    app.dependency_overrides[get_skill_roadmap_progress_repo] = lambda: SQLAlchemySkillRoadmapProgressRepository(sa_session)
    app.dependency_overrides[get_skill_roadmap_job_repo] = lambda: SQLAlchemySkillRoadmapJobRepository(sa_session)

    return app


@pytest.fixture(scope="module")
def client(test_db):
    app = _build_app(test_db)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ── Helper functions ──────────────────────────────────────────────

def create_test_job(session, num=9001, company="TestCorp_API", url="https://example.com/api-test", **overrides):
    from jobs.infrastructure.models.job_model import JobModel
    job = JobModel(num=num, company=company, role="API Tester", location="Berlin",
                   url=url, match="95%", score="A", work_type="Remote",
                   deleted=0, workflow_log="[]", locations='["Berlin"]', work_types='["Remote"]',
                   employment_type="Full-time", **overrides)
    session.add(job)
    session.commit()
    return job


def create_test_skill(session, name="Python_API", level=8, category="technical"):
    from skills.infrastructure.models.skill_model import SkillModel
    skill = SkillModel(name=name, level=level, category=category, source="api_test")
    session.add(skill)
    session.commit()
    return skill


def create_test_company(session, name="TestCorp_API"):
    from companies.infrastructure.models.company_model import CompanyModel
    company = CompanyModel(name=name, industry="Tech", city="Berlin", country="DE")
    session.add(company)
    session.commit()
    return company


def create_test_pending_job(session, url="https://example.com/pending-api-test", status="pending"):
    from processing.infrastructure.models.pending_model import PendingJobModel
    item = PendingJobModel(url=url, source="api_test", status=status)
    session.add(item)
    session.commit()
    return item


def create_test_pending_company(session, input_text="TestCompany_API", status="pending"):
    from processing.infrastructure.models.pending_model import PendingCompanyModel
    item = PendingCompanyModel(input_text=input_text, source="api_test", status=status)
    session.add(item)
    session.commit()
    return item


def create_test_insight(session, insight_type="skills", data_json='{"test": true}'):
    from career.infrastructure.models.insight_model import CareerInsightModel
    insight = CareerInsightModel(insight_type=insight_type, data_json=data_json, score=8.5)
    session.add(insight)
    session.commit()
    return insight


def create_test_resume(session, id="resume_api_test", title="API Test Resume"):
    from shared.infrastructure.database.models.misc_models import ResumeModel
    resume = ResumeModel(id=id, title=title, content="Test content", raw_text="Raw text")
    session.add(resume)
    session.commit()
    return resume


def create_test_roadmap(session, skill_name="Python_API", title="Basics"):
    from shared.infrastructure.database.models.misc_models import SkillRoadmapModel
    rm = SkillRoadmapModel(skill_name=skill_name, title=title, description="Test roadmap")
    session.add(rm)
    session.commit()
    return rm


def create_test_preference(session, category="location", key="berlin", value="true", scope="SHARED"):
    from shared.infrastructure.database.models.misc_models import PreferenceModel
    pref = PreferenceModel(category=category, key=key, value=value, scope=scope)
    session.add(pref)
    session.commit()
    return pref


def create_test_summary(session, num=9001, company="TestCorp_API"):
    from shared.infrastructure.database.models.misc_models import SummaryModel
    summary = SummaryModel(num=num, company=company, match="95%", score="A", summary="Test summary")
    session.add(summary)
    session.commit()
    return summary


# ── HEALTH ────────────────────────────────────────────────────────

class TestHealth:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ── JOBS ──────────────────────────────────────────────────────────

class TestJobsAPI:
    def test_list_jobs_empty(self, client):
        r = client.get("/api/jobs")
        assert r.status_code == 200
        data = r.json()
        assert "jobs" in data
        assert "total" in data

    def test_list_jobs_with_data(self, client, sa_session):
        create_test_job(sa_session, num=9100, company="ListCorp")
        r = client.get("/api/jobs")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_list_jobs_with_filters(self, client, sa_session):
        create_test_job(sa_session, num=9101, company="FilterCorp")
        r = client.get("/api/jobs?filter_companies=FilterCorp")
        assert r.status_code == 200

    def test_list_jobs_pagination(self, client, sa_session):
        for i in range(5):
            create_test_job(sa_session, num=9110+i, company=f"PageCorp{i}")
        r = client.get("/api/jobs?offset=0&limit=2")
        assert r.status_code == 200
        assert len(r.json()["jobs"]) <= 2

    def test_get_job(self, client, sa_session):
        create_test_job(sa_session, num=9200)
        r = client.get("/api/jobs/9200")
        assert r.status_code == 200
        assert r.json()["num"] == 9200

    def test_get_job_not_found(self, client):
        r = client.get("/api/jobs/99999")
        assert r.status_code == 404

    def test_update_job(self, client, sa_session):
        create_test_job(sa_session, num=9300)
        r = client.put("/api/jobs/9300", json={"role": "Updated Role"})
        assert r.status_code == 200

    def test_update_job_not_found(self, client):
        r = client.put("/api/jobs/99999", json={"role": "X"})
        assert r.status_code == 404

    def test_delete_job(self, client, sa_session):
        create_test_job(sa_session, num=9400)
        r = client.delete("/api/jobs/9400")
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    def test_get_summaries(self, client, sa_session):
        create_test_summary(sa_session, num=9500)
        r = client.get("/api/jobs/summaries")
        assert r.status_code == 200

    def test_get_generation_history(self, client, sa_session):
        create_test_job(sa_session, num=9600)
        r = client.get("/api/jobs/9600/generation-history")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_requeue_job(self, client, sa_session):
        create_test_job(sa_session, num=9700, url="https://example.com/requeue-test")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post("/api/jobs/9700/requeue")
            assert r.status_code == 200
            assert r.json()["status"] == "queued"

    def test_requeue_job_not_found(self, client):
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post("/api/jobs/99999/requeue")
            assert r.status_code == 404

    def test_rescore_job(self, client, sa_session):
        create_test_job(sa_session, num=9800, url="https://example.com/rescore-test")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post("/api/jobs/9800/rescore")
            assert r.status_code == 200

    def test_rescore_job_not_found(self, client):
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post("/api/jobs/99999/rescore")
            assert r.status_code == 404

    def test_generate_resume(self, client, sa_session):
        create_test_job(sa_session, num=9900)
        with patch('dependencies.get_session_sync', return_value=sa_session):
            r = client.post("/api/jobs/9900/generate-resume")
            assert r.status_code == 200
            assert r.json()["status"] == "queued"

    def test_generate_resume_not_found(self, client, sa_session):
        with patch('dependencies.get_session_sync', return_value=sa_session):
            r = client.post("/api/jobs/99999/generate-resume")
            assert r.status_code == 404

    def test_generate_cover(self, client, sa_session):
        create_test_job(sa_session, num=9901)
        with patch('dependencies.get_session_sync', return_value=sa_session):
            r = client.post("/api/jobs/9901/generate-cover")
            assert r.status_code == 200

    def test_generate_cover_not_found(self, client, sa_session):
        with patch('dependencies.get_session_sync', return_value=sa_session):
            r = client.post("/api/jobs/99999/generate-cover")
            assert r.status_code == 404

    def test_link_job_to_company(self, client, sa_session):
        company = create_test_company(sa_session)
        create_test_job(sa_session, num=9902)
        r = client.post("/api/jobs/9902/link-company", json={"company_id": company.id})
        assert r.status_code == 200


# ── SKILLS ────────────────────────────────────────────────────────

class TestSkillsAPI:
    def test_list_skills(self, client, sa_session):
        create_test_skill(sa_session, "SkillList_API")
        r = client.get("/api/skills")
        assert r.status_code == 200

    def test_list_skills_by_category(self, client, sa_session):
        create_test_skill(sa_session, "SkillCat_API", category="engineering")
        r = client.get("/api/skills?category=engineering")
        assert r.status_code == 200

    def test_list_hidden_skills(self, client, sa_session):
        from skills.infrastructure.models.skill_model import SkillModel
        s = SkillModel(name="Hidden_API", hidden=1)
        sa_session.add(s)
        sa_session.commit()
        r = client.get("/api/skills/hidden")
        assert r.status_code == 200

    def test_get_categories(self, client, sa_session):
        create_test_skill(sa_session, "SkillCats_API", category="technical")
        r = client.get("/api/skills/categories")
        assert r.status_code == 200

    def test_get_stats(self, client, sa_session):
        create_test_skill(sa_session, "SkillStats_API")
        r = client.get("/api/skills/stats")
        assert r.status_code == 200

    def test_create_skill(self, client):
        r = client.post("/api/skills", json={"name": "NewSkill_API", "level": 5})
        assert r.status_code == 200

    def test_create_skill_duplicate(self, client, sa_session):
        create_test_skill(sa_session, "DupSkill_API")
        r = client.post("/api/skills", json={"name": "DupSkill_API", "level": 5})
        assert r.status_code == 200
        assert "already exists" in r.json().get("message", "")

    def test_update_skill(self, client, sa_session):
        skill = create_test_skill(sa_session, "UpdSkill_API")
        r = client.put(f"/api/skills/{skill.id}", json={"level": 10})
        assert r.status_code == 200

    def test_update_skill_not_found(self, client):
        r = client.put("/api/skills/99999", json={"level": 10})
        assert r.status_code == 404

    def test_update_skill_empty(self, client, sa_session):
        skill = create_test_skill(sa_session, "EmptyUpd_API")
        r = client.put(f"/api/skills/{skill.id}", json={})
        assert r.status_code == 400

    def test_rename_skill(self, client, sa_session):
        skill = create_test_skill(sa_session, "RenameMe_API")
        r = client.patch(f"/api/skills/{skill.id}/rename", json={"name": "Renamed_API"})
        assert r.status_code == 200

    def test_rename_skill_not_found(self, client):
        r = client.patch("/api/skills/99999/rename", json={"name": "X"})
        assert r.status_code == 404

    def test_delete_skill(self, client, sa_session):
        skill = create_test_skill(sa_session, "DelSkill_API")
        r = client.delete(f"/api/skills/{skill.id}")
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

    def test_delete_skill_not_found(self, client):
        r = client.delete("/api/skills/99999")
        assert r.status_code == 404

    def test_hide_skill(self, client, sa_session):
        skill = create_test_skill(sa_session, "HideSkill_API")
        r = client.patch(f"/api/skills/{skill.id}/hide", json={"hidden": 1})
        assert r.status_code == 200

    def test_hide_skill_not_found(self, client):
        r = client.patch("/api/skills/99999/hide", json={"hidden": 1})
        assert r.status_code == 404

    def test_restore_skill(self, client, sa_session):
        skill = create_test_skill(sa_session, "RestoreSkill_API")
        r = client.patch(f"/api/skills/{skill.id}/restore")
        assert r.status_code == 200

    def test_restore_skill_not_found(self, client):
        r = client.patch("/api/skills/99999/restore")
        assert r.status_code == 404

    def test_merge_skills(self, client, sa_session):
        target = create_test_skill(sa_session, "MergeTarget_API")
        source = create_test_skill(sa_session, "MergeSource_API")
        r = client.post("/api/skills/merge", json={"target_id": target.id, "source_ids": [source.id]})
        assert r.status_code == 200

    def test_bulk_hide(self, client, sa_session):
        s1 = create_test_skill(sa_session, "BulkH1_API")
        s2 = create_test_skill(sa_session, "BulkH2_API")
        r = client.post("/api/skills/bulk-hide", json={"ids": [s1.id, s2.id]})
        assert r.status_code == 200

    def test_bulk_hide_empty(self, client):
        r = client.post("/api/skills/bulk-hide", json={"ids": []})
        assert r.status_code == 400

    def test_bulk_categorize(self, client, sa_session):
        s1 = create_test_skill(sa_session, "BulkC1_API")
        r = client.post("/api/skills/bulk-categorize", json={"ids": [s1.id], "category": "technical"})
        assert r.status_code == 200

    def test_bulk_categorize_invalid(self, client, sa_session):
        s1 = create_test_skill(sa_session, "BulkCI_API")
        r = client.post("/api/skills/bulk-categorize", json={"ids": [s1.id], "category": "INVALID"})
        assert r.status_code == 400

    def test_update_category(self, client, sa_session):
        skill = create_test_skill(sa_session, "CatUpd_API")
        r = client.put(f"/api/skills/{skill.id}/category", json={"category": "engineering"})
        assert r.status_code == 200

    def test_update_category_invalid(self, client, sa_session):
        skill = create_test_skill(sa_session, "CatInv_API")
        r = client.put(f"/api/skills/{skill.id}/category", json={"category": "INVALID"})
        assert r.status_code == 400

    def test_update_category_not_found(self, client):
        r = client.put("/api/skills/99999/category", json={"category": "technical"})
        assert r.status_code == 404

    def test_get_skill_relationships(self, client, sa_session):
        create_test_skill(sa_session, "RelSkill_API")
        r = client.get("/api/skills/skill-relationships/RelSkill_API")
        assert r.status_code == 200

    def test_create_skill_relationship(self, client, sa_session):
        create_test_skill(sa_session, "RelA_API")
        create_test_skill(sa_session, "RelB_API")
        r = client.post("/api/skills/skill-relationships", json={
            "skill_name": "RelA_API", "related_name": "RelB_API", "relation_type": "related_to"
        })
        assert r.status_code == 200

    def test_delete_skill_relationship(self, client, sa_session):
        create_test_skill(sa_session, "RelDelA_API")
        create_test_skill(sa_session, "RelDelB_API")
        from skills.infrastructure.models.skill_model import SkillRelationshipModel
        rel = SkillRelationshipModel(skill_name="RelDelA_API", related_name="RelDelB_API", relation_type="related_to")
        sa_session.add(rel)
        sa_session.commit()
        r = client.delete(f"/api/skills/skill-relationships/{rel.id}")
        assert r.status_code == 200


# ── COMPANIES ─────────────────────────────────────────────────────

class TestCompaniesAPI:
    def test_list_companies(self, client, sa_session):
        create_test_company(sa_session, "ListComp_API")
        r = client.get("/api/companies")
        assert r.status_code == 200

    def test_get_company(self, client, sa_session):
        c = create_test_company(sa_session, "GetComp_API")
        r = client.get(f"/api/companies/{c.id}")
        assert r.status_code == 200

    def test_get_company_not_found(self, client):
        r = client.get("/api/companies/99999")
        assert r.status_code == 404

    def test_create_company(self, client):
        r = client.post("/api/companies", json={"name": "NewComp_API", "industry": "Tech"})
        assert r.status_code == 200

    def test_update_company(self, client, sa_session):
        c = create_test_company(sa_session, "UpdComp_API")
        r = client.put(f"/api/companies/{c.id}", json={"name": "UpdatedComp_API"})
        assert r.status_code == 200

    def test_update_company_not_found(self, client):
        r = client.put("/api/companies/99999", json={"name": "X"})
        assert r.status_code == 404

    def test_delete_company(self, client, sa_session):
        c = create_test_company(sa_session, "DelComp_API")
        r = client.delete(f"/api/companies/{c.id}")
        assert r.status_code == 200

    def test_get_company_intelligence(self, client, sa_session):
        c = create_test_company(sa_session, "IntComp_API")
        r = client.get(f"/api/companies/{c.id}/intelligence")
        assert r.status_code == 200

    def test_get_company_intelligence_with_data(self, client, sa_session):
        c = create_test_company(sa_session, "IntData_API")
        from companies.infrastructure.models.company_model import CompanyIntelligenceModel
        intel = CompanyIntelligenceModel(company_id=c.id, overview="Test overview", scores='{"tech": 8}')
        sa_session.add(intel)
        sa_session.commit()
        r = client.get(f"/api/companies/{c.id}/intelligence")
        assert r.status_code == 200

    def test_get_company_jobs(self, client, sa_session):
        c = create_test_company(sa_session, "CompJobs_API")
        create_test_job(sa_session, num=9050, company="CompJobs_API", company_id=c.id)
        r = client.get(f"/api/companies/{c.id}/jobs")
        assert r.status_code == 200

    def test_get_company_links(self, client, sa_session):
        c = create_test_company(sa_session, "CompLinks_API")
        r = client.get(f"/api/companies/{c.id}/links")
        assert r.status_code == 200

    def test_add_company_link(self, client, sa_session):
        c = create_test_company(sa_session, "CompAddLink_API")
        r = client.post(f"/api/companies/{c.id}/links", json={"url": "https://test.com", "title": "Test"})
        assert r.status_code == 200

    def test_delete_company_link(self, client, sa_session):
        c = create_test_company(sa_session, "CompDelLink_API")
        from companies.infrastructure.models.company_model import CompanyLinkModel
        link = CompanyLinkModel(company_id=c.id, url="https://del.com", title="Delete me")
        sa_session.add(link)
        sa_session.commit()
        r = client.delete(f"/api/companies/{c.id}/links/{link.id}")
        assert r.status_code == 200

    def test_add_note(self, client, sa_session):
        c = create_test_company(sa_session, "CompNote_API")
        r = client.post(f"/api/companies/{c.id}/notes", json={"content": "Test note"})
        assert r.status_code == 200

    def test_get_notes(self, client, sa_session):
        c = create_test_company(sa_session, "CompGetNotes_API")
        from companies.infrastructure.models.company_model import CompanyLinkModel
        note = CompanyLinkModel(company_id=c.id, url="", title="note:Test note")
        sa_session.add(note)
        sa_session.commit()
        r = client.get(f"/api/companies/{c.id}/notes")
        assert r.status_code == 200

    def test_delete_note(self, client, sa_session):
        c = create_test_company(sa_session, "CompDelNote_API")
        from companies.infrastructure.models.company_model import CompanyLinkModel
        note = CompanyLinkModel(company_id=c.id, url="", title="note:Delete me")
        sa_session.add(note)
        sa_session.commit()
        r = client.delete(f"/api/companies/{c.id}/notes/{note.id}")
        assert r.status_code == 200


# ── INSIGHTS ──────────────────────────────────────────────────────

class TestInsightsAPI:
    def test_get_insights(self, client, sa_session):
        create_test_insight(sa_session, "skills")
        r = client.get("/api/insights")
        assert r.status_code == 200

    def test_get_insights_status(self, client, sa_session):
        create_test_insight(sa_session, "overview")
        r = client.get("/api/insights/status")
        assert r.status_code == 200

    def test_get_insights_progress(self, client):
        with patch('career.presentation.api.insights_router.get_task_manager') as mock:
            mock.return_value.is_running = MagicMock(return_value=False)
            r = client.get("/api/insights/progress")
            assert r.status_code == 200

    def test_get_skills_intelligence(self, client, sa_session):
        create_test_insight(sa_session, "skills")
        r = client.get("/api/insights/skills-intel")
        assert r.status_code == 200

    def test_get_skills_intelligence_empty(self, client):
        r = client.get("/api/insights/skills-intel")
        assert r.status_code == 200

    def test_get_insight_section(self, client, sa_session):
        create_test_insight(sa_session, "market")
        r = client.get("/api/insights/market")
        assert r.status_code == 200

    def test_get_insight_section_empty(self, client):
        r = client.get("/api/insights/nonexistent")
        assert r.status_code == 200

    def test_refresh_insights(self, client):
        with patch('career.presentation.api.insights_router.get_task_manager') as mock:
            mock.return_value.run = AsyncMock()
            r = client.post("/api/insights/refresh")
            assert r.status_code == 200

    def test_refresh_insight_section(self, client):
        with patch('career.presentation.api.insights_router.get_task_manager') as mock:
            mock.return_value.run = AsyncMock()
            r = client.post("/api/insights/skills/refresh")
            assert r.status_code == 200

    def test_cancel_insights(self, client):
        with patch('career.presentation.api.insights_router.get_task_manager') as mock:
            mock.return_value.cancel = MagicMock()
            r = client.post("/api/insights/cancel")
            assert r.status_code == 200


# ── PENDING ───────────────────────────────────────────────────────

class TestPendingAPI:
    def test_list_pending(self, client, sa_session):
        create_test_pending_job(sa_session)
        r = client.get("/api/pending")
        assert r.status_code == 200

    def test_create_pending(self, client):
        r = client.post("/api/pending", json={"url": "https://example.com/new-pending", "source": "api_test"})
        assert r.status_code == 200

    def test_get_pending(self, client, sa_session):
        item = create_test_pending_job(sa_session, url="https://example.com/get-pending")
        r = client.get(f"/api/pending/{item.id}")
        assert r.status_code == 200

    def test_get_pending_not_found(self, client):
        r = client.get("/api/pending/99999")
        assert r.status_code == 404

    def test_cancel_pending(self, client, sa_session):
        item = create_test_pending_job(sa_session, url="https://example.com/cancel-pending")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.cancel_job = MagicMock(return_value=True)
            r = client.delete(f"/api/pending/{item.id}")
            assert r.status_code == 200

    def test_reset_pending(self, client, sa_session):
        item = create_test_pending_job(sa_session, url="https://example.com/reset-pending")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.reset_job = MagicMock(return_value=True)
            r = client.post(f"/api/pending/{item.id}/reset")
            assert r.status_code == 200

    def test_queue_all(self, client, sa_session):
        create_test_pending_job(sa_session, url="https://example.com/queueall1")
        r = client.post("/api/pending/queue-all")
        assert r.status_code == 200

    def test_process_pending(self, client, sa_session):
        item = create_test_pending_job(sa_session, url="https://example.com/process-pending")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post(f"/api/pending/{item.id}/process")
            assert r.status_code == 200


# ── PENDING COMPANIES ─────────────────────────────────────────────

class TestPendingCompaniesAPI:
    def test_list_pending_companies(self, client, sa_session):
        create_test_pending_company(sa_session)
        r = client.get("/api/pending-companies")
        assert r.status_code == 200

    def test_create_pending_company(self, client):
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post("/api/pending-companies", json={"input_text": "NewPendingComp", "input_type": "text"})
            assert r.status_code == 200

    def test_get_pending_company(self, client, sa_session):
        item = create_test_pending_company(sa_session, "GetPendingComp")
        r = client.get(f"/api/pending-companies/{item.id}")
        assert r.status_code == 200

    def test_get_pending_company_not_found(self, client):
        r = client.get("/api/pending-companies/99999")
        assert r.status_code == 404

    def test_cancel_pending_company(self, client, sa_session):
        item = create_test_pending_company(sa_session, "CancelPendingComp")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.cancel_job = MagicMock(return_value=True)
            r = client.delete(f"/api/pending-companies/{item.id}")
            assert r.status_code == 200

    def test_add_notes(self, client, sa_session):
        item = create_test_pending_company(sa_session, "NotesPendingComp")
        r = client.post(f"/api/pending-companies/{item.id}/notes", json={"note": "Test note"})
        assert r.status_code == 200

    def test_add_notes_not_found(self, client):
        r = client.post("/api/pending-companies/99999/notes", json={"note": "X"})
        assert r.status_code == 404

    def test_add_links(self, client, sa_session):
        item = create_test_pending_company(sa_session, "LinksPendingComp")
        r = client.post(f"/api/pending-companies/{item.id}/links", json={"links": [{"url": "https://test.com"}]})
        assert r.status_code == 200

    def test_add_links_not_found(self, client):
        r = client.post("/api/pending-companies/99999/links", json={"links": []})
        assert r.status_code == 404

    def test_queue_all(self, client, sa_session):
        create_test_pending_company(sa_session, "QueueAllComp")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue_bulk = MagicMock()
            r = client.post("/api/pending-companies/queue-all")
            assert r.status_code == 200

    def test_process_pending_company(self, client, sa_session):
        item = create_test_pending_company(sa_session, "ProcessPendingComp")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post(f"/api/pending-companies/{item.id}/process")
            assert r.status_code == 200


# ── RESUMES ───────────────────────────────────────────────────────

class TestResumesAPI:
    def test_list_resumes(self, client, sa_session):
        create_test_resume(sa_session)
        r = client.get("/api/resumes")
        assert r.status_code == 200

    def test_get_active_generations(self, client):
        r = client.get("/api/resumes/active-generations")
        assert r.status_code == 200

    def test_get_resume(self, client, sa_session):
        create_test_resume(sa_session, "resume_get_test")
        r = client.get("/api/resumes/resume_get_test")
        assert r.status_code == 200

    def test_get_resume_not_found(self, client):
        r = client.get("/api/resumes/nonexistent")
        assert r.status_code == 404

    def test_create_resume(self, client):
        r = client.post("/api/resumes", json={"title": "New Resume", "content": "Test"})
        assert r.status_code == 200

    def test_update_resume(self, client, sa_session):
        create_test_resume(sa_session, "resume_upd_test")
        r = client.put("/api/resumes/resume_upd_test", json={"title": "Updated"})
        assert r.status_code == 200

    def test_update_resume_not_found(self, client):
        r = client.put("/api/resumes/nonexistent", json={"title": "X"})
        assert r.status_code == 404

    def test_delete_resume(self, client, sa_session):
        create_test_resume(sa_session, "resume_del_test")
        r = client.delete("/api/resumes/resume_del_test")
        assert r.status_code == 200

    def test_generate_cover(self, client):
        r = client.post("/api/resumes/resume_x/generate-cover", json={"job_num": 9001})
        assert r.status_code == 200


# ── SKILL ROADMAPS ────────────────────────────────────────────────

class TestSkillRoadmapsAPI:
    def test_list_roadmaps(self, client, sa_session):
        create_test_roadmap(sa_session)
        r = client.get("/api/skill-roadmaps")
        assert r.status_code == 200

    def test_list_roadmaps_by_skill(self, client, sa_session):
        create_test_roadmap(sa_session, "PythonRoadmap_API")
        r = client.get("/api/skill-roadmaps?skill=PythonRoadmap_API")
        assert r.status_code == 200

    def test_get_roadmap_job_progress(self, client):
        r = client.get("/api/skill-roadmaps/progress")
        assert r.status_code == 200

    def test_get_roadmap_job_progress_by_skill(self, client):
        r = client.get("/api/skill-roadmaps/progress?skill=Python")
        assert r.status_code == 200

    def test_get_roadmap_jobs(self, client):
        r = client.get("/api/skill-roadmaps/jobs")
        assert r.status_code == 200

    def test_get_all_progress(self, client):
        r = client.get("/api/skill-roadmaps/progress/all")
        assert r.status_code == 200

    def test_get_roadmap(self, client, sa_session):
        rm = create_test_roadmap(sa_session)
        r = client.get(f"/api/skill-roadmaps/{rm.id}")
        assert r.status_code == 200

    def test_get_roadmap_not_found(self, client):
        r = client.get("/api/skill-roadmaps/99999")
        assert r.status_code == 404

    def test_generate_roadmap(self, client):
        with patch('skills.presentation.api.skill_roadmaps_router.get_task_manager') as mock:
            mock.return_value.run = AsyncMock()
            r = client.post("/api/skill-roadmaps/generate", json={"skill_name": "Python"})
            assert r.status_code == 200

    def test_extend_roadmap(self, client):
        with patch('skills.presentation.api.skill_roadmaps_router.get_task_manager') as mock:
            mock.return_value.run = AsyncMock()
            r = client.post("/api/skill-roadmaps/extend", json={"skill_name": "Python"})
            assert r.status_code == 200

    def test_finegrain_roadmap(self, client):
        with patch('skills.presentation.api.skill_roadmaps_router.get_task_manager') as mock:
            mock.return_value.run = AsyncMock()
            r = client.post("/api/skill-roadmaps/finegrain", json={"skill_name": "Python"})
            assert r.status_code == 200

    def test_cancel_roadmap(self, client):
        with patch('skills.presentation.api.skill_roadmaps_router.get_task_manager') as mock:
            mock.return_value.cancel = MagicMock()
            r = client.post("/api/skill-roadmaps/cancel?skill=Python")
            assert r.status_code == 200


# ── RULES ─────────────────────────────────────────────────────────

class TestRulesAPI:
    def test_get_rules(self, client, sa_session):
        create_test_preference(sa_session)
        r = client.get("/api/rules")
        assert r.status_code == 200

    def test_create_rule(self, client):
        r = client.post("/api/rules", json={"category": "location", "key": "munich", "value": "true", "scope": "SHARED"})
        assert r.status_code == 200

    def test_create_rules_bulk(self, client):
        r = client.post("/api/rules", json={"rules": [
            {"category": "tech", "key": "python", "value": "required", "scope": "SHARED"},
            {"category": "tech", "key": "java", "value": "nice", "scope": "SHARED"},
        ]})
        assert r.status_code == 200

    def test_update_rule(self, client, sa_session):
        pref = create_test_preference(sa_session, key="to_update")
        r = client.put(f"/api/rules/{pref.id}", json={"value": "false"})
        assert r.status_code == 200

    def test_delete_rule(self, client, sa_session):
        pref = create_test_preference(sa_session, key="to_delete")
        r = client.delete(f"/api/rules/{pref.id}")
        assert r.status_code == 200

    def test_bulk_update_rules(self, client, sa_session):
        pref = create_test_preference(sa_session, key="bulk_upd")
        r = client.put("/api/rules", json={"rules": [{"id": pref.id, "priority": 10}]})
        assert r.status_code == 200


# ── DASHBOARD ─────────────────────────────────────────────────────

class TestDashboardAPI:
    def test_get_dashboard(self, client, sa_session):
        create_test_job(sa_session, num=9500)
        create_test_company(sa_session, "DashComp")
        create_test_skill(sa_session, "DashSkill")
        r = client.get("/api/dashboard")
        assert r.status_code == 200

    def test_get_generation_history(self, client):
        r = client.get("/api/generation-history")
        assert r.status_code == 200

    def test_get_local_history(self, client):
        r = client.get("/api/local-history?context=job&job_num=1")
        assert r.status_code == 200

    def test_get_local_history_invalid_context(self, client):
        r = client.get("/api/local-history?context=invalid")
        assert r.status_code == 200

    def test_get_local_active_count(self, client):
        r = client.get("/api/local-history/active?context=job&job_num=1")
        assert r.status_code == 200

    def test_get_cities(self, client, sa_session):
        create_test_job(sa_session, num=9501)
        r = client.get("/api/cities")
        assert r.status_code == 200


# ── ROUTER COMPAT ─────────────────────────────────────────────────

class TestRouterCompat:
    def test_summaries_compat(self, client):
        r = client.get("/api/summaries")
        assert r.status_code == 200

    def test_linkedin_compat(self, client):
        r = client.get("/api/linkedin")
        assert r.status_code == 200

    def test_tech_stack_compat(self, client, sa_session):
        create_test_skill(sa_session, "TechStack_API")
        r = client.get("/api/tech-stack")
        assert r.status_code == 200

    def test_skills_intel_dashboard(self, client, sa_session):
        create_test_insight(sa_session, "skills")
        r = client.get("/api/skills-intelligence/dashboard")
        assert r.status_code == 200

    def test_skill_roadmap_progress_all(self, client):
        r = client.get("/api/skill-roadmap-progress/all")
        assert r.status_code == 200

    def test_skill_roadmap_progress(self, client):
        r = client.get("/api/skill-roadmap-progress")
        assert r.status_code == 200

    def test_skill_roadmap_progress_by_skill(self, client):
        r = client.get("/api/skill-roadmap-progress?skill=Python")
        assert r.status_code == 200

    def test_skill_roadmap_jobs(self, client):
        r = client.get("/api/skill-roadmap-jobs")
        assert r.status_code == 200

    def test_get_skill_relationships_compat(self, client):
        r = client.get("/api/skill-relationships/Python")
        assert r.status_code == 200

    def test_create_skill_relationship_compat(self, client, sa_session):
        from skills.infrastructure.models.skill_model import SkillRelationshipModel
        import time
        unique = str(int(time.time() * 1000))[-6:]
        skill_a = f"Compat{unique}A"
        skill_b = f"Compat{unique}B"
        r = client.post("/api/skill-relationships", json={"skill_name": skill_a, "related_name": skill_b, "relation_type": "related_to"})
        assert r.status_code == 200

    def test_delete_skill_relationship_compat(self, client, sa_session):
        from skills.infrastructure.models.skill_model import SkillRelationshipModel
        rel = SkillRelationshipModel(skill_name="DelA", related_name="DelB", relation_type="related_to")
        sa_session.add(rel)
        sa_session.commit()
        r = client.delete(f"/api/skill-relationships/{rel.id}")
        assert r.status_code == 200

    def test_cancel_generation(self, client, sa_session):
        from processing.infrastructure.models.pending_model import PendingGenerationModel
        gen = PendingGenerationModel(job_num=1, type="resume", status="processing")
        sa_session.add(gen)
        sa_session.commit()
        r = client.post(f"/api/generations/{gen.id}/cancel")
        assert r.status_code == 200

    def test_cancel_generation_not_found(self, client):
        r = client.post("/api/generations/99999/cancel")
        assert r.status_code == 404

    def test_reprocess_company(self, client, sa_session):
        c = create_test_company(sa_session, "Reprocess_API")
        with patch('shared.infrastructure.config.queue.get_queue_manager') as mock_qm:
            mock_qm.return_value.enqueue = MagicMock()
            r = client.post(f"/api/companies/{c.id}/reprocess")
            assert r.status_code == 200
