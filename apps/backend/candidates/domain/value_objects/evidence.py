"""Evidence and Confidence value objects for candidate profile entities.

Every extracted entity carries provenance: which sources contributed to it and
how confident the system is in it. A skill proven by Resume + LinkedIn + GitHub
would carry ``Evidence(sources=["resume", "linkedin", "github"], confidence=0.96)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Confidence:
    """A confidence score normalized to the [0.0, 1.0] range."""

    value: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", max(0.0, min(1.0, float(self.value))))

    def to_dict(self) -> float:
        return self.value

    @classmethod
    def from_value(cls, value: float | None) -> "Confidence":
        return cls(float(value or 0.0))


@dataclass(frozen=True)
class Evidence:
    """Provenance for a candidate profile entity.

    Attributes:
        sources: Source identifiers that contributed to this entity (e.g.
            ``["resume", "linkedin"]``).
        confidence: Confidence score in [0.0, 1.0].
        notes: Optional free-form provenance notes.
    """

    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", list(self.sources))
        object.__setattr__(self, "confidence", Confidence(self.confidence).value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sources": list(self.sources),
            "confidence": self.confidence,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> "Evidence":
        data = data or {}
        return cls(
            sources=list(data.get("sources") or []),
            confidence=data.get("confidence", 0.0),
            notes=data.get("notes", ""),
        )
