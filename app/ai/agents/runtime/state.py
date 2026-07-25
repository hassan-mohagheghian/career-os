"""Agent State — the domain model flowing through workflow graphs.

DDD Value Object: State carries all context between graph nodes.
Each node reads from state and writes updates back.
Immutable contract: nodes return new/updated state, never modify in-place.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Typed state dictionary for agent graph execution.

    Attributes:
        input: The original user input / prompt.
        output: The final output after graph execution.
        context: Shared context (provider, config, DB connections).
        errors: List of error messages encountered during execution.
        metadata: Arbitrary metadata (duration, token counts, etc.).
        node_history: List of node names that have executed.
    """
    input: str
    output: str
    context: dict[str, Any]
    errors: list[str]
    metadata: dict[str, Any]
    node_history: list[str]


def create_initial_state(
    input: str = "",
    context: dict[str, Any] | None = None,
) -> AgentState:
    """Factory function — creates a fresh state for graph execution.

    DDD Factory: Encapsulates state creation logic.
    """
    return AgentState(
        input=input,
        output="",
        context=context or {},
        errors=[],
        metadata={},
        node_history=[],
    )
