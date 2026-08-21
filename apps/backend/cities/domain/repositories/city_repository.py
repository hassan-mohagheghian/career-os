"""Repository port for the Cities bounded context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ICityRepository(ABC):
    """Persistence port for normalized city rows."""

    @abstractmethod
    def find_by_city_country(self, city: str, country: str) -> dict[str, Any] | None:
        """Return a city row by its canonical city+country (case-insensitive)."""

    @abstractmethod
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new city row and return it as a dict."""

    @abstractmethod
    def list_with_job_counts(
        self, sort: str = "jobs", order: str = "desc"
    ) -> list[dict[str, Any]]:
        """Return every visible (non-hidden) city with its non-deleted job count.

        ``sort`` is one of ``jobs`` | ``country`` | ``city`` | ``created_at``;
        ``order`` is ``asc`` | ``desc``. Default: jobs count descending.
        """

    @abstractmethod
    def get_by_id(self, city_id: str) -> dict[str, Any] | None:
        """Return a city row (including hidden ones) by id, with aliases."""

    @abstractmethod
    def merge(self, target_id: str, source_ids: list[str]) -> dict[str, Any]:
        """Merge one or more source cities into a target city.

        Sources are soft-hidden, their names become aliases of the target, and
        every logical reference (jobs/companies/candidate profiles) plus the
        denormalized city/country text is re-pointed to the target.
        """

    @abstractmethod
    def add_alias(self, city_id: str, alias_name: str) -> dict[str, Any] | None:
        """Add an alias to a city; return the updated city or None if missing."""

    @abstractmethod
    def remove_alias(self, city_id: str, alias_name: str) -> dict[str, Any] | None:
        """Remove an alias from a city; return the updated city or None if missing."""

    @abstractmethod
    def promote_alias_to_canonical(
        self, city_id: str, alias_name: str
    ) -> dict[str, Any] | None:
        """Make an alias the canonical name; the old canonical becomes an alias."""


__all__ = ["ICityRepository"]