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
from shared.infrastructure.database.models.misc_models import (
    SummaryModel,
    ResumeModel,
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


# ── summaries / linkedin / tech-stack ───────────────────────────


def test_summaries_compat(client, sa_session):
    sa_session.add(SummaryModel(job_id="job-901", company="SummaryCo", score="A"))
    sa_session.commit()
    resp = client.get("/api/summaries")
    assert resp.status_code == 200
    assert any(r["job_id"] == "job-901" and r["company"] == "SummaryCo" for r in resp.json())


def test_linkedin_compat(client, sa_session):
    sa_session.add_all(
        [
            ResumeModel(id="original", title="Original"),
            ResumeModel(id="linkedin_1", title="LinkedIn"),
            ResumeModel(id="cover_2", title="Cover"),
        ]
    )
    sa_session.commit()
    resp = client.get("/api/linkedin")
    assert resp.status_code == 200
    assert {r["id"] for r in resp.json()} == {"linkedin_1"}


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
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post(f"/api/companies/{co_id}/reprocess")
    assert resp.status_code == 200
    assert resp.json() == {"status": "queued"}
    mock_enq.assert_called_once_with(co_id)


def test_reprocess_company_not_found(client, sa_session):
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post("/api/companies/999999999/reprocess")
    assert resp.status_code == 200
    assert resp.json() == {"error": "Not found"}
    mock_enq.assert_not_called()


# ── pending companies ───────────────────────────────────────────


def test_list_pending_companies(client, sa_session):
    _mark_all_companies_processed(sa_session)
    sa_session.add(CompanyModel(name="PendingCo1", status="created"))
    sa_session.add(CompanyModel(name="PendingCo2", status="processed"))
    sa_session.commit()
    resp = client.get("/api/pending-companies")
    assert resp.status_code == 200
    assert [r["name"] for r in resp.json()] == ["PendingCo1"]


def test_create_pending_company_fallback(client, sa_session):
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post(
            "/api/pending-companies",
            json={
                "notes": [{"type": "text", "content": "First note"}, "plain"],
                "links": [{"url": "https://a.example.com", "title": "A"}, "https://b.example.com"],
                "name": "",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "created"
    mock_enq.assert_called_once()
    assert mock_enq.call_args.args[0] == data["id"]


def test_create_pending_company_with_input_text(client, sa_session):
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post(
            "/api/pending-companies",
            json={"input_text": "https://input.example.com", "notes": [], "links": []},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"
    mock_enq.assert_called_once()


def test_create_pending_company_empty_body(client, sa_session):
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post("/api/pending-companies", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"
    mock_enq.assert_called_once()


def test_queue_all_pending_companies_empty(client, sa_session):
    _mark_all_companies_processed(sa_session)
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post("/api/pending-companies/queue-all")
    assert resp.status_code == 200
    assert resp.json() == {"status": "queued", "count": 0}
    mock_enq.assert_not_called()


def test_queue_all_pending_companies_with_items(client, sa_session):
    _mark_all_companies_processed(sa_session)
    co1 = CompanyModel(name="QCo1", status="created")
    co2 = CompanyModel(name="QCo2", status="created")
    sa_session.add_all([co1, co2])
    sa_session.commit()
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post("/api/pending-companies/queue-all")
    assert resp.status_code == 200
    assert resp.json() == {"status": "queued", "count": 2}
    assert {c.args[0] for c in mock_enq.call_args_list} == {co1.id, co2.id}


def test_get_pending_company_found(client, sa_session):
    co_id = _seed_company(sa_session, name="GetPendCo")
    resp = client.get(f"/api/pending-companies/{co_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == co_id


def test_get_pending_company_not_found(client, sa_session):
    resp = client.get("/api/pending-companies/999999998")
    assert resp.status_code == 404
    assert resp.json() == {"error": "Not found"}


def test_delete_pending_company_found(client, sa_session):
    co_id = _seed_company(sa_session, name="DelPendCo")
    resp = client.delete(f"/api/pending-companies/{co_id}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "deleted"}


def test_delete_pending_company_not_found(client, sa_session):
    resp = client.delete("/api/pending-companies/999999997")
    assert resp.status_code == 404
    assert resp.json() == {"error": "Not found"}


def test_add_pending_company_notes(client, sa_session):
    co_id = _seed_company(sa_session, name="NotesCo")
    resp = client.post(f"/api/pending-companies/{co_id}/notes", json={"notes": ["n1", "n2"]})
    assert resp.status_code == 200
    assert resp.json() == {"status": "updated", "notes": ["n1", "n2"]}
    co = sa_session.query(CompanyModel).filter(CompanyModel.id == co_id).first()
    assert co.notes == '["n1", "n2"]'


def test_add_pending_company_notes_not_found(client, sa_session):
    resp = client.post("/api/pending-companies/999999996/notes", json={"notes": ["n1"]})
    assert resp.status_code == 404
    assert resp.json() == {"error": "Not found"}


def test_add_pending_company_links(client, sa_session):
    co_id = _seed_company(sa_session, name="LinksCo")
    resp = client.post(
        f"/api/pending-companies/{co_id}/links",
        json={"links": ["https://l1.example.com"]},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "updated", "links": ["https://l1.example.com"]}
    co = sa_session.query(CompanyModel).filter(CompanyModel.id == co_id).first()
    assert co.notes == '["https://l1.example.com"]'


def test_add_pending_company_links_not_found(client, sa_session):
    resp = client.post("/api/pending-companies/999999995/links", json={"links": ["https://x"]})
    assert resp.status_code == 404
    assert resp.json() == {"error": "Not found"}


def test_process_pending_company(client, sa_session):
    co_id = _seed_company(sa_session, name="ProcPendCo")
    with patch("shared.infrastructure.taskiq.client.enqueue_company_sync") as mock_enq:
        resp = client.post(f"/api/pending-companies/{co_id}/process")
    assert resp.status_code == 200
    assert resp.json() == {"status": "queued"}
    mock_enq.assert_called_once_with(co_id)


# ── resumes ─────────────────────────────────────────────────────


def test_active_generations_compat(client, sa_session):
    # The /api/resumes/active-generations path is shadowed by resumes_router's
    # GET /active-generations, so call the compat route function directly.
    assert root_router_module.active_generations_compat(sa_session) == []
