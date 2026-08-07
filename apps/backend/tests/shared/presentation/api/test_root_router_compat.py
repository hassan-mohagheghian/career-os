"""Coverage tests for the inline compat routes in shared/presentation/api/root_router.py.

These routes live at the bottom of root_router.py (after the include_router calls)
and are mounted under the /api prefix. They are tested through the ``client``
fixture from tests/conftest.py, which wires a real SQLAlchemy test session.

Compat routes that call ``get_session_sync()`` directly (rather than via FastAPI DI)
are pointed at the test session by patching ``root_router.get_session_sync``.
"""

from unittest.mock import patch

import pytest

from jobs.infrastructure.models.job_model import JobModel
from companies.infrastructure.models.company_model import CompanyModel
from skills.infrastructure.models.skill_model import SkillModel, SkillRelationshipModel
from jobs.infrastructure.models.misc_models import SummaryModel
from skills.infrastructure.models.skill_roadmap_models import (
    SkillRoadmapModel,
    SkillRoadmapProgressModel,
    SkillRoadmapJobModel,
)
from shared.presentation.api import root_router as root_router_module


@pytest.fixture(autouse=True)
def _patch_get_session_sync(sa_session, monkeypatch):
    """Route the compat routes' direct get_session_sync() calls at the test DB."""
    monkeypatch.setattr(root_router_module, "get_session_sync", lambda: sa_session)


def _mark_all_jobs_processed(sa_session):
    sa_session.query(JobModel).filter(JobModel.status != "processed").update(
        {"status": "processed"}
    )
    sa_session.commit()


def _mark_all_companies_processed(sa_session):
    sa_session.query(CompanyModel).filter(CompanyModel.status != "processed").update(
        {"status": "processed"}
    )
    sa_session.commit()


def _seed_company(sa_session, name="Co"):
    co = CompanyModel(name=name)
    sa_session.add(co)
    sa_session.commit()
    return co.id


def _seed_roadmap(sa_session, skill_name, completed=0, title="Basics"):
    rm = SkillRoadmapModel(skill_name=skill_name, title=title)
    sa_session.add(rm)
    sa_session.commit()
    sa_session.add(
        SkillRoadmapProgressModel(roadmap_id=rm.id, skill_name=skill_name, completed=completed)
    )
    sa_session.commit()
    return rm.id


# ── summaries / tech-stack ──────────────────────────────────────


def test_summaries_compat(client, sa_session):
    sa_session.add(SummaryModel(job_id="job-901", company="SummaryCo", score="A"))
    sa_session.commit()
    resp = client.get("/api/summaries")
    assert resp.status_code == 200
    assert any(r["job_id"] == "job-901" and r["company"] == "SummaryCo" for r in resp.json())


def test_tech_stack_compat(client, sa_session):
    sa_session.add(SkillModel(name="TechStackPy", hidden=0))
    sa_session.add(SkillModel(name="HiddenSkill", hidden=1))
    sa_session.commit()
    resp = client.get("/api/tech-stack")
    assert resp.status_code == 200
    names = {r["name"] for r in resp.json()}
    assert "TechStackPy" in names
    assert "HiddenSkill" not in names


# ── skill roadmap progress ──────────────────────────────────────


