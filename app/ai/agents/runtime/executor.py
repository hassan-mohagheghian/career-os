"""Agent Executor — orchestrates node execution with lifecycle logging.

SRP: Only handles node execution, error handling, and event logging.
Observer Pattern: Emits structured log events at each lifecycle point.
Decorator Pattern: Wraps node functions with retry/error handling.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable, Optional

from .state import AgentState, create_initial_state

try:
    from services.process.logging_config import get_logger
    _log = get_logger("ai.executor")
except ImportError:
    import logging

    class _CompatLogger:
        """Adapter: converts structlog-style kwargs to stdlib logging."""

        def __init__(self, name):
            self._logger = logging.getLogger(name)

        def info(self, event, **kwargs):
            self._logger.info("%s %s", event, kwargs)

        def warning(self, event, **kwargs):
            self._logger.warning("%s %s", event, kwargs)

        def error(self, event, **kwargs):
            self._logger.error("%s %s", event, kwargs)

    _log = _CompatLogger("ai.executor")


class AgentExecutor:
    """Executes agent nodes with error handling and structured logging.

    Lifecycle:
    1. node_started — before node execution
    2. node_completed — after successful execution
    3. node_failed — on error

    Design Patterns:
    - Strategy: Different execution strategies (retry, timeout, etc.)
    - Observer: Logs events at each lifecycle point
    - Template Method: Subclasses can override error handling
    """

    def __init__(self, max_retries: int = 0):
        self._max_retries = max_retries

    def execute_node(
        self,
        node_fn: Callable[[dict], dict],
        state: AgentState,
        node_name: str = "",
        retries: Optional[int] = None,
    ) -> AgentState:
        """Execute a single graph node.

        Args:
            node_fn: Callable that takes state dict and returns updated state.
            state: Current agent state.
            node_name: Name for logging (defaults to function name).
            retries: Override max retries for this node.

        Returns:
            Updated state after node execution.
        """
        name = node_name or getattr(node_fn, "__name__", "unknown")
        max_retries = retries if retries is not None else self._max_retries
        attempt = 0

        while attempt <= max_retries:
            start_time = time.time()

            _log.info("agent.node_started", node=name, attempt=attempt)

            try:
                result = node_fn(state)
                duration = time.time() - start_time

                # Record in node history
                if "node_history" not in result:
                    result["node_history"] = []
                result["node_history"].append(name)

                _log.info(
                    "agent.node_completed",
                    node=name,
                    duration=round(duration, 3),
                    attempt=attempt,
                )
                return result

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"[{name}] {type(e).__name__}: {e}"

                _log.warning(
                    "agent.node_failed",
                    node=name,
                    error=str(e),
                    attempt=attempt,
                    duration=round(duration, 3),
                )

                # Record error in state
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(error_msg)

                if attempt < max_retries:
                    attempt += 1
                    continue

                # Final failure — record in history and return
                if "node_history" not in state:
                    state["node_history"] = []
                state["node_history"].append(f"{name}:FAILED")
                return state

        return state

    def execute_chain(
        self,
        nodes: list[tuple[str, Callable]],
        state: AgentState,
    ) -> AgentState:
        """Execute a chain of nodes sequentially.

        Args:
            nodes: List of (name, node_fn) tuples.
            state: Initial state.

        Returns:
            Final state after all nodes execute.
        """
        for name, node_fn in nodes:
            state = self.execute_node(node_fn, state, node_name=name)
            # Stop chain if there are unrecoverable errors
            if state.get("errors") and self._max_retries == 0:
                break
        return state
