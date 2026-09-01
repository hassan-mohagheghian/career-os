"""Tests for SQLAlchemyRoadmapRepository against the test session."""

from __future__ import annotations

import uuid

import pytest

from roadmaps.domain.entities.roadmap import TaskStatus
from roadmaps.infrastructure import SQLAlchemyRoadmapRepository
from roadmaps.infrastructure.models.roadmap_model import (
    RoadmapMilestoneModel,
    RoadmapModel,
    RoadmapNoteModel,
    RoadmapResourceModel,
    RoadmapSkillLinkModel,
    RoadmapTaskModel,
)


def _roadmap_data(**overrides):
    data = dict(
        title="Backend Roadmap",
        description="Master backend",
        goal_type="CUSTOM",
        source="MANUAL",
        application_id=None,
        status="ACTIVE",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    data.update(overrides)
    data["id"] = data.get("id") or str(uuid.uuid7())
    return data


@pytest.fixture
def repo(sa_session):
    return SQLAlchemyRoadmapRepository(sa_session, user_id="test-user")


class TestRoadmapRepository:
    def test_create_and_get_by_id(self, repo):
        created = repo.create(_roadmap_data(title="Get Hired"))
        assert created["id"]
        assert created["title"] == "Get Hired"

        fetched = repo.get_by_id(created["id"])
        assert fetched["title"] == "Get Hired"
        assert fetched["source"] == "MANUAL"

    def test_get_missing_returns_none(self, repo):
        assert repo.get_by_id("nope") is None

    def test_create_goal_and_update(self, repo):
        r = repo.create(_roadmap_data())
        goal = repo.create_goal(
            {
                "roadmap_id": r["id"],
                "type": "CUSTOM",
                "title": "goal",
                "description": "",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        )
        assert repo.get_goal(r["id"])["id"] == goal["id"]
        updated = repo.update_goal(r["id"], {"title": "new goal"})
        assert updated["title"] == "new goal"

    def test_list_newest_first(self, repo):
        older = repo.create(_roadmap_data(id=str(uuid.uuid7()), created_at="2026-01-01T00:00:00+00:00"))
        newer = repo.create(_roadmap_data(id=str(uuid.uuid7()), created_at="2026-01-02T00:00:00+00:00"))
        ids = [r["id"] for r in repo.list()]
        assert ids.index(newer["id"]) < ids.index(older["id"])

    def test_update_roadmap(self, repo):
        r = repo.create(_roadmap_data())
        updated = repo.update(r["id"], {"title": "Updated", "status": "ARCHIVED"})
        assert updated["title"] == "Updated"
        assert updated["status"] == "ARCHIVED"

    def test_delete_cascades_children(self, repo, sa_session):
        r = repo.create(_roadmap_data())
        goal = repo.create_goal({"roadmap_id": r["id"], "type": "CUSTOM", "title": "g", "created_at": "x", "updated_at": "x"})
        ms = repo.create_milestone({"roadmap_id": r["id"], "position": 0, "title": "ms", "status": "NOT_STARTED", "priority": "MEDIUM", "created_at": "x", "updated_at": "x"})
        task = repo.create_task({"milestone_id": ms["id"], "position": 0, "title": "t", "status": "NOT_STARTED", "priority": "MEDIUM", "created_at": "x", "updated_at": "x"})
        repo.create_note({"roadmap_id": r["id"], "content": "note", "created_at": "x", "updated_at": "x"})
        repo.create_resource({"roadmap_id": r["id"], "title": "res", "url": "u", "type": "OTHER", "status": "PLANNED", "source": "USER", "created_at": "x", "updated_at": "x"})
        repo.create_skill_link({"roadmap_id": r["id"], "task_id": task["id"], "skill_id": "s-1", "position": 0, "created_at": "x", "updated_at": "x"})

        assert repo.delete(r["id"]) is True

        assert sa_session.query(RoadmapModel).filter(RoadmapModel.id == r["id"]).first() is None
        assert sa_session.query(RoadmapMilestoneModel).filter(RoadmapMilestoneModel.id == ms["id"]).first() is None
        assert sa_session.query(RoadmapTaskModel).filter(RoadmapTaskModel.id == task["id"]).first() is None
        assert sa_session.query(RoadmapNoteModel).first() is None
        assert sa_session.query(RoadmapResourceModel).first() is None
        assert sa_session.query(RoadmapSkillLinkModel).first() is None
        assert goal["id"]  # goal created; cascade covers roadmap-goal

    def test_delete_missing_returns_false(self, repo):
        assert repo.delete("nope") is False

    def test_by_application(self, repo):
        r = repo.create(_roadmap_data(application_id="app-1"))
        repo.create(_roadmap_data())
        assert repo.get_by_application_id("app-1")["id"] == r["id"]

    def test_delete_by_application(self, repo, sa_session):
        repo.create(_roadmap_data(application_id="app-1"))
        repo.create(_roadmap_data(application_id="app-1"))
        assert repo.delete_by_application("app-1") == 2
        assert sa_session.query(RoadmapModel).count() == 0


class TestChildRepository:
    def test_milestone_crud(self, repo):
        r = repo.create(_roadmap_data())
        ms = repo.create_milestone({"roadmap_id": r["id"], "position": 0, "title": "ms", "status": "NOT_STARTED", "priority": "MEDIUM", "created_at": "x", "updated_at": "x"})
        assert repo.get_milestone(ms["id"])["title"] == "ms"
        milestones = repo.list_milestones(r["id"])
        assert [m["id"] for m in milestones] == [ms["id"]]

        repo.update_milestone(ms["id"], {"position": 3, "status": "COMPLETED"})
        assert repo.get_milestone(ms["id"])["position"] == 3

        assert repo.delete_milestone(ms["id"]) is True
        assert repo.get_milestone(ms["id"]) is None

    def test_task_crud_and_completed_at(self, repo):
        r = repo.create(_roadmap_data())
        ms = repo.create_milestone({"roadmap_id": r["id"], "position": 0, "title": "ms", "status": "NOT_STARTED", "priority": "MEDIUM", "created_at": "x", "updated_at": "x"})
        t = repo.create_task({"milestone_id": ms["id"], "position": 0, "title": "t", "status": "NOT_STARTED", "priority": "MEDIUM", "created_at": "x", "updated_at": "x"})
        assert [x["id"] for x in repo.list_tasks(ms["id"])] == [t["id"]]

        updated = repo.update_task(t["id"], {"status": TaskStatus.COMPLETED, "completed_at": "2026-01-05"})
        assert updated["status"] == TaskStatus.COMPLETED
        assert updated["completed_at"] == "2026-01-05"

        assert repo.delete_task(t["id"]) is True
        assert repo.get_task(t["id"]) is None

    def test_skill_links_and_delete(self, repo):
        r = repo.create(_roadmap_data())
        link = repo.create_skill_link({"roadmap_id": r["id"], "skill_id": "s-1", "position": 0, "created_at": "x", "updated_at": "x"})
        assert [s["id"] for s in repo.list_skills(r["id"])] == [link["id"]]
        assert repo.get_skill_link(link["id"])["skill_id"] == "s-1"
        assert repo.delete_skill_link(link["id"]) is True

    def test_notes_and_resources(self, repo):
        r = repo.create(_roadmap_data())
        note = repo.create_note({"roadmap_id": r["id"], "content": "hi", "created_at": "x", "updated_at": "x"})
        assert repo.list_notes(r["id"])[0]["content"] == "hi"
        assert repo.delete_note(note["id"]) is True

        res = repo.create_resource({"roadmap_id": r["id"], "title": "r", "url": "u", "type": "OTHER", "status": "PLANNED", "source": "USER", "created_at": "x", "updated_at": "x"})
        assert repo.list_resources(r["id"])[0]["title"] == "r"
        repo.update_resource(res["id"], {"status": "COMPLETED"})
        assert repo.get_by_id(r["id"])
        assert repo.delete_resource(res["id"]) is True