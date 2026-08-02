"""GraphExecutor — orchestrates LangGraph workflow execution.

Strategy Pattern: Different graph executors for different workflow types.
Observer Pattern: Emits progress events at each stage.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable, Optional

from ...domain.value_objects.graph_state import GraphState, create_initial_state


class GraphExecutor:
    """Executes workflow graphs with error handling and progress tracking.

    Lifecycle:
    1. Initialize state
    2. Execute graph nodes sequentially
    3. Emit progress events
    4. Handle errors and retries
    5. Return final state
    """

    def __init__(
        self,
        max_retries: int = 1,
        retry_delay: float = 1.0,
    ):
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def execute(
        self,
        graph: Any,
        state: Optional[GraphState] = None,
        session_id: str = "",
        progress_callback: Optional[Callable] = None,
    ) -> GraphState:
        """Execute a workflow graph.

        Args:
            graph: The compiled graph to execute.
            state: Initial state. If None, creates empty state.
            session_id: Generation session ID for tracking.
            progress_callback: Callback for progress events.

        Returns:
            Final state after graph execution.
        """
        if state is None:
            state = create_initial_state(session_id=session_id)

        start_time = time.time()

        try:
            # Execute the graph
            result = graph.invoke(state)

            duration = time.time() - start_time

            # Emit completion
            if progress_callback:
                progress_callback(
                    stage="completed",
                    progress=1.0,
                    message=f"Graph completed in {duration:.2f}s",
                )

            return result

        except Exception as e:
            duration = time.time() - start_time

            # Record error
            state.errors.append(f"Graph execution failed: {e}")

            # Emit failure
            if progress_callback:
                progress_callback(
                    stage="failed",
                    progress=0.0,
                    message=f"Graph failed: {e}",
                )

            raise

    def execute_node(
        self,
        node_fn: Callable[[GraphState], GraphState],
        state: GraphState,
        node_name: str = "",
        retries: Optional[int] = None,
    ) -> GraphState:
        """Execute a single graph node with retry logic.

        Args:
            node_fn: Function that takes state and returns updated state.
            state: Current graph state.
            node_name: Name for logging.
            retries: Override max retries for this node.

        Returns:
            Updated state after node execution.
        """
        name = node_name or getattr(node_fn, "__name__", "unknown")
        max_retries = retries if retries is not None else self._max_retries
        attempt = 0

        while attempt <= max_retries:
            start_time = time.time()

            try:
                result = node_fn(state)
                duration = time.time() - start_time

                # Record in node history
                result.node_history.append(name)

                return result

            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"[{name}] {type(e).__name__}: {e}"

                # Record error
                state.errors.append(error_msg)

                if attempt < max_retries:
                    attempt += 1
                    time.sleep(self._retry_delay)
                    continue

                # Final failure
                state.node_history.append(f"{name}:FAILED")
                return state

        return state
