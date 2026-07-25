"""Tests for workflow graphs — LangGraph-based orchestration.

TDD: Tests define the graph execution contract.
DDD: Graphs model domain workflows as state machines.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.ai.agents.runtime.state import create_initial_state
from app.ai.agents.runtime.graph import GraphBuilder, CompiledGraph
from app.ai.agents.runtime.executor import AgentExecutor
from app.ai.agents.runtime.registry import AgentRegistry


# ── Graph Builder Tests ─────────────────────────────────────────────

class TestGraphBuilder:
    """GraphBuilder — Builder Pattern for constructing workflow graphs."""

    def test_build_simple_linear_graph(self):
        def node_a(state):
            state["output"] = "a"
            return state

        def node_b(state):
            state["output"] = state["output"] + "b"
            return state

        builder = GraphBuilder("test_linear")
        builder.add_node("a", node_a)
        builder.add_node("b", node_b)
        builder.add_edge("a", "b")
        builder.set_entry("a")
        builder.set_finish("b")

        graph = builder.compile()
        result = graph.invoke(create_initial_state(input="start"))

        assert result["output"] == "ab"

    def test_graph_records_node_history(self):
        def node_a(state):
            return state
        def node_b(state):
            return state

        builder = GraphBuilder("test_history")
        builder.add_node("a", node_a)
        builder.add_node("b", node_b)
        builder.add_edge("a", "b")
        builder.set_entry("a")
        builder.set_finish("b")

        graph = builder.compile()
        result = graph.invoke(create_initial_state(input="test"))

        assert "a" in result["node_history"]
        assert "b" in result["node_history"]

    def test_graph_with_conditional_edge(self):
        def node_fetch(state):
            state["metadata"]["has_content"] = True
            return state

        def node_analyze(state):
            state["output"] = "analyzed"
            return state

        def node_skip(state):
            state["output"] = "skipped"
            return state

        def route(state):
            if state.get("metadata", {}).get("has_content"):
                return "analyze"
            return "skip"

        builder = GraphBuilder("test_conditional")
        builder.add_node("fetch", node_fetch)
        builder.add_node("analyze", node_analyze)
        builder.add_node("skip", node_skip)
        builder.add_conditional_edge("fetch", route, {
            "analyze": "analyze",
            "skip": "skip",
        })
        builder.set_entry("fetch")

        graph = builder.compile()
        result = graph.invoke(create_initial_state(input="test"))

        assert result["output"] == "analyzed"

    def test_graph_error_stops_execution(self):
        def node_a(state):
            raise ValueError("boom")

        def node_b(state):
            state["output"] = "should not run"
            return state

        builder = GraphBuilder("test_error")
        builder.add_node("a", node_a)
        builder.add_node("b", node_b)
        builder.add_edge("a", "b")
        builder.set_entry("a")

        graph = builder.compile()
        result = graph.invoke(create_initial_state(input="test"))

        assert len(result["errors"]) > 0
        assert result.get("output") != "should not run"


# ── Compiled Graph Tests ────────────────────────────────────────────

class TestCompiledGraph:
    def test_invoke_with_default_state(self):
        def echo(state):
            state["output"] = state["input"]
            return state

        builder = GraphBuilder("test_echo")
        builder.add_node("echo", echo)
        builder.set_entry("echo")
        builder.set_finish("echo")

        graph = builder.compile()
        result = graph.invoke()  # No state provided

        assert result["input"] == ""

    def test_graph_name_and_backend(self):
        builder = GraphBuilder("my_graph")
        builder.add_node("n", lambda s: s)
        builder.set_entry("n")

        graph = builder.compile()
        assert graph.name == "my_graph"
        assert graph.backend in ("langgraph", "sequential")


# ── Integration: Executor + Graph ───────────────────────────────────

class TestExecutorWithGraph:
    """Integration test: AgentExecutor executing graph nodes."""

    def test_execute_chain_via_executor(self):
        executor = AgentExecutor()

        def fetch(state):
            state["output"] = "fetched"
            return state

        def analyze(state):
            state["output"] = state["output"] + " + analyzed"
            return state

        state = create_initial_state(input="test")
        result = executor.execute_chain(
            [("fetch", fetch), ("analyze", analyze)],
            state,
        )

        assert result["output"] == "fetched + analyzed"
        assert "fetch" in result["node_history"]
        assert "analyze" in result["node_history"]


# ── Integration: Registry + Executor ────────────────────────────────

class TestRegistryIntegration:
    def test_register_and_execute_agent(self):
        registry = AgentRegistry()
        registry.reset()

        def my_agent(state):
            state["output"] = "agent result"
            return state

        registry.register("test_agent", my_agent, description="Test agent")

        agent = registry.get("test_agent")
        assert agent is not None

        executor = AgentExecutor()
        state = create_initial_state(input="test")
        result = executor.execute_node(agent, state, node_name="test_agent")

        assert result["output"] == "agent result"
        registry.reset()
