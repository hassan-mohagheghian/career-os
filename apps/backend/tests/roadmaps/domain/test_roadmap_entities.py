"""Tests for the Roadmaps bounded context entities and domain events."""

from __future__ import annotations

from roadmaps.domain.entities.roadmap import (
    GoalType,
    MilestoneStatus,
    NodePriority,
    ResourceSource,
    ResourceStatus,
    ResourceType,
    Roadmap,
    RoadmapGoal,
    RoadmapMilestone,
    RoadmapNote,
    RoadmapResource,
    RoadmapSkillLink,
    RoadmapSource,
    RoadmapStatus,
    RoadmapTask,
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
from shared.domain.domain_event import DomainEvent


class TestRoadmapEntity:
    def test_defaults(self):
        r = Roadmap()
        assert r.status == RoadmapStatus.ACTIVE
        assert r.source == RoadmapSource.MANUAL
        assert r.goal_type == GoalType.CUSTOM
        assert r.application_id is None
        assert r.created_at and r.updated_at

    def test_to_dict(self):
        r = Roadmap(title="Backend Roadmap", description="Go deeper")
        data = r.to_dict()
        assert data["title"] == "Backend Roadmap"
        assert data["goal_type"] == GoalType.CUSTOM
        assert data["source"] == RoadmapSource.MANUAL

    def test_id_is_uuid7(self):
        r = Roadmap()
        assert len(r.id) == 36


class TestChildEntities:
    def test_goal_defaults(self):
        g = RoadmapGoal()
        assert g.type == GoalType.CUSTOM
        assert g.target_job_id is None
        assert g.to_dict()["roadmap_id"] == ""

    def test_milestone_defaults(self):
        m = RoadmapMilestone()
        assert m.status == MilestoneStatus.NOT_STARTED
        assert m.priority == NodePriority.MEDIUM
        assert m.position == 0

    def test_task_defaults(self):
        t = RoadmapTask()
        assert t.status == TaskStatus.NOT_STARTED
        assert t.priority == NodePriority.MEDIUM
        assert t.estimated_effort is None
        assert t.completed_at is None

    def test_skill_link_defaults(self):
        s = RoadmapSkillLink()
        assert s.skill_id == ""
        assert s.milestone_id is None
        assert s.task_id is None

    def test_note_defaults(self):
        n = RoadmapNote()
        assert n.content == ""
        assert n.milestone_id is None
        assert n.task_id is None

    def test_resource_defaults(self):
        r = RoadmapResource()
        assert r.type == ResourceType.OTHER
        assert r.status == ResourceStatus.PLANNED
        assert r.source == ResourceSource.USER


class TestEnumConstants:
    def test_status_lists(self):
        assert RoadmapStatus.ALL == ("ACTIVE", "COMPLETED", "ARCHIVED")
        assert MilestoneStatus.ALL == ("NOT_STARTED", "IN_PROGRESS", "COMPLETED")
        assert TaskStatus.ALL == ("NOT_STARTED", "IN_PROGRESS", "COMPLETED", "SKIPPED")

    def test_goal_types(self):
        assert GoalType.ALL == ("JOB", "CAREER", "SKILL", "CUSTOM")

    def test_resource_lists(self):
        assert ResourceType.ALL == (
            "ARTICLE",
            "VIDEO",
            "COURSE",
            "BOOK",
            "DOCUMENTATION",
            "PROJECT",
            "OTHER",
        )
        assert ResourceStatus.ALL == ("PLANNED", "IN_PROGRESS", "COMPLETED")
        assert ResourceSource.ALL == ("AI", "USER")


class TestRoadmapEvents:
    def test_all_events_are_domain_events(self):
        for cls in (
            RoadmapCreated,
            RoadmapUpdated,
            RoadmapDeleted,
            RoadmapMilestoneAdded,
            RoadmapMilestoneUpdated,
            RoadmapMilestoneDeleted,
            RoadmapTaskAdded,
            RoadmapTaskUpdated,
            RoadmapTaskDeleted,
            RoadmapNoteAdded,
            RoadmapResourceAdded,
            RoadmapSkillLinked,
        ):
            assert issubclass(cls, DomainEvent)

    def test_created_event_fields(self):
        e = RoadmapCreated(aggregate_id="r-1", roadmap_id="r-1", source=RoadmapSource.APPLICATION, application_id="a-1")
        assert e.event_type == "roadmap.created"
        assert e.roadmap_id == "r-1"
        assert e.application_id == "a-1"
        assert e.aggregate_id == "r-1"

    def test_updated_event(self):
        e = RoadmapUpdated(roadmap_id="r-1", status=RoadmapStatus.COMPLETED)
        assert e.event_type == "roadmap.updated"

    def test_task_updated_event(self):
        e = RoadmapTaskUpdated(roadmap_id="r-1", milestone_id="m-1", task_id="t-1", status=TaskStatus.COMPLETED)
        assert e.event_type == "roadmap.task.updated"

    def test_skill_linked_event(self):
        e = RoadmapSkillLinked(roadmap_id="r-1", link_id="l-1", skill_id="s-1")
        assert e.event_type == "roadmap.skill.linked"
