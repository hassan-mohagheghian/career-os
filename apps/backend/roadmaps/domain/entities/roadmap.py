"""Roadmap aggregate entities.

The Roadmap is the independent aggregate root of the Roadmaps bounded context
(spec 144 §5, §7, §28). It represents a user goal broken into milestones and
tasks, with optional skill links, notes and learning resources.

Cross-context references (``application_id``, ``skill_id``) are logical only —
no FKs into the ``application`` or ``skill`` schemas (AGENTS.md rule 15). FKs
exist only within the ``roadmap`` schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any
import uuid


@dataclass
class TimestampedEntity:
    """Minimal timestamped entity base used by the Roadmaps context."""

    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class RoadmapSource:
    """Where a roadmap came from."""

    APPLICATION = "APPLICATION"
    AI_GENERATED = "AI_GENERATED"
    MANUAL = "MANUAL"

    ALL = (APPLICATION, AI_GENERATED, MANUAL)


class RoadmapStatus:
    """Allowed roadmap lifecycle statuses."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

    ALL = (ACTIVE, COMPLETED, ARCHIVED)


class GoalType:
    """What kind of goal a roadmap targets."""

    JOB = "JOB"
    CAREER = "CAREER"
    SKILL = "SKILL"
    CUSTOM = "CUSTOM"

    ALL = (JOB, CAREER, SKILL, CUSTOM)


class NodePriority:
    """Priority of a milestone or task."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    ALL = (CRITICAL, HIGH, MEDIUM, LOW)


class TaskStatus:
    """Status of a roadmap task."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"

    ALL = (NOT_STARTED, IN_PROGRESS, COMPLETED, SKIPPED)
    COMPLETION_STATES = (COMPLETED, SKIPPED)


class MilestoneStatus:
    """Status of a roadmap milestone."""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

    ALL = (NOT_STARTED, IN_PROGRESS, COMPLETED)


class ResourceType:
    """Kind of learning resource attached to a roadmap node."""

    ARTICLE = "ARTICLE"
    VIDEO = "VIDEO"
    COURSE = "COURSE"
    BOOK = "BOOK"
    DOCUMENTATION = "DOCUMENTATION"
    PROJECT = "PROJECT"
    OTHER = "OTHER"

    ALL = (ARTICLE, VIDEO, COURSE, BOOK, DOCUMENTATION, PROJECT, OTHER)


class ResourceStatus:
    """Progress of a learning resource."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

    ALL = (PLANNED, IN_PROGRESS, COMPLETED)


class ResourceSource:
    """Who created a resource — AI or the user."""

    AI = "AI"
    USER = "USER"

    ALL = (AI, USER)


@dataclass
class Roadmap(TimestampedEntity):
    """A personalized goal-based roadmap."""

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    title: str = ""
    description: str = ""
    goal_type: str = GoalType.CUSTOM
    source: str = RoadmapSource.MANUAL
    application_id: str | None = None
    status: str = RoadmapStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "goal_type": self.goal_type,
            "source": self.source,
            "application_id": self.application_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoadmapGoal(TimestampedEntity):
    """The goal a roadmap targets.

    Kept as a separate row so future goal types can carry target references
    (job/company/skill) without reshaping the roadmap aggregate.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    roadmap_id: str = ""
    type: str = GoalType.CUSTOM
    title: str = ""
    description: str = ""
    target_job_id: str | None = None
    target_company_id: str | None = None
    target_skill_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "roadmap_id": self.roadmap_id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "target_job_id": self.target_job_id,
            "target_company_id": self.target_company_id,
            "target_skill_id": self.target_skill_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoadmapMilestone(TimestampedEntity):
    """A milestone is a meaningful outcome, not merely a topic."""

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    roadmap_id: str = ""
    position: int = 0
    title: str = ""
    description: str = ""
    status: str = MilestoneStatus.NOT_STARTED
    priority: str = NodePriority.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "roadmap_id": self.roadmap_id,
            "position": self.position,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoadmapTask(TimestampedEntity):
    """A concrete, actionable step inside a milestone."""

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    milestone_id: str = ""
    position: int = 0
    title: str = ""
    description: str = ""
    status: str = TaskStatus.NOT_STARTED
    priority: str = NodePriority.MEDIUM
    estimated_effort: str | None = None
    success_criteria: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "milestone_id": self.milestone_id,
            "position": self.position,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "estimated_effort": self.estimated_effort,
            "success_criteria": self.success_criteria,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoadmapSkillLink(TimestampedEntity):
    """A reference from a milestone or task to a global Skill (logical id)."""

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    roadmap_id: str = ""
    milestone_id: str | None = None
    task_id: str | None = None
    skill_id: str = ""
    skill_name: str = ""
    position: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "roadmap_id": self.roadmap_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "position": self.position,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoadmapNote(TimestampedEntity):
    """A contextual note on a milestone or task."""

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    roadmap_id: str = ""
    milestone_id: str | None = None
    task_id: str | None = None
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "roadmap_id": self.roadmap_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class RoadmapResource(TimestampedEntity):
    """A learning resource attached to a milestone or task."""

    id: str = field(default_factory=lambda: str(uuid.uuid7()))
    roadmap_id: str = ""
    milestone_id: str | None = None
    task_id: str | None = None
    title: str = ""
    url: str = ""
    description: str = ""
    type: str = ResourceType.OTHER
    status: str = ResourceStatus.PLANNED
    source: str = ResourceSource.USER

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "roadmap_id": self.roadmap_id,
            "milestone_id": self.milestone_id,
            "task_id": self.task_id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "type": self.type,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


__all__ = [
    "TimestampedEntity",
    "Roadmap",
    "RoadmapGoal",
    "RoadmapMilestone",
    "RoadmapTask",
    "RoadmapSkillLink",
    "RoadmapNote",
    "RoadmapResource",
    "RoadmapSource",
    "RoadmapStatus",
    "GoalType",
    "NodePriority",
    "TaskStatus",
    "MilestoneStatus",
    "ResourceType",
    "ResourceStatus",
    "ResourceSource",
]