def test_skill_roadmap_progress_all(client, sa_session):
    rm1 = SkillRoadmapModel(skill_name="AggroAll", title="T1")
    rm2 = SkillRoadmapModel(skill_name="AggroAll", title="T2")
    sa_session.add_all([rm1, rm2])
    sa_session.commit()
    rid1 = rm1.id
    sa_session.add(
        SkillRoadmapProgressModel(roadmap_id=rid1, skill_name="AggroAll", completed=1)
    )
    sa_session.commit()
    resp = client.get("/api/skill-roadmap-progress/all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["AggroAll"] == {"total": 2, "completed": 1, "pct": 50, "checked": {str(rid1): 1}}


def test_skill_roadmap_progress_compat_with_skill(client, sa_session):
    rid = _seed_roadmap(sa_session, "GetBySkill", completed=1)
    resp = client.get("/api/skill-roadmap-progress?skill=GetBySkill")
    assert resp.status_code == 200
    assert resp.json() == {str(rid): 1}


def test_skill_roadmap_progress_compat_without_skill(client, sa_session):
    _seed_roadmap(sa_session, "CompatAll", completed=1)
    resp = client.get("/api/skill-roadmap-progress")
    assert resp.status_code == 200
    assert "CompatAll" in resp.json()


def test_toggle_roadmap_progress(client, sa_session):
    rid = _seed_roadmap(sa_session, "TogglePy", completed=0)
    resp = client.patch(f"/api/skill-roadmap-progress/{rid}", json={})
    assert resp.status_code == 200
    assert resp.json()["completed"] == 1


def test_update_roadmap_progress(client, sa_session):
    rid = _seed_roadmap(sa_session, "UpdatePy", completed=0)
    resp = client.put(f"/api/skill-roadmap-progress/{rid}", json={"completed": True})
    assert resp.status_code == 200
    assert resp.json()["completed"] == 1
    resp = client.put(f"/api/skill-roadmap-progress/{rid}", json={"completed": False})
    assert resp.status_code == 200
    assert resp.json()["completed"] == 0
    resp = client.put(f"/api/skill-roadmap-progress/{rid}", json={})
    assert resp.status_code == 200
    assert resp.json()["completed"] == 0


def test_skill_roadmap_jobs_compat(client, sa_session):
    sa_session.add(SkillRoadmapJobModel(skill_name="RoadmapJobs", status="queued"))
    sa_session.commit()
    resp = client.get("/api/skill-roadmap-jobs")
    assert resp.status_code == 200
    assert any(i["skill_name"] == "RoadmapJobs" for i in resp.json()["items"])


# ── skill relationships ─────────────────────────────────────────


def test_get_skill_relationships_compat(client, sa_session):
    sa_session.add(
        SkillRelationshipModel(
            skill_name="RelReact", related_name="ReactJS", relation_type="similar"
        )
    )
    sa_session.commit()
    resp = client.get("/api/skill-relationships/RelReact")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_create_skill_relationship_compat(client, sa_session):
    resp = client.post(
        "/api/skill-relationships",
        json={"skill_name": "RelPython", "related_name": "Py", "relation_type": "similar"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "created"}


def test_create_skill_relationship_compat_conflict(client, sa_session):
    body = {"skill_name": "RelDup", "related_name": "Dup", "relation_type": "similar"}
    assert client.post("/api/skill-relationships", json=body).status_code == 200
    resp = client.post("/api/skill-relationships", json=body)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


def test_delete_skill_relationship_compat(client, sa_session):
    rel = SkillRelationshipModel(
        skill_name="RelDel", related_name="Del", relation_type="similar"
    )
    sa_session.add(rel)
    sa_session.commit()
    resp = client.delete(f"/api/skill-relationships/{rel.id}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "deleted"}


# ── job-company link / company reprocess ────────────────────────


def test_link_job_to_company_with_company_id(client, sa_session):
    sa_session.add(JobModel(id="job-501", url="https://example.com/link1", company="Co"))
    sa_session.commit()
    co_id = _seed_company(sa_session, name="LinkedCo")
    resp = client.post("/api/jobs/job-501/link-company", json={"company_id": co_id})
    assert resp.status_code == 200
    assert resp.json() == {"status": "linked"}
    job = sa_session.query(JobModel).filter(JobModel.id == "job-501").first()
    assert job.company_id == co_id


def test_link_job_to_company_without_company_id(client, sa_session):
    sa_session.add(JobModel(id="job-502", url="https://example.com/link2", company="Co"))
    sa_session.commit()
    resp = client.post("/api/jobs/job-502/link-company", json={"company_id": None})
    assert resp.status_code == 200
    assert resp.json() == {"status": "linked"}


def test_reprocess_company_found(client, sa_session):
    co_id = _seed_company(sa_session, name="ReproCo")
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync"),
    ):
        resp = client.post(f"/api/companies/{co_id}/reprocess")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    assert "execution_id" in data
    enqueue.assert_called_once_with(data["execution_id"])


def test_reprocess_company_not_found(client, sa_session):
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync"),
    ):
        resp = client.post("/api/companies/999999999/reprocess")
    assert resp.status_code == 200
    assert resp.json() == {"error": "Not found"}
    enqueue.assert_not_called()


# ── company intake ──────────────────────────────────────────────


def test_create_company_queue_default(client, sa_session):
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync"),
    ):
        resp = client.post(
            "/api/companies",
            json={
                "name": "Acme GmbH",
                "notes": [{"type": "text", "content": "Berlin product company"}],
                "links": [{"url": "https://acme.example", "title": "Website"}],
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme GmbH"
    assert data["status"] == "queued"
    assert "execution_id" in data
    enqueue.assert_called_once_with(data["execution_id"])

    from companies.infrastructure.models.company_model import CompanyModel
    company = sa_session.query(CompanyModel).filter(CompanyModel.id == data["id"]).first()
    assert company is not None
    assert "Berlin product company" in company.notes
    assert "https://acme.example" in company.notes


def test_create_company_without_queue(client, sa_session):
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync"),
    ):
        resp = client.post(
            "/api/companies",
            json={"name": "IdleCo", "notes": [], "links": [], "queue": False},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "IdleCo"
    assert data["status"] == "created"
    assert "execution_id" not in data
    enqueue.assert_not_called()


def test_create_company_empty_body(client, sa_session):
    with (
        patch("shared.infrastructure.taskiq.client.enqueue_execution_sync") as enqueue,
        patch("shared.infrastructure.events.processing_events.publish_sync"),
    ):
        resp = client.post("/api/companies", json={})
    assert resp.status_code == 201
    assert resp.json()["status"] == "queued"
    enqueue.assert_called_once()
