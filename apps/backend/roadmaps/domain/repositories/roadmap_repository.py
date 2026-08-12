"""Roadmap repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class IRoadmapRepository(ABC):
    """Data access for the Roadmap aggregate and its children."""

    @abstractmethod
    def get_by_id(self, roadmap_id: str) -> dict[str, Any] | None:
        """Get a roadmap by id, or None."""
        ...

    @abstractmethod
    def get_by_application_id(self, application_id: str) -> dict[str, Any] | None:
        """Get the roadmap for an application, or None."""
        ...

    @abstractmethod
    def list(self) -> list[dict[str, Any]]:
        """List roadmaps, newest first (created_at desc)."""
        ...

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a roadmap. Returns the stored dict."""
        ...

    @abstractmethod
    def update(self, roadmap_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update roadmap core fields (title, description, status, goal fields)."""
        ...

    @abstractmethod
    def delete(self, roadmap_id: str) -> bool:
        """Delete a roadmap and all children. Returns True when a row was removed."""
        ...

    @abstractmethod
    def delete_by_application(self, application_id: str) -> int:
        """Delete every roadmap belonging to an application. Returns the count."""
        ...

    # Goal

    @abstractmethod
    def get_goal(self, roadmap_id: str) -> dict[str, Any] | None:
        """Get the goal row for a roadmap, or None."""
        ...

    @abstractmethod
    def create_goal(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a roadmap goal."""
        ...

    @abstractmethod
    def update_goal(self, roadmap_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a roadmap goal."""
        ...

    # Milestones

    @abstractmethod
    def list_milestones(self, roadmap_id: str) -> list[dict[str, Any]]:
        """List milestones for a roadmap, in position order."""
        ...

    @abstractmethod
    def get_milestone(self, milestone_id: str) -> dict[str, Any] | None:
        """Get a milestone by id, or None."""
        ...

    @abstractmethod
    def create_milestone(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a milestone. Returns the stored dict."""
        ...

    @abstractmethod
    def update_milestone(self, milestone_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update milestone fields."""
        ...

    @abstractmethod
    def delete_milestone(self, milestone_id: str) -> bool:
        """Delete a milestone (and its tasks/links). Returns True when removed."""
        ...

    # Tasks

    @abstractmethod
    def list_tasks(self, milestone_id: str) -> list[dict[str, Any]]:
        """List tasks for a milestone, in position order."""
        ...

    @abstractmethod
    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get a task by id, or None."""
        ...

    @abstractmethod
    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a task. Returns the stored dict."""
        ...

    @abstractmethod
    def update_task(self, task_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update task fields."""
        ...

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """Delete a task. Returns True when removed."""
        ...

    # Skill links

    @abstractmethod
    def list_skills(self, roadmap_id: str) -> list[dict[str, Any]]:
        """List skill links for a roadmap (milestone and task level)."""
        ...

    @abstractmethod
    def get_skill_link(self, link_id: str) -> dict[str, Any] | None:
        """Get a skill link by id, or None."""
        ...

    @abstractmethod
    def create_skill_link(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a skill link. Returns the stored dict."""
        ...

    @abstractmethod
    def delete_skill_link(self, link_id: str) -> bool:
        """Delete a skill link. Returns True when removed."""
        ...

    # Notes

    @abstractmethod
    def list_notes(self, roadmap_id: str) -> list[dict[str, Any]]:
        """List notes for a roadmap."""
        ...

    @abstractmethod
    def create_note(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a note. Returns the stored dict."""
        ...

    @abstractmethod
    def delete_note(self, note_id: str) -> bool:
        """Delete a note. Returns True when removed."""
        ...

    # Resources

    @abstractmethod
    def list_resources(self, roadmap_id: str) -> list[dict[str, Any]]:
        """List resources for a roadmap."""
        ...

    @abstractmethod
    def create_resource(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a resource. Returns the stored dict."""
        ...

    @abstractmethod
    def update_resource(self, resource_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a resource. Returns the stored dict or None."""
        ...

    @abstractmethod
    def delete_resource(self, resource_id: str) -> bool:
        """Delete a resource. Returns True when removed."""
        ...