"""RoadmapService — manual roadmaps CRUD and progress calculation.

Business operations for the Roadmap aggregate: create manual roadmaps, edit
goal/milestones/tasks, attach notes, resources and skills, and compute progress
from meaningful completion states (spec 144 §19). Domain events are emitted
best-effort through the RoadmapEventPublisher port (in-memory collector by
default — EDD is incremental, no pub/sub yet).
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from roadmaps.domain.entities.roadmap import (
    GoalType,
    MilestoneStatus,
    NodePriority,
    ResourceStatus,
    ResourceType,
    RoadmapSource,
    RoadmapStatus,
    TaskStatus,
)
from roadmaps.domain.event_publisher import InMemoryEventCollector, RoadmapEventPublisher
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

_UPDATABLE_ROADMAP = ("title", "description", "status", "goal_type")


class RoadmapService:
    """Business operations for the Roadmap aggregate."""

    def __init__(
        self,
        roadmap_repo: Any,
        skill_repo: Any | None = None,
        event_publisher: RoadmapEventPublisher | None = None,
    ):
        self._repo = roadmap_repo
        self._skills = skill_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    # ── Roadmap ─────────────────────────────────────────────────────

    def create_manual(self, title: str, description: str = "", goal: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a roadmap from scratch (source=MANUAL) with an optional goal."""
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create(
            {
                "title": title or "Untitled Roadmap",
                "description": description or "",
                "goal_type": (goal or {}).get("type") or GoalType.CUSTOM,
                "source": RoadmapSource.MANUAL,
                "application_id": None,
                "status": RoadmapStatus.ACTIVE,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._ensure_goal(stored["id"], goal, goal_type=stored["goal_type"])
        self._emit(
            RoadmapCreated(
                aggregate_id=stored["id"],
                roadmap_id=stored["id"],
                source=stored.get("source") or RoadmapSource.MANUAL,
                application_id=stored.get("application_id"),
            )
        )
        return stored

    def create_from_application(
        self,
        title: str,
        description: str = "",
        application_id: str = "",
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a roadmap linked to an application (source=APPLICATION)."""
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create(
            {
                "title": title or "Job Preparation Roadmap",
                "description": description or "",
                "goal_type": GoalType.JOB,
                "source": RoadmapSource.APPLICATION,
                "application_id": application_id or None,
                "status": RoadmapStatus.ACTIVE,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._ensure_goal(stored["id"], goal, goal_type=GoalType.JOB)
        self._emit(
            RoadmapCreated(
                aggregate_id=stored["id"],
                roadmap_id=stored["id"],
                source=stored.get("source") or RoadmapSource.APPLICATION,
                application_id=stored.get("application_id"),
            )
        )
        return stored

    def get(self, roadmap_id: str) -> dict[str, Any] | None:
        return self._repo.get_by_id(roadmap_id)

    def get_by_application(self, application_id: str) -> dict[str, Any] | None:
        return self._repo.get_by_application_id(application_id)

    def list(self) -> list[dict[str, Any]]:
        return self._repo.list()

    def update(self, roadmap_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self._repo.get_by_id(roadmap_id)
        if not current:
            raise NotFoundError(f"Roadmap {roadmap_id} not found")

        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        if "title" in data:
            update["title"] = data["title"]
        if "description" in data:
            update["description"] = data["description"]
        if "status" in data and data["status"] is not None:
            self._validate_roadmap_status(data["status"])
            update["status"] = data["status"]

        stored = self._repo.update(roadmap_id, update) or current
        if data.get("goal") is not None:
            self.update_goal(roadmap_id, data["goal"])
        self._emit(
            RoadmapUpdated(
                aggregate_id=roadmap_id,
                roadmap_id=roadmap_id,
                status=stored.get("status") or RoadmapStatus.ACTIVE,
            )
        )
        return stored

    def delete(self, roadmap_id: str) -> None:
        current = self._repo.get_by_id(roadmap_id)
        if not current:
            raise NotFoundError(f"Roadmap {roadmap_id} not found")
        self._repo.delete(roadmap_id)
        self._emit(RoadmapDeleted(aggregate_id=roadmap_id, roadmap_id=roadmap_id))

    def delete_by_application(self, application_id: str) -> int:
        return self._repo.delete_by_application(application_id)

    # ── Goal ────────────────────────────────────────────────────────

    def update_goal(self, roadmap_id: str, goal: dict[str, Any]) -> dict[str, Any]:
        current = self._repo.get_goal(roadmap_id)
        if not current:
            return self._ensure_goal(roadmap_id, goal, goal_type=goal.get("type") or GoalType.CUSTOM)
        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        for field in ("type", "title", "description"):
            if field in goal and goal[field] is not None:
                self._validate_goal_type(goal[field]) if field == "type" else None
                update[field] = goal[field]
        updated = self._repo.update_goal(roadmap_id, update) or current
        return updated

    # ── Milestones ──────────────────────────────────────────────────

    def add_milestone(
        self,
        roadmap_id: str,
        title: str,
        description: str = "",
        priority: str = NodePriority.MEDIUM,
    ) -> dict[str, Any]:
        self._ensure_roadmap(roadmap_id)
        self._validate_priority(priority)
        milestones = self._repo.list_milestones(roadmap_id)
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create_milestone(
            {
                "roadmap_id": roadmap_id,
                "position": len(milestones),
                "title": title or "New Milestone",
                "description": description or "",
                "status": MilestoneStatus.NOT_STARTED,
                "priority": priority,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            RoadmapMilestoneAdded(
                aggregate_id=roadmap_id,
                roadmap_id=roadmap_id,
                milestone_id=stored["id"],
            )
        )
        return stored

    def update_milestone(self, milestone_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self._repo.get_milestone(milestone_id)
        if not current:
            raise NotFoundError(f"Milestone {milestone_id} not found")
        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        for field in ("position", "title", "description", "priority"):
            if field in data and data[field] is not None:
                if field == "priority":
                    self._validate_priority(data[field])
                update[field] = data[field]
        if "status" in data and data["status"] is not None:
            self._validate_milestone_status(data["status"])
            update["status"] = data["status"]
        stored = self._repo.update_milestone(milestone_id, update) or current
        self._emit(
            RoadmapMilestoneUpdated(
                aggregate_id=stored.get("roadmap_id"),
                roadmap_id=stored.get("roadmap_id") or "",
                milestone_id=milestone_id,
                status=stored.get("status") or MilestoneStatus.NOT_STARTED,
            )
        )
        return stored

    def delete_milestone(self, milestone_id: str) -> None:
        current = self._repo.get_milestone(milestone_id)
        if not current:
            raise NotFoundError(f"Milestone {milestone_id} not found")
        self._repo.delete_milestone(milestone_id)
        self._emit(
            RoadmapMilestoneDeleted(
                aggregate_id=current.get("roadmap_id"),
                roadmap_id=current.get("roadmap_id") or "",
                milestone_id=milestone_id,
            )
        )

    # ── Tasks ───────────────────────────────────────────────────────

    def add_task(
        self,
        milestone_id: str,
        title: str,
        description: str = "",
        priority: str = NodePriority.MEDIUM,
        estimated_effort: str | None = None,
        success_criteria: str | None = None,
    ) -> dict[str, Any]:
        milestone = self._repo.get_milestone(milestone_id)
        if not milestone:
            raise NotFoundError(f"Milestone {milestone_id} not found")
        self._validate_priority(priority)
        tasks = self._repo.list_tasks(milestone_id)
        now = datetime.now(UTC).isoformat()
        stored = self._repo.create_task(
            {
                "milestone_id": milestone_id,
                "position": len(tasks),
                "title": title or "New Task",
                "description": description or "",
                "status": TaskStatus.NOT_STARTED,
                "priority": priority,
                "estimated_effort": estimated_effort,
                "success_criteria": success_criteria,
                "completed_at": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        self._emit(
            RoadmapTaskAdded(
                aggregate_id=milestone.get("roadmap_id"),
                roadmap_id=milestone.get("roadmap_id") or "",
                milestone_id=milestone_id,
                task_id=stored["id"],
            )
        )
        return stored

    def update_task(self, task_id: str, data: dict[str, Any]) -> dict[str, Any]:
        current = self._repo.get_task(task_id)
        if not current:
            raise NotFoundError(f"Task {task_id} not found")
        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        for field in ("position", "title", "description", "priority", "estimated_effort", "success_criteria"):
            if field in data and data[field] is not None:
                if field == "priority":
                    self._validate_priority(data[field])
                update[field] = data[field]
        if "status" in data and data["status"] is not None and data["status"] != current.get("status"):
            self._validate_task_status(data["status"])
            update["status"] = data["status"]
            update["completed_at"] = (
                datetime.now(UTC).isoformat()
                if data["status"] == TaskStatus.COMPLETED
                else None
            )
        stored = self._repo.update_task(task_id, update) or current
        self._emit(
            RoadmapTaskUpdated(
                aggregate_id=current.get("milestone_id"),
                roadmap_id=current.get("roadmap_id") or self._roadmap_id_for_task(task_id) or "",
                milestone_id=current.get("milestone_id") or "",
                task_id=task_id,
                status=stored.get("status") or TaskStatus.NOT_STARTED,
            )
        )
        return stored

    def delete_task(self, task_id: str) -> None:
        current = self._repo.get_task(task_id)
        if not current:
            raise NotFoundError(f"Task {task_id} not found")
        roadmap_id = self._roadmap_id_for_task(task_id) or ""
        self._repo.delete_task(task_id)
        self._emit(
            RoadmapTaskDeleted(
                aggregate_id=current.get("milestone_id"),
                roadmap_id=roadmap_id,
                milestone_id=current.get("milestone_id") or "",
                task_id=task_id,
            )
        )

    # ── Notes / Resources / Skills ──────────────────────────────────

    def add_note(self, roadmap_id: str, content: str, milestone_id: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        self._ensure_roadmap(roadmap_id)
        if not str(content or "").strip():
            raise ValidationError("Note content must not be empty")
        stored = self._repo.create_note(
            {
                "roadmap_id": roadmap_id,
                "milestone_id": milestone_id,
                "task_id": task_id,
                "content": content,
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )
        self._emit(
            RoadmapNoteAdded(
                aggregate_id=roadmap_id,
                roadmap_id=roadmap_id,
                note_id=stored["id"],
            )
        )
        return stored

    def delete_note(self, note_id: str) -> None:
        if not self._repo.delete_note(note_id):
            raise NotFoundError(f"Note {note_id} not found")

    def add_resource(
        self,
        roadmap_id: str,
        title: str,
        url: str = "",
        description: str = "",
        type_: str = ResourceType.OTHER,
        milestone_id: str | None = None,
        task_id: str | None = None,
        source: str = "USER",
    ) -> dict[str, Any]:
        self._ensure_roadmap(roadmap_id)
        self._validate_str_in(title, "Resource title")
        self._validate_str_in(type_, "Resource type", ResourceType.ALL)
        stored = self._repo.create_resource(
            {
                "roadmap_id": roadmap_id,
                "milestone_id": milestone_id,
                "task_id": task_id,
                "title": title,
                "url": url or "",
                "description": description or "",
                "type": type_,
                "status": ResourceStatus.PLANNED,
                "source": source if source in ("AI", "USER") else "USER",
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )
        self._emit(
            RoadmapResourceAdded(
                aggregate_id=roadmap_id,
                roadmap_id=roadmap_id,
                resource_id=stored["id"],
            )
        )
        return stored

    def update_resource(self, resource_id: str, data: dict[str, Any]) -> dict[str, Any]:
        update: dict[str, Any] = {"updated_at": datetime.now(UTC).isoformat()}
        for field in ("title", "url", "description", "type", "status"):
            if field in data and data[field] is not None:
                update[field] = data[field]
        updated = self._repo.update_resource(resource_id, update)
        if not updated:
            raise NotFoundError(f"Resource {resource_id} not found")
        return updated

    def delete_resource(self, resource_id: str) -> None:
        if not self._repo.delete_resource(resource_id):
            raise NotFoundError(f"Resource {resource_id} not found")

    def link_skill(self, roadmap_id: str, skill_name: str, milestone_id: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        self._ensure_roadmap(roadmap_id)
        if not self._skills:
            raise ValidationError("Skill repository is not available")
        skill_id = str(self._skills.resolve_skill({"name": skill_name, "source_type": "ai_generated"}))
        links = self._repo.list_skills(roadmap_id)
        stored = self._repo.create_skill_link(
            {
                "roadmap_id": roadmap_id,
                "milestone_id": milestone_id,
                "task_id": task_id,
                "skill_id": skill_id,
                "skill_name": skill_name,
                "position": len(links),
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )
        self._emit(
            RoadmapSkillLinked(
                aggregate_id=roadmap_id,
                roadmap_id=roadmap_id,
                link_id=stored["id"],
                skill_id=skill_id,
            )
        )
        return stored

    def unlink_skill(self, link_id: str) -> None:
        if not self._repo.delete_skill_link(link_id):
            raise NotFoundError(f"Skill link {link_id} not found")

    # ── Progress ────────────────────────────────────────────────────

    def compute_progress(self, roadmap_id: str) -> dict[str, Any]:
        """Derive progress from task completion states (spec 144 §19).

        Returns ``{completed_tasks, total_tasks, overall_percent,
        milestone_progress: [{milestone_id, completed, total, percent}]}``.
        overall_percent = completed tasks / total tasks (0 when no tasks).
        """
        milestones = self._repo.list_milestones(roadmap_id)
        completed_tasks = 0
        total_tasks = 0
        milestone_progress: list[dict[str, Any]] = []
        for ms in milestones:
            tasks = self._repo.list_tasks(ms["id"])
            done = sum(1 for t in tasks if t.get("status") in TaskStatus.COMPLETION_STATES)
            total_tasks += len(tasks)
            completed_tasks += done
            milestone_progress.append(
                {
                    "milestone_id": ms["id"],
                    "completed": done,
                    "total": len(tasks),
                    "percent": round(done / len(tasks) * 100) if tasks else 0,
                }
            )
        overall = round(completed_tasks / total_tasks * 100) if total_tasks else 0
        return {
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "overall_percent": overall,
            "milestone_progress": milestone_progress,
        }

    # ── helpers ─────────────────────────────────────────────────────

    def _ensure_goal(self, roadmap_id: str, goal: dict[str, Any] | None, goal_type: str = GoalType.CUSTOM) -> dict[str, Any]:
        goal = goal or {}
        type_ = goal.get("type") or goal_type
        self._validate_goal_type(type_)
        return self._repo.create_goal(
            {
                "roadmap_id": roadmap_id,
                "type": type_,
                "title": goal.get("title") or "",
                "description": goal.get("description") or "",
                "target_job_id": goal.get("target_job_id"),
                "target_company_id": goal.get("target_company_id"),
                "target_skill_id": goal.get("target_skill_id"),
                "created_at": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )

    def _roadmap_id_for_task(self, task_id: str) -> str | None:
        task = self._repo.get_task(task_id)
        if not task:
            return None
        milestone = self._repo.get_milestone(task.get("milestone_id") or "")
        return milestone.get("roadmap_id") if milestone else None

    def _ensure_roadmap(self, roadmap_id: str) -> None:
        if not self._repo.get_by_id(roadmap_id):
            raise NotFoundError(f"Roadmap {roadmap_id} not found")

    @staticmethod
    def _validate_roadmap_status(status: str) -> None:
        if status not in RoadmapStatus.ALL:
            raise ValidationError(
                f"Invalid roadmap status '{status}'; allowed: {', '.join(RoadmapStatus.ALL)}"
            )

    @staticmethod
    def _validate_goal_type(type_: str) -> None:
        if type_ not in GoalType.ALL:
            raise ValidationError(f"Invalid goal type '{type_}'; allowed: {', '.join(GoalType.ALL)}")

    @staticmethod
    def _validate_priority(priority: str) -> None:
        if priority not in NodePriority.ALL:
            raise ValidationError(f"Invalid priority '{priority}'; allowed: {', '.join(NodePriority.ALL)}")

    @staticmethod
    def _validate_task_status(status: str) -> None:
        if status not in TaskStatus.ALL:
            raise ValidationError(f"Invalid task status '{status}'; allowed: {', '.join(TaskStatus.ALL)}")

    @staticmethod
    def _validate_milestone_status(status: str) -> None:
        if status not in MilestoneStatus.ALL:
            raise ValidationError(f"Invalid milestone status '{status}'; allowed: {', '.join(MilestoneStatus.ALL)}")

    @staticmethod
    def _validate_str_in(value: str, label: str, allowed: tuple[str, ...] | None = None) -> None:
        if not str(value or "").strip():
            raise ValidationError(f"{label} must not be empty")
        if allowed is not None and value not in allowed:
            raise ValidationError(
                f"Invalid {label} '{value}'; allowed: {', '.join(allowed)}"
            )

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


__all__ = ["RoadmapService"]