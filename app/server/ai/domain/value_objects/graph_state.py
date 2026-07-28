"""GraphState — the domain model flowing through workflow graphs.

Immutable contract: nodes return new/updated state, never modify in-place.
This is the core data structure that all graph nodes read from and write to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphState:
    """Typed state dictionary for graph execution.

    Attributes:
        input: The original user input / prompt.
        output: The final output after graph execution.
        context: Shared context (provider, config, DB connections).
        errors: List of error messages encountered during execution.
        metadata: Arbitrary metadata (duration, token counts, etc.).
        node_history: List of node names that have executed.
        session_id: Generation session ID for tracking.
    """
    input: str = ""
    output: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    node_history: list[str] = field(default_factory=list)
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "context": self.context,
            "errors": self.errors,
            "metadata": self.metadata,
            "node_history": self.node_history,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphState:
        return cls(
            input=data.get("input", ""),
            output=data.get("output", ""),
            context=data.get("context", {}),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
            node_history=data.get("node_history", []),
            session_id=data.get("session_id", ""),
        )


def create_initial_state(
    input: str = "",
    context: dict[str, Any] | None = None,
    session_id: str = "",
) -> GraphState:
    """Factory function — creates a fresh state for graph execution."""
    return GraphState(
        input=input,
        context=context or {},
        session_id=session_id,
    )
