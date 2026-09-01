"""Tests for the Roadmaps API router."""

from __future__ import annotations

import uuid

from roadmaps.infrastructure.models.roadmap_model import RoadmapModel


def _create_roadmap(client, **kwargs) -> dict:
    body = {"title": "Backend Roadmap", "description": "Deep dive"}
    body.update(kwargs)
    resp = client.post("/api/roadmaps", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_milestone(client, roadmap_id: str, **kwargs) -> dict:
    body = {"title": "Milestone", "description": "desc", "priority": "HIGH"}
    body.update(kwargs)
    resp = client.post(f"/api/roadmaps/{roadmap_id}/milestones", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_task(client, milestone_id: str, **kwargs) -> dict:
    body = {"title": "Task", "description": "desc"}
    body.update(kwargs)
    resp = client.post(f"/api/roadmaps/milestones/{milestone_id}/tasks", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestRoadmapCRUD:
    def test_create_roadmap_returns_detail(self, client):
        body = _create_roadmap(client, goal={"type": "CUSTOM", "title": "Goal"})
        assert body["title"] == "Backend Roadmap"
        assert body["source"] == "MANUAL"
        assert body["goal"]["type"] == "CUSTOM"
        assert body["milestones"] == []
        assert body["progress"]["overall_percent"] == 0

    def test_list_roadmaps(self, client):
        _create_roadmap(client, title="One")
        _create_roadmap(client, title="Two")
        resp = client.get("/api/roadmaps")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_get_roadmap_by_id(self, client):
        created = _create_roadmap(client)
        resp = client.get(f"/api/roadmaps/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_missing_roadmap_404(self, client):
        resp = client.get("/api/roadmaps/missing")
        assert resp.status_code == 404

    def test_by_application(self, client):
        resp = client.post(
            "/api/roadmaps",
            json={"title": "Prep", "goal": {"type": "JOB", "application_id": None}},
        )
        assert resp.status_code == 201
        roadmap_id = resp.json()["id"]
        # application_id is not settable via manual create; use repo-level lookup path
        _ = roadmap_id
        resp404 = client.get("/api/roadmaps/by-application/some-app")
        assert resp404.status_code == 404

    def test_by_application_found(self, client, sa_session):
        roadmap = RoadmapModel(
            id=str(uuid.uuid7()),
            title="App roadmap",
            application_id="app-1",
            source="APPLICATION",
            user_id="test-user",
        )
        sa_session.add(roadmap)
        sa_session.commit()
        resp = client.get("/api/roadmaps/by-application/app-1")
        assert resp.status_code == 200
        assert resp.json()["application_id"] == "app-1"

    def test_update_roadmap(self, client):
        created = _create_roadmap(client)
        resp = client.patch(f"/api/roadmaps/{created['id']}", json={"title": "New Title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_update_invalid_status_422(self, client):
        created = _create_roadmap(client)
        resp = client.patch(f"/api/roadmaps/{created['id']}", json={"status": "bogus"})
        assert resp.status_code == 422

    def test_delete_roadmap(self, client, sa_session):
        created = _create_roadmap(client)
        resp = client.delete(f"/api/roadmaps/{created['id']}")
        assert resp.status_code == 200
        sa_session.expire_all()
        assert sa_session.query(RoadmapModel).filter(RoadmapModel.id == created["id"]).first() is None

    def test_delete_missing_404(self, client):
        resp = client.delete("/api/roadmaps/missing")
        assert resp.status_code == 404


class TestMilestoneTaskAPI:
    def test_add_milestone_and_list_in_detail(self, client):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        assert ms["priority"] == "HIGH"

        detail = client.get(f"/api/roadmaps/{roadmap['id']}").json()
        assert detail["milestones"][0]["id"] == ms["id"]

    def test_add_milestone_missing_roadmap_404(self, client):
        resp = client.post("/api/roadmaps/missing/milestones", json={"title": "m"})
        assert resp.status_code == 404

    def test_update_and_delete_milestone(self, client, sa_session):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        updated = client.patch(f"/api/roadmaps/milestones/{ms['id']}", json={"status": "COMPLETED"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "COMPLETED"

        deleted = client.delete(f"/api/roadmaps/milestones/{ms['id']}")
        assert deleted.status_code == 200

    def test_add_task_and_progress(self, client):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        task = _create_task(client, ms["id"])
        assert task["position"] == 0

        def _progress():
            return client.get(f"/api/roadmaps/{roadmap['id']}").json()["progress"]

        assert _progress()["overall_percent"] == 0
        client.patch(f"/api/roadmaps/tasks/{task['id']}", json={"status": "COMPLETED"})
        assert _progress()["overall_percent"] == 100

    def test_update_task_priority(self, client):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        task = _create_task(client, ms["id"])
        resp = client.patch(
            f"/api/roadmaps/tasks/{task['id']}",
            json={"priority": "CRITICAL", "estimated_effort": "4h"},
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "CRITICAL"
        assert resp.json()["estimated_effort"] == "4h"

    def test_delete_task(self, client, sa_session):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        task = _create_task(client, ms["id"])
        resp = client.delete(f"/api/roadmaps/tasks/{task['id']}")
        assert resp.status_code == 200
        detail = client.get(f"/api/roadmaps/{roadmap['id']}").json()
        assert detail["milestones"][0]["tasks"] == []


class TestNotesResourcesAPI:
    def test_add_and_delete_note(self, client):
        roadmap = _create_roadmap(client)
        resp = client.post(f"/api/roadmaps/{roadmap['id']}/notes", json={"content": "Remember"})
        assert resp.status_code == 201
        note_id = resp.json()["id"]

        detail = client.get(f"/api/roadmaps/{roadmap['id']}").json()
        assert detail["notes"][0]["content"] == "Remember"

        deleted = client.delete(f"/api/roadmaps/notes/{note_id}")
        assert deleted.status_code == 200

    def test_add_note_empty_422(self, client):
        roadmap = _create_roadmap(client)
        resp = client.post(f"/api/roadmaps/{roadmap['id']}/notes", json={"content": " "})
        assert resp.status_code == 422

    def test_resource_crud(self, client):
        roadmap = _create_roadmap(client)
        resp = client.post(
            f"/api/roadmaps/{roadmap['id']}/resources",
            json={"title": "Grokking", "url": "https://example.com", "type": "BOOK"},
        )
        assert resp.status_code == 201
        res = resp.json()
        assert res["status"] == "PLANNED"

        updated = client.patch(f"/api/roadmaps/resources/{res['id']}", json={"status": "COMPLETED"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "COMPLETED"

        deleted = client.delete(f"/api/roadmaps/resources/{res['id']}")
        assert deleted.status_code == 200


class TestSkillLinkAPI:
    def test_link_skill_resolves_by_name(self, client):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        resp = client.post(
            "/api/roadmaps/skills",
            json={"skill_name": "python", "milestone_id": ms["id"]},
        )
        assert resp.status_code == 201
        link = resp.json()
        assert link["skill_id"]

    def test_link_skill_to_task(self, client):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        task = _create_task(client, ms["id"])
        resp = client.post(
            "/api/roadmaps/skills",
            json={"skill_name": "kubernetes", "task_id": task["id"]},
        )
        assert resp.status_code == 201

    def test_link_skill_requires_node(self, client):
        resp = client.post("/api/roadmaps/skills", json={"skill_name": "python"})
        assert resp.status_code == 400

    def test_unlink_skill(self, client, sa_session):
        roadmap = _create_roadmap(client)
        ms = _create_milestone(client, roadmap["id"])
        link = client.post(
            "/api/roadmaps/skills",
            json={"skill_name": "go", "milestone_id": ms["id"]},
        ).json()
        resp = client.delete(f"/api/roadmaps/skills/{link['id']}")
        assert resp.status_code == 200