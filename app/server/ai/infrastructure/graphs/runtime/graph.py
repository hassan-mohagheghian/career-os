"""Graph Builder — constructs and compiles LangGraph workflows.

Builder Pattern: Chain node/edge additions, then compile.
Adapter Pattern: Wraps LangGraph's StateGraph with our AgentState.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Type

try:
    from langgraph.graph import StateGraph, END
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False

from .state import AgentState, create_initial_state

try:
    from services.process.logging_config import get_logger
    _log = get_logger("ai.graph")
except ImportError:
    import logging
    _log = logging.getLogger("ai.graph")


class GraphBuilder:
    """Builds workflow graphs using LangGraph's StateGraph.

    Builder Pattern:
        builder = GraphBuilder()
        builder.add_node("fetch", fetch_fn)
        builder.add_node("analyze", analyze_fn)
        builder.add_edge("fetch", "analyze")
        builder.set_entry("fetch")
        builder.set_finish("analyze")
        graph = builder.compile()

    If langgraph is not available, falls back to a simple sequential executor.
    """

    def __init__(self, name: str = "agent_graph"):
        self._name = name
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable, dict]] = []
        self._entry: Optional[str] = None
        self._finish: Optional[str] = None

    def add_node(self, name: str, fn: Callable) -> GraphBuilder:
        """Add a named node to the graph."""
        self._nodes[name] = fn
        return self

    def add_edge(self, source: str, target: str) -> GraphBuilder:
        """Add a direct edge between two nodes."""
        self._edges.append((source, target))
        return self

    def add_conditional_edge(
        self,
        source: str,
        condition: Callable,
        mapping: dict[str, str],
    ) -> GraphBuilder:
        """Add a conditional edge with a routing function.

        Args:
            source: Source node name.
            condition: Function that takes state and returns a key.
            mapping: Maps condition return values to target node names.
        """
        self._conditional_edges.append((source, condition, mapping))
        return self

    def set_entry(self, node_name: str) -> GraphBuilder:
        """Set the entry point node."""
        self._entry = node_name
        return self

    def set_finish(self, node_name: str) -> GraphBuilder:
        """Set the finish point node."""
        self._finish = node_name
        return self

    def compile(self) -> "CompiledGraph":
        """Compile the graph into an executable form.

        Uses LangGraph if available, otherwise falls back to sequential.
        """
        if _HAS_LANGGRAPH:
            return self._compile_langgraph()
        else:
            return self._compile_sequential()

    def _compile_langgraph(self) -> "CompiledGraph":
        """Compile using LangGraph's StateGraph.

        Wraps each node with error handling and history recording
        since LangGraph manages state immutably.
        """
        graph = StateGraph(AgentState)

        for name, fn in self._nodes.items():
            wrapped = self._wrap_node(name, fn)
            graph.add_node(name, wrapped)

        for source, target in self._edges:
            graph.add_edge(source, target)

        for source, condition, mapping in self._conditional_edges:
            graph.add_conditional_edges(source, condition, mapping)

        if self._entry:
            graph.set_entry_point(self._entry)

        if self._finish:
            graph.add_edge(self._finish, END)

        compiled = graph.compile()

        _log.info(
            "graph.compiled",
            name=self._name,
            nodes=list(self._nodes.keys()),
            entry=self._entry,
            finish=self._finish,
            backend="langgraph",
        )

        return CompiledGraph(
            name=self._name,
            _compiled=compiled,
            backend="langgraph",
        )

    def _wrap_node(self, name: str, fn: Callable) -> Callable:
        """Wrap a node function with error handling and history recording.

        Decorator Pattern: transparently adds cross-cutting concerns.
        """
        def wrapped(state: dict) -> dict:
            try:
                result = fn(state)
                if "node_history" not in result:
                    result["node_history"] = []
                result["node_history"].append(name)
                return result
            except Exception as e:
                state.setdefault("errors", []).append(f"[{name}] {type(e).__name__}: {e}")
                state.setdefault("node_history", []).append(f"{name}:FAILED")
                raise
        wrapped.__name__ = name
        return wrapped

    def _compile_sequential(self) -> "CompiledGraph":
        """Fallback: simple sequential execution without LangGraph."""
        # Build execution order from edges
        order = self._build_execution_order()

        def run(state: AgentState) -> AgentState:
            for node_name in order:
                fn = self._nodes[node_name]
                try:
                    state = fn(state)
                    state.setdefault("node_history", []).append(node_name)
                except Exception as e:
                    state.setdefault("errors", []).append(
                        f"[{node_name}] {type(e).__name__}: {e}"
                    )
                    state.setdefault("node_history", []).append(
                        f"{node_name}:FAILED"
                    )
                    break
            return state

        _log.info(
            "graph.compiled",
            name=self._name,
            nodes=order,
            backend="sequential",
        )

        return CompiledGraph(
            name=self._name,
            _compiled=None,
            _sequential_fn=run,
            backend="sequential",
        )

    def _build_execution_order(self) -> list[str]:
        """Build topological order from edges."""
        if not self._edges:
            return list(self._nodes.keys())

        # Simple topological sort
        in_degree = {n: 0 for n in self._nodes}
        adjacency = {n: [] for n in self._nodes}
        for src, tgt in self._edges:
            adjacency[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

        queue = [n for n, d in in_degree.items() if d == 0]
        order = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order


class CompiledGraph:
    """A compiled, ready-to-execute graph.

    Adapter Pattern: Wraps LangGraph compiled graph or sequential function.
    """

    def __init__(
        self,
        name: str,
        _compiled=None,
        _sequential_fn: Optional[Callable] = None,
        backend: str = "unknown",
    ):
        self._name = name
        self._compiled = _compiled
        self._sequential_fn = _sequential_fn
        self._backend = backend

    def invoke(self, state: Optional[AgentState] = None) -> AgentState:
        """Execute the graph with optional initial state.

        Args:
            state: Initial state. If None, creates empty state.

        Returns:
            Final state after graph execution.
        """
        if state is None:
            state = create_initial_state()

        if self._backend == "langgraph" and self._compiled is not None:
            try:
                result = self._compiled.invoke(state)
                return result
            except Exception as e:
                state.setdefault("errors", []).append(str(e))
                return state
        elif self._sequential_fn is not None:
            return self._sequential_fn(state)
        else:
            raise RuntimeError(f"Graph '{self._name}' has no execution backend")

    @property
    def name(self) -> str:
        return self._name

    @property
    def backend(self) -> str:
        return self._backend
