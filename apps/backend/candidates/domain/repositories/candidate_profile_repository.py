"""Candidate profile repository interface.

The profile aggregate owns all children (skills, experiences, projects, ...).
Repositories expose read of the full nested aggregate, replace of a child set
(delete-then-insert, the merge primitive), core updates, and version snapshots.
"""

from abc import ABC, abstractmethod
from typing import Any

CHILD_KINDS = (
    "skills",
    "experiences",
    "projects",
    "educations",
    "certificates",
    "interests",
    "languages",
)


class ICandidateProfileRepository(ABC):
    """Data access for the candidate profile aggregate."""

    @abstractmethod
    def get_current_profile(self) -> dict[str, Any] | None:
        """Get the current profile with all children, or None."""
        ...

    @abstractmethod
    def get_or_create_current(self) -> dict[str, Any]:
        """Get the current profile, creating the singleton candidate + profile."""
        ...

    @abstractmethod
    def update_core(self, profile_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update the profile header fields (version, name, title, ...)."""
        ...

    @abstractmethod
    def replace_children(self, profile_id: str, kind: str, items: list[dict[str, Any]]) -> int:
        """Replace the full child set of ``kind`` for a profile (delete-then-insert).

        ``kind`` is one of CHILD_KINDS. Returns the number of rows inserted.
        """
        ...

    @abstractmethod
    def create_version(
        self,
        profile_id: str,
        version: int,
        snapshot: dict[str, Any],
        source_versions: dict[str, int],
        change_summary: str = "",
    ) -> dict[str, Any]:
        """Persist an immutable profile version snapshot."""
        ...

    @abstractmethod
    def list_versions(self, profile_id: str) -> list[dict[str, Any]]:
        """List profile versions, newest first."""
        ...
