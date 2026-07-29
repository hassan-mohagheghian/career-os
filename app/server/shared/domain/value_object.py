"""Base Value Object and common value object types.

Value objects are immutable and defined by their attributes, not identity.
Two value objects are equal if all their attributes are equal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any
import uuid


@dataclass(frozen=True)
class ValueObject:
    """Base class for all value objects.

    Subclasses should be frozen dataclasses for immutability.
    Equality is based on attribute values.
    """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))


@dataclass(frozen=True)
class UUID(ValueObject):
    """UUID value object."""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> UUID:
        return cls(value=value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DateTime(ValueObject):
    """DateTime value object."""
    value: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def now(cls) -> DateTime:
        return cls(value=datetime.now(UTC))

    @classmethod
    def from_string(cls, value: str) -> DateTime:
        return cls(value=datetime.fromisoformat(value))

    def __str__(self) -> str:
        return self.value.isoformat()
