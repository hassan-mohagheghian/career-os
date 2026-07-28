"""ProcessJobCommand — command object for initiating job processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessJobCommand:
    """Command to process a job through the AI workflow graph.

    Business contexts send this command to the AI bounded context.
    The AI context owns the entire processing pipeline.
    """
    url: str = ""
    notes: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    source: str = "web"
    pid: int = 0
    session_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_sources(self) -> bool:
        return bool(self.url or self.notes or self.links)

    def validate(self) -> list[str]:
        """Validate the command. Returns list of errors."""
        errors = []
        if not self.has_sources:
            errors.append("At least one job source (URL, notes, or links) is required")
        return errors
