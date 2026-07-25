"""Tests for the Agent Runtime layer.

TDD: These tests define the agent system contract.
DDD: Tests verify domain model invariants.
SOLID: Each test class covers one responsibility.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.ai.agents.runtime.state import AgentState, create_initial_state
from app.ai.agents.runtime.registry import AgentRegistry, AgentMetadata
from app.ai.providers.base import LLMProvider, ProviderConfig, ProviderResponse


# ── Domain Model Tests ──────────────────────────────────────────────

class TestAgentState:
    """AgentState is a value object — immutable state flowing through graphs.

    DDD: State carries the domain context between graph nodes.
    """

    def test_create_initial_state(self):
        state = create_initial_state(input="test prompt")
        assert state["input"] == "test prompt"
        assert state["output"] == ""
        assert state["errors"] == []
        assert state["metadata"] == {}

    def test_state_has_required_keys(self):
        state = create_initial_state(input="test")
        required = {"input", "output", "context", "errors", "metadata", "node_history"}
        assert required.issubset(state.keys())

    def test_state_is_mutable_dict(self):
        state = create_initial_state(input="test")
        state["output"] = "result"
        assert state["output"] == "result"

    def test_state_default_context_is_empty_dict(self):
        state = create_initial_state(input="test")
        assert state["context"] == {}

    def test_state_carry_extra_metadata(self):
        state = create_initial_state(input="test")
        state["metadata"]["provider"] = "mimo"
        state["metadata"]["duration"] = 1.5
        assert state["metadata"]["provider"] == "mimo"


# ── Agent Registry Tests ────────────────────────────────────────────

class TestAgentMetadata:
    """AgentMetadata is a value object — agent registration info."""

    def test_create_metadata(self):
        meta = AgentMetadata(
            name="job_extractor",
            description="Extracts job information",
            version="1.0.0",
            tags=["job", "extraction"],
        )
        assert meta.name == "job_extractor"
        assert meta.version == "1.0.0"
        assert "job" in meta.tags


class TestAgentRegistry:
    """AgentRegistry — Registry Pattern for agent discovery.

    SRP: Only manages agent registration and retrieval.
    OCP: New agents register without modifying the registry.
    """

    def test_register_and_get_agent(self):
        registry = AgentRegistry()
        agent = MagicMock()
        registry.register("test_agent", agent, description="Test agent")
        retrieved = registry.get("test_agent")
        assert retrieved is agent

    def test_get_unknown_agent_returns_none(self):
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_register_with_metadata(self):
        registry = AgentRegistry()
        agent = MagicMock()
        meta = AgentMetadata(name="my_agent", description="desc")
        registry.register("my_agent", agent, metadata=meta)
        assert registry.get_metadata("my_agent") is meta

    def test_list_agents(self):
        registry = AgentRegistry()
        registry.register("agent_a", MagicMock())
        registry.register("agent_b", MagicMock())
        names = registry.list_agents()
        assert "agent_a" in names
        assert "agent_b" in names

    def test_unregister_agent(self):
        registry = AgentRegistry()
        registry.register("temp_agent", MagicMock())
        registry.unregister("temp_agent")
        assert registry.get("temp_agent") is None

    def test_singleton_pattern(self):
        r1 = AgentRegistry.instance()
        r2 = AgentRegistry.instance()
        assert r1 is r2

    def test_reset_clears_all(self):
        registry = AgentRegistry()
        registry.register("x", MagicMock())
        registry.reset()
        assert registry.get("x") is None


# ── Agent Execution Tests ───────────────────────────────────────────

class TestAgentExecutor:
    """AgentExecutor — Orchestrates agent graph execution.

    Strategy Pattern: Executor uses different graph strategies.
    Observer Pattern: Logs events at each lifecycle point.
    """

    def test_execute_simple_node(self):
        from app.ai.agents.runtime.executor import AgentExecutor

        def my_node(state: dict) -> dict:
            state["output"] = "done"
            return state

        executor = AgentExecutor()
        result = executor.execute_node(my_node, create_initial_state(input="test"))
        assert result["output"] == "done"

    def test_execute_node_with_provider(self):
        from app.ai.agents.runtime.executor import AgentExecutor

        provider = MagicMock(spec=LLMProvider)
        provider.generate.return_value = ProviderResponse(content="ai response")

        def ai_node(state: dict) -> dict:
            resp = state["context"]["provider"].generate(state["input"])
            state["output"] = resp.content
            return state

        executor = AgentExecutor()
        state = create_initial_state(input="test prompt")
        state["context"]["provider"] = provider
        result = executor.execute_node(ai_node, state)
        assert result["output"] == "ai response"

    def test_execute_records_node_history(self):
        from app.ai.agents.runtime.executor import AgentExecutor

        def node_a(state):
            return state
        def node_b(state):
            return state

        executor = AgentExecutor()
        state = create_initial_state(input="test")
        state = executor.execute_node(node_a, state, node_name="node_a")
        state = executor.execute_node(node_b, state, node_name="node_b")
        assert "node_a" in state["node_history"]
        assert "node_b" in state["node_history"]

    def test_execute_node_catches_errors(self):
        from app.ai.agents.runtime.executor import AgentExecutor

        def failing_node(state):
            raise ValueError("something broke")

        executor = AgentExecutor()
        state = create_initial_state(input="test")
        result = executor.execute_node(failing_node, state, node_name="failing")
        assert len(result["errors"]) == 1
        assert "something broke" in result["errors"][0]
