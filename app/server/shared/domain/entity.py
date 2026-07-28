"""Base Entity class for all domain entities.

Provides identity management, equality based on identity,
and automatic created_at/updated_at handling.

Existing entities must preserve their existing identifiers.
New entities automatically receive a UUID v4 identifier.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


class BaseEntity:
    """Base class for all domain entities.

    An entity is defined by its identity, not its attributes.
    Two entities are equal if they share the same identity.

    Attributes:
        id: Unique identifier (UUID v4 for new entities, preserves existing for migrated)
        created_at: Timestamp when entity was created
        updated_at: Timestamp when entity was last updated
    """

    def __init__(
        self,
        id: Any = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        if id is None:
            id = str(uuid.uuid4())
        self._id = id
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or datetime.utcnow()

    @property
    def id(self) -> Any:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        self._updated_at = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id!r})"
