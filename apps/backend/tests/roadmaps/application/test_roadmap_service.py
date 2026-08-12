"""Tests for RoadmapService (manual CRUD, progress, events)."""

from __future__ import annotations

import pytest

from roadmaps.application.services.roadmap_service import RoadmapService
from roadmaps.domain.entities.roadmap import (
    GoalType,
    MilestoneStatus,
    NodePriority,
    RoadmapSource,
    RoadmapStatus,
    TaskStatus,
)
from roadmaps.domain.events import (
    RoadmapCreated,
    RoadmapDeleted,
    RoadmapMilestoneAdded,
    RoadmapMilestoneDeleted,
    RoadmapMilestoneUpdated,
    RoadmapNoteAdded,
    RoadmapResourceAdded,
    RoadmapSkillLinked,
    RoadmapTaskAdded,
    RoadmapTaskDeleted,
    RoadmapTaskUpdated,
    RoadmapUpdated,
)
from shared.application.exceptions import NotFoundError, ValidationError


class FakeRoadmapRepo:
    """In-memory repository mirroring the IRoadmapRepository port surface."""

    def __init__(self):
        self.roadmaps: dict[str, dict] = {}
        self.goals: dict[str, dict] = {}
        self.milestones: dict[str, dict] = {}
        self.tasks: dict[str, dict] = {}
        self.skill_links: dict[str, dict] = {}
        self.notes: dict[str, dict] = {}
        self.resources: dict[str, dict] = {}
        self._n = 0

    def _id(self, prefix):
        self._n += 1
        return f"{prefix}-{self._n}"

    def create(self, data):
        row = dict(data)
        row["id"] = self._id("roadmap")
        self.roadmaps[row["id"]] = row
        return row

    def get_by_id(self, roadmap_id):
        return self.roadmaps.get(roadmap_id)

    def get_by_application_id(self, application_id):
        return next((r for r in self.roadmaps.values() if r.get("application_id") == application_id), None)

    def list(self):
        return list(self.roadmaps.values())

    def update(self, roadmap_id, data):
        row = self.roadmaps.get(roadmap_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete(self, roadmap_id):
        return self.roadmaps.pop(roadmap_id, None) is not None

    def delete_by_application(self, application_id):
        ids = [r["id"] for r in self.roadmaps.values() if r.get("application_id") == application_id]
        for i in ids:
            self.roadmaps.pop(i, None)
        return len(ids)

    def get_goal(self, roadmap_id):
        return next((g for g in self.goals.values() if g["roadmap_id"] == roadmap_id), None)

    def create_goal(self, data):
        row = dict(data)
        row["id"] = self._id("goal")
        self.goals[row["id"]] = row
        return row

    def update_goal(self, roadmap_id, data):
        goal = self.get_goal(roadmap_id)
        if not goal:
            return None
        goal.update(data)
        return goal

    def list_milestones(self, roadmap_id):
        return [m for m in self.milestones.values() if m["roadmap_id"] == roadmap_id]

    def get_milestone(self, milestone_id):
        return self.milestones.get(milestone_id)

    def create_milestone(self, data):
        row = dict(data)
        row["id"] = self._id("milestone")
        self.milestones[row["id"]] = row
        return row

    def update_milestone(self, milestone_id, data):
        row = self.milestones.get(milestone_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete_milestone(self, milestone_id):
        return self.milestones.pop(milestone_id, None) is not None

    def list_tasks(self, milestone_id):
        return [t for t in self.tasks.values() if t["milestone_id"] == milestone_id]

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def create_task(self, data):
        row = dict(data)
        row["id"] = self._id("task")
        self.tasks[row["id"]] = row
        return row

    def update_task(self, task_id, data):
        row = self.tasks.get(task_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete_task(self, task_id):
        return self.tasks.pop(task_id, None) is not None

    def list_skills(self, roadmap_id):
        return [s for s in self.skill_links.values() if s["roadmap_id"] == roadmap_id]

    def get_skill_link(self, link_id):
        return self.skill_links.get(link_id)

    def create_skill_link(self, data):
        row = dict(data)
        row["id"] = self._id("link")
        self.skill_links[row["id"]] = row
        return row

    def delete_skill_link(self, link_id):
        return self.skill_links.pop(link_id, None) is not None

    def list_notes(self, roadmap_id):
        return [n for n in self.notes.values() if n["roadmap_id"] == roadmap_id]

    def create_note(self, data):
        row = dict(data)
        row["id"] = self._id("note")
        self.notes[row["id"]] = row
        return row

    def delete_note(self, note_id):
        return self.notes.pop(note_id, None) is not None

    def list_resources(self, roadmap_id):
        return [r for r in self.resources.values() if r["roadmap_id"] == roadmap_id]

    def create_resource(self, data):
        row = dict(data)
        row["id"] = self._id("resource")
        self.resources[row["id"]] = row
        return row

    def update_resource(self, resource_id, data):
        row = self.resources.get(resource_id)
        if not row:
            return None
        row.update(data)
        return row

    def delete_resource(self, resource_id):
        return self.resources.pop(resource_id, None) is not None


class RecordingCollector:
    def __init__(self):
        self._events = []

    def publish(self, event):
        self._events.append(event)

    @property
    def events(self):
        return list(self._events)


def _service():
    repo = FakeRoadmapRepo()
    collector = RecordingCollector()
    service = RoadmapService(repo, None, collector)
    return service, repo, collector


class TestRoadmapCRUD:
    def test_create_manual_sets_source_and_goal(self):
        service, repo, collector = _service()
        stored = service.create_manual(
            "Learn Go", "Grok concurrency", {"type": GoalType.SKILL, "title": "Go mastery"}
        )
        assert stored["source"] == RoadmapSource.MANUAL
        assert stored["status"] == RoadmapStatus.ACTIVE
        goal = repo.get_goal(stored["id"])
        assert goal["type"] == GoalType.SKILL
        assert any(isinstance(e, RoadmapCreated) and e.roadmap_id == stored["id"] for e in collector.events)

    def test_create_from_application(self):
        service, _, collector = _service()
        stored = service.create_from_application("Prep", "desc", "app-1")
        assert stored["source"] == RoadmapSource.APPLICATION
        assert stored["application_id"] == "app-1"
        event = next(e for e in collector.events if isinstance(e, RoadmapCreated))
        assert event.application_id == "app-1"

    def test_get_and_list(self):
        service, _, _ = _service()
        created = service.create_manual("Roadmap")
        assert service.get(created["id"])["title"] == "Roadmap"
        assert len(service.list()) == 1
        assert service.get("missing") is None

    def test_update_roadmap(self):
        service, _, collector = _service()
        created = service.create_manual("Old")
        updated = service.update(created["id"], {"title": "New", "status": "ARCHIVED"})
        assert updated["title"] == "New"
        assert updated["status"] == "ARCHIVED"
        assert any(isinstance(e, RoadmapUpdated) for e in collector.events)

    def test_update_missing_raises(self):
        service, _, _ = _service()
        with pytest.raises(NotFoundError):
            service.update("missing", {"title": "x"})

    def test_update_invalid_status_raises(self):
        service, _, _ = _service()
        created = service.create_manual("x")
        with pytest.raises(ValidationError):
            service.update(created["id"], {"status": "bogus"})

    def test_delete_roadmap(self):
        service, repo, collector = _service()
        created = service.create_manual("x")
        service.delete(created["id"])
        assert repo.get_by_id(created["id"]) is None
        assert any(isinstance(e, RoadmapDeleted) for e in collector.events)

    def test_delete_by_application(self):
        service, _, _ = _service()
        service.create_from_application("a", "d", "app-1")
        service.create_from_application("b", "d", "app-1")
        assert service.delete_by_application("app-1") == 2


class TestMilestoneAndTask:
    def _with_roadmap_and_milestone(self):
        service, repo, collector = _service()
        r = service.create_manual("r")
        ms = service.add_milestone(r["id"], "Milestone 1", "desc", NodePriority.HIGH)
        return service, repo, collector, r, ms

    def test_add_milestone(self):
        service, repo, collector, r, ms = self._with_roadmap_and_milestone()
        assert ms["position"] == 0
        assert ms["priority"] == NodePriority.HIGH
        assert len(repo.list_milestones(r["id"])) == 1
        assert any(isinstance(e, RoadmapMilestoneAdded) for e in collector.events)

    def test_add_milestone_missing_roadmap(self):
        service, _, _ = _service()
        with pytest.raises(NotFoundError):
            service.add_milestone("missing", "m")

    def test_update_milestone(self):
        service, _, collector, _, ms = self._with_roadmap_and_milestone()
        updated = service.update_milestone(ms["id"], {"status": MilestoneStatus.COMPLETED, "priority": "LOW"})
        assert updated["status"] == MilestoneStatus.COMPLETED
        assert updated["priority"] == "LOW"
        assert any(isinstance(e, RoadmapMilestoneUpdated) for e in collector.events)

    def test_delete_milestone(self):
        service, repo, collector, _, ms = self._with_roadmap_and_milestone()
        service.delete_milestone(ms["id"])
        assert repo.get_milestone(ms["id"]) is None
        assert any(isinstance(e, RoadmapMilestoneDeleted) for e in collector.events)

    def test_add_task_positions_append(self):
        service, _, collector, _, ms = self._with_roadmap_and_milestone()
        t1 = service.add_task(ms["id"], "Task A")
        t2 = service.add_task(ms["id"], "Task B")
        assert t1["position"] == 0
        assert t2["position"] == 1
        assert any(isinstance(e, RoadmapTaskAdded) for e in collector.events)

    def test_add_task_missing_milestone(self):
        service, _, _ = _service()
        with pytest.raises(NotFoundError):
            service.add_task("missing", "t")

    def test_complete_task_sets_completed_at(self):
        service, _, collector, _, ms = self._with_roadmap_and_milestone()
        t = service.add_task(ms["id"], "Task")
        updated = service.update_task(t["id"], {"status": TaskStatus.COMPLETED})
        assert updated["completed_at"] is not None
        assert any(
            isinstance(e, RoadmapTaskUpdated) and e.status == TaskStatus.COMPLETED for e in collector.events
        )

    def test_completed_at_cleared_when_reopened(self):
        service, _, _, _, ms = self._with_roadmap_and_milestone()
        t = service.add_task(ms["id"], "Task")
        service.update_task(t["id"], {"status": TaskStatus.COMPLETED})
        reopened = service.update_task(t["id"], {"status": TaskStatus.IN_PROGRESS})
        assert reopened["completed_at"] is None

    def test_delete_task(self):
        service, repo, collector, _, ms = self._with_roadmap_and_milestone()
        t = service.add_task(ms["id"], "Task")
        service.delete_task(t["id"])
        assert repo.get_task(t["id"]) is None
        assert any(isinstance(e, RoadmapTaskDeleted) for e in collector.events)


class TestNotesResourcesSkills:
    def test_add_and_delete_note(self):
        service, repo, collector = _service()
        r = service.create_manual("r")
        note = service.add_note(r["id"], "remember this")
        assert repo.get_by_id(r["id"])
        assert any(isinstance(e, RoadmapNoteAdded) for e in collector.events)
        service.delete_note(note["id"])
        assert service._repo.get_by_id(r["id"])

    def test_add_note_empty_rejected(self):
        service, _, _ = _service()
        r = service.create_manual("r")
        with pytest.raises(ValidationError):
            service.add_note(r["id"], "   ")

    def test_add_edit_delete_resource(self):
        service, _, collector = _service()
        r = service.create_manual("r")
        res = service.add_resource(r["id"], "Read docs", url="https://example.com", type_="DOCUMENTATION")
        assert res["status"] == "PLANNED"
        assert any(isinstance(e, RoadmapResourceAdded) for e in collector.events)
        updated = service.update_resource(res["id"], {"status": "COMPLETED"})
        assert updated["status"] == "COMPLETED"
        service.delete_resource(res["id"])

    def test_link_skill_requires_repo(self):
        service, _, _ = _service()
        r = service.create_manual("r")
        with pytest.raises(ValidationError):
            service.link_skill(r["id"], "python")

    def test_link_skill(self):
        class FakeSkillRepo:
            def resolve_skill(self, data):
                return "skill-123"

        repo = FakeRoadmapRepo()
        collector = RecordingCollector()
        service = RoadmapService(repo, FakeSkillRepo(), collector)
        r = service.create_manual("r")
        link = service.link_skill(r["id"], "python")
        assert link["skill_id"] == "skill-123"
        assert link["position"] == 0
        assert any(isinstance(e, RoadmapSkillLinked) and e.skill_id == "skill-123" for e in collector.events)

    def test_unlink_skill(self):
        repo = FakeRoadmapRepo()
        service = RoadmapService(repo, None, RecordingCollector())
        r = service.create_manual("r")
        link = repo.create_skill_link({"roadmap_id": r["id"], "skill_id": "s", "position": 0})
        service.unlink_skill(link["id"])
        assert service._repo.get_skill_link(link["id"]) is None


class TestProgress:
    def _setup(self):
        service, _, _ = _service()
        r = service.create_manual("r")
        ms1 = service.add_milestone(r["id"], "M1")
        ms2 = service.add_milestone(r["id"], "M2")
        t1 = service.add_task(ms1["id"], "T1")
        t2 = service.add_task(ms1["id"], "T2")
        service.add_task(ms2["id"], "T3")
        return service, r["id"], ms1["id"], ms2["id"], t1["id"], t2["id"]

    def test_progress_starts_zero(self):
        service, rid, *_ = self._setup()
        progress = service.compute_progress(rid)
        assert progress["total_tasks"] == 3
        assert progress["completed_tasks"] == 0
        assert progress["overall_percent"] == 0

    def test_progress_partial(self):
        service, rid, _, _, t1, _ = self._setup()
        service.update_task(t1, {"status": TaskStatus.COMPLETED})
        progress = service.compute_progress(rid)
        assert progress["completed_tasks"] == 1
        assert progress["overall_percent"] == 33
        ms = progress["milestone_progress"][0]
        assert ms["completed"] == 1
        assert ms["total"] == 2
        assert ms["percent"] == 50

    def test_progress_complete_when_all_done(self):
        service, rid, _, ms2, t1, t2 = self._setup()
        service.update_task(t1, {"status": TaskStatus.COMPLETED})
        service.update_task(t2, {"status": TaskStatus.SKIPPED})
        remaining = service._repo.list_tasks(ms2)[0]
        service.update_task(remaining["id"], {"status": TaskStatus.COMPLETED})
        progress = service.compute_progress(rid)
        assert progress["overall_percent"] == 100

    def test_progress_empty_roadmap(self):
        service, _, _ = _service()
        r = service.create_manual("empty")
        progress = service.compute_progress(r["id"])
        assert progress["total_tasks"] == 0
        assert progress["overall_percent"] == 0
        assert progress["milestone_progress"] == []