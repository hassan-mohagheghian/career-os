from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Callable, Optional

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.checkpoint.base import BaseCheckpointSaver
    _HAS_LANGGRAPH = True
except ImportError:
    _HAS_LANGGRAPH = False

from .state import BaseState, create_initial_state, CheckpointConfig

try:
    import structlog
    _log = structlog.get_logger("ai.graph")
except ImportError:
    import logging
    _log = logging.getLogger("ai.graph")


def _create_checkpointer(config: Optional[CheckpointConfig] = None) -> Any:
    if config is None or not config.get("enabled", True):
        return MemorySaver()
    db_url = config.get("db_url", "")
    if db_url:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            return PostgresSaver.from_conn_string(db_url)
        except ImportError:
            _log.warning("graph.checkpoint.postgres_unavailable", db_url=db_url)
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        conn = sqlite3.connect(config.get("table_name", "checkpoints.db"), check_same_thread=False)
        return SqliteSaver(conn)
    except ImportError:
        pass
    return MemorySaver()


class GraphBuilder:
    def __init__(self, name: str = "agent_graph"):
        self._name = name
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable, dict]] = []
        self._entry: Optional[str] = None
        self._finish: Optional[str] = None
        self._retry_config: dict[str, dict] = {}

    def add_node(self, name: str, fn: Callable) -> GraphBuilder:
        self._nodes[name] = fn
        return self

    def add_edge(self, source: str, target: str) -> GraphBuilder:
        self._edges.append((source, target))
        return self

    def add_conditional_edge(
        self,
        source: str,
        condition: Callable,
        mapping: dict[str, str],
    ) -> GraphBuilder:
        self._conditional_edges.append((source, condition, mapping))
        return self

    def set_entry(self, node_name: str) -> GraphBuilder:
        self._entry = node_name
        return self

    def set_finish(self, node_name: str) -> GraphBuilder:
        self._finish = node_name
        return self

    def set_retry(self, node_name: str, max_retries: int = 3, delay: float = 1.0) -> GraphBuilder:
        self._retry_config[node_name] = {
            "max_retries": max_retries,
            "delay": delay,
        }
        return self

    def compile(self, checkpointer: Any = None) -> "CompiledGraph":
        if _HAS_LANGGRAPH:
            return self._compile_langgraph(checkpointer=checkpointer)
        else:
            return self._compile_sequential()

    def _compile_langgraph(self, checkpointer: Any = None) -> "CompiledGraph":
        graph = StateGraph(BaseState)

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

        if checkpointer is not None:
            compiled = graph.compile(checkpointer=checkpointer)
        else:
            compiled = graph.compile()

        _log.info(
            "graph.compiled",
            name=self._name,
            nodes=list(self._nodes.keys()),
            entry=self._entry,
            finish=self._finish,
            backend="langgraph",
            checkpoint_type=type(checkpointer).__name__ if checkpointer else "None",
        )

        return CompiledGraph(
            name=self._name,
            _compiled=compiled,
            backend="langgraph",
            retry_config=self._retry_config,
        )

    def _wrap_node(self, name: str, fn: Callable) -> Callable:
        retry_cfg = self._retry_config.get(name, {})
        max_retries = retry_cfg.get("max_retries", 0)
        delay = retry_cfg.get("delay", 1.0)

        # Total nodes for progress calculation
        total_nodes = max(len(self._nodes), 1)

        def wrapped(state: dict) -> dict:
            attempt = 0
            node_start = time.time()

            state["current_node"] = name

            completed = state.get("progress", {}).get("completed_nodes", [])
            pct = (len(completed) / total_nodes) * 100
            state["progress"] = {
                "current_node": name,
                "progress_pct": round(pct, 1),
                "message": f"Running {name}...",
                "started_at": state.get("progress", {}).get("started_at") or datetime.now().isoformat(),
                "completed_nodes": completed,
                "node_timings": state.get("progress", {}).get("node_timings", {}),
            }

            while True:
                try:
                    result = fn(state)
                    if "node_history" not in result:
                        result["node_history"] = []
                    result["node_history"].append(name)

                    elapsed = time.time() - node_start
                    completed = result.get("progress", {}).get("completed_nodes", [])
                    if name not in completed:
                        completed = [*completed, name]
                    timings = result.get("progress", {}).get("node_timings", {})
                    timings[name] = round(elapsed * 1000, 1)
                    pct = (len(completed) / total_nodes) * 100
                    result["progress"] = {
                        "current_node": "",
                        "progress_pct": round(min(pct, 99.9), 1),
                        "message": f"Completed {name} ({round(elapsed * 1000)}ms)",
                        "started_at": result.get("progress", {}).get("started_at") or datetime.now().isoformat(),
                        "completed_nodes": completed,
                        "node_timings": timings,
                    }
                    result["current_node"] = ""
                    return result
                except Exception as e:
                    retry_info = f" (attempt {attempt + 1}/{max_retries + 1})" if max_retries > 0 else ""
                    error_msg = f"[{name}] Failed{retry_info}: {type(e).__name__}: {e}"
                    state.setdefault("errors", []).append(error_msg)
                    state.setdefault("failure_details", []).append({
                        "workflow_step": name,
                        "exception": f"{type(e).__name__}: {e}",
                        "retry_count": attempt,
                        "recoverable": attempt < max_retries,
                    })
                    if attempt < max_retries:
                        attempt += 1
                        time.sleep(delay)
                        continue
                    state.setdefault("node_history", []).append(
                        f"{name}:FAILED"
                    )
                    state["progress"] = {
                        "current_node": f"{name}:FAILED",
                        "progress_pct": state.get("progress", {}).get("progress_pct", 0),
                        "message": error_msg,
                        "started_at": state.get("progress", {}).get("started_at"),
                        "completed_nodes": state.get("progress", {}).get("completed_nodes", []),
                        "node_timings": state.get("progress", {}).get("node_timings", {}),
                    }
                    raise

        wrapped.__name__ = name
        return wrapped

    def _compile_sequential(self) -> "CompiledGraph":
        order = self._build_execution_order()

        def run(state: BaseState) -> BaseState:
            for node_name in order:
                fn = self._nodes[node_name]
                retry_cfg = self._retry_config.get(node_name, {})
                max_retries = retry_cfg.get("max_retries", 0)
                delay = retry_cfg.get("delay", 1.0)
                attempt = 0

                while True:
                    try:
                        state = fn(state)
                        state.setdefault("node_history", []).append(node_name)
                        break
                    except Exception as e:
                        state.setdefault("errors", []).append(
                            f"[{node_name}] {type(e).__name__}: {e}"
                        )
                        if attempt < max_retries:
                            attempt += 1
                            time.sleep(delay)
                            continue
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
        if not self._edges:
            return list(self._nodes.keys())

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
    def __init__(
        self,
        name: str,
        _compiled=None,
        _sequential_fn: Optional[Callable] = None,
        backend: str = "unknown",
        retry_config: Optional[dict] = None,
    ):
        self._name = name
        self._compiled = _compiled
        self._sequential_fn = _sequential_fn
        self._backend = backend
        self._retry_config = retry_config or {}

    def invoke(
        self,
        state: Optional[BaseState] = None,
        config: Optional[dict] = None,
    ) -> BaseState:
        if state is None:
            state = create_initial_state()

        if self._backend == "langgraph" and self._compiled is not None:
            try:
                result = self._compiled.invoke(state, config=config)
                return result
            except Exception as e:
                state.setdefault("errors", []).append(str(e))
                return state
        elif self._sequential_fn is not None:
            return self._sequential_fn(state)
        else:
            raise RuntimeError(f"Graph '{self._name}' has no execution backend")

    def stream(
        self,
        state: Optional[BaseState] = None,
        config: Optional[dict] = None,
    ):
        if state is None:
            state = create_initial_state()

        if self._backend == "langgraph" and self._compiled is not None:
            for event in self._compiled.stream(state, config=config):
                yield event
        else:
            result = self.invoke(state, config)
            yield {"output": result}

    def get_state(self, config: dict) -> Optional[BaseState]:
        if self._backend == "langgraph" and self._compiled is not None:
            try:
                snapshot = self._compiled.get_state(config)
                return snapshot.values if hasattr(snapshot, "values") else snapshot
            except Exception:
                return None
        return None

    def update_state(self, config: dict, values: dict) -> None:
        if self._backend == "langgraph" and self._compiled is not None:
            try:
                self._compiled.update_state(config, values)
            except Exception as e:
                _log.warning("graph.update_state_failed", error=str(e))

    @property
    def name(self) -> str:
        return self._name

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def retry_config(self) -> dict:
        return self._retry_config
