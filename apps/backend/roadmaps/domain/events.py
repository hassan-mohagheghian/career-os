"""Domain events for the Roadmaps bounded context.

Emitted as a roadmap evolves: created, edited, deleted, milestones/tasks/notes/
resources/skill links added or removed. All events are immutable facts
(AGENTS.md rule 16); the default transport is the in-memory collector.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class RoadmapCreated(DomainEvent):
    """A new roadmap was created."""

    roadmap_id: str = ""
    source: str = ""
    application_id: str | None = None
    event_type: str = "roadmap.created"


@dataclass(frozen=True)
class RoadmapUpdated(DomainEvent):
    """The roadmap core changed (title, description, status, goal)."""

    roadmap_id: str = ""
    status: str = ""
    event_type: str = "roadmap.updated"


@dataclass(frozen=True)
class RoadmapDeleted(DomainEvent):
    """A roadmap was removed."""

    roadmap_id: str = ""
    event_type: str = "roadmap.deleted"


@dataclass(frozen=True)
class RoadmapMilestoneAdded(DomainEvent):
    """A milestone was added to a roadmap."""

    roadmap_id: str = ""
    milestone_id: str = ""
    event_type: str = "roadmap.milestone.added"


@dataclass(frozen=True)
class RoadmapMilestoneUpdated(DomainEvent):
    """A milestone changed (title, description, status, priority, position)."""

    roadmap_id: str = ""
    milestone_id: str = ""
    status: str = ""
    event_type: str = "roadmap.milestone.updated"


@dataclass(frozen=True)
class RoadmapMilestoneDeleted(DomainEvent):
    """A milestone was removed."""

    roadmap_id: str = ""
    milestone_id: str = ""
    event_type: str = "roadmap.milestone.deleted"


@dataclass(frozen=True)
class RoadmapTaskAdded(DomainEvent):
    """A task was added to a milestone."""

    roadmap_id: str = ""
    milestone_id: str = ""
    task_id: str = ""
    event_type: str = "roadmap.task.added"


@dataclass(frozen=True)
class RoadmapTaskUpdated(DomainEvent):
    """A task changed (title, description, status, priority, position)."""

    roadmap_id: str = ""
    milestone_id: str = ""
    task_id: str = ""
    status: str = ""
    event_type: str = "roadmap.task.updated"


@dataclass(frozen=True)
class RoadmapTaskDeleted(DomainEvent):
    """A task was removed."""

    roadmap_id: str = ""
    milestone_id: str = ""
    task_id: str = ""
    event_type: str = "roadmap.task.deleted"


@dataclass(frozen=True)
class RoadmapNoteAdded(DomainEvent):
    """A note was attached to a roadmap node."""

    roadmap_id: str = ""
    note_id: str = ""
    event_type: str = "roadmap.note.added"


@dataclass(frozen=True)
class RoadmapResourceAdded(DomainEvent):
    """A learning resource was attached to a roadmap node."""

    roadmap_id: str = ""
    resource_id: str = ""
    event_type: str = "roadmap.resource.added"


@dataclass(frozen=True)
class RoadmapSkillLinked(DomainEvent):
    """A skill was linked to a roadmap milestone or task."""

    roadmap_id: str = ""
    link_id: str = ""
    skill_id: str = ""
    event_type: str = "roadmap.skill.linked"


__all__ = [
    "RoadmapCreated",
    "RoadmapUpdated",
    "RoadmapDeleted",
    "RoadmapMilestoneAdded",
    "RoadmapMilestoneUpdated",
    "RoadmapMilestoneDeleted",
    "RoadmapTaskAdded",
    "RoadmapTaskUpdated",
    "RoadmapTaskDeleted",
    "RoadmapNoteAdded",
    "RoadmapResourceAdded",
    "RoadmapSkillLinked",
]