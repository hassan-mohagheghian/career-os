"""GraphState — the domain model flowing through workflow graphs.

Backward-compatible alias for BaseState from the runtime layer.
New code should import BaseState directly from graphs.runtime.state.
"""

from __future__ import annotations

from typing import Any

from ...graphs.runtime.state import BaseState, create_initial_state


class GraphState:
    """Backward-compatible wrapper around BaseState TypedDict.

    Provides dataclass-like interface for legacy code that uses
    attribute access (state.input) instead of dict access (state["input"]).
    """

    def __init__(self, **kwargs: Any):
        self._data = BaseState(
            input=kwargs.get("input", ""),
            output=kwargs.get("output", ""),
            context=kwargs.get("context", {}),
            errors=kwargs.get("errors", []),
            metadata=kwargs.get("metadata", {}),
            node_history=kwargs.get("node_history", []),
        )

    @property
    def input(self) -> str:
        return self._data["input"]

    @input.setter
    def input(self, value: str):
        self._data["input"] = value

    @property
    def output(self) -> str:
        return self._data["output"]

    @output.setter
    def output(self, value: str):
        self._data["output"] = value

    @property
    def context(self) -> dict[str, Any]:
        return self._data["context"]

    @property
    def errors(self) -> list[str]:
        return self._data["errors"]

    @property
    def metadata(self) -> dict[str, Any]:
        return self._data["metadata"]

    @property
    def node_history(self) -> list[str]:
        return self._data["node_history"]

    @property
    def session_id(self) -> str:
        return self._data.get("session_id", "")

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphState":
        return cls(**data)


def create_graph_state(
    input: str = "",
    context: dict[str, Any] | None = None,
    session_id: str = "",
) -> GraphState:
    """Factory function — creates a fresh GraphState for legacy code."""
    return GraphState(input=input, context=context or {})
