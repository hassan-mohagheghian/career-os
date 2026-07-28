"""Tests for workflow graphs — LangGraph-based orchestration.

TDD: Tests define the graph execution contract.
DDD: Graphs model domain workflows as state machines.
"""

import pytest
import json
from unittest.mock import MagicMock, patch

from ai.infrastructure.graphs.runtime.state import (
    create_initial_state,
    JobProcessingState,
    CompanyProcessingState,
    InsightsState,
    SkillRoadmapState,
    CheckpointConfig,
)
from ai.infrastructure.graphs.runtime.graph import GraphBuilder, CompiledGraph
from ai.infrastructure.graphs.runtime.executor import AgentExecutor
from ai.infrastructure.graphs.runtime.registry import AgentRegistry


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

    def test_graph_with_retry(self):
        call_count = 0

        def flaky_node(state):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient error")
            state["output"] = "success after retry"
            return state

        builder = GraphBuilder("test_retry")
        builder.add_node("flaky", flaky_node)
        builder.set_entry("flaky")
        builder.set_finish("flaky")
        builder.set_retry("flaky", max_retries=3, delay=0.01)

        graph = builder.compile()
        result = graph.invoke(create_initial_state(input="test"))

        assert result["output"] == "success after retry"
        assert call_count == 3


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


# ── Checkpointing Tests ─────────────────────────────────────────────

class TestCheckpointing:
    """Checkpointing — LangGraph native checkpoint integration."""

    def test_checkpoint_config_defaults(self):
        config: CheckpointConfig = {"thread_id": "thread_1"}
        assert config["thread_id"] == "thread_1"
        assert "checkpoint_id" not in config

    def test_checkpoint_config_full(self):
        config: CheckpointConfig = {
            "thread_id": "thread_1",
            "checkpoint_id": "ckpt_001",
        }
        assert config["thread_id"] == "thread_1"
        assert config["checkpoint_id"] == "ckpt_001"

    def test_compile_with_checkpointer(self):
        def node_a(state):
            state["output"] = "checkpointed"
            return state

        builder = GraphBuilder("test_checkpoint")
        builder.add_node("a", node_a)
        builder.set_entry("a")
        builder.set_finish("a")

        from langgraph.checkpoint.memory import MemorySaver
        graph = builder.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "test_thread"}}
        state = create_initial_state(input="test")
        result = graph.invoke(state, config=config)

        assert result["output"] == "checkpointed"

    def test_graph_get_and_update_state(self):
        def node_a(state):
            state["output"] = "from_a"
            state.setdefault("metadata", {})["visited_a"] = True
            return state

        builder = GraphBuilder("test_state_ops")
        builder.add_node("a", node_a)
        builder.set_entry("a")
        builder.set_finish("a")

        from langgraph.checkpoint.memory import MemorySaver
        graph = builder.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "state_ops"}}
        state = create_initial_state(input="test")
        graph.invoke(state, config=config)

        saved = graph.get_state(config)
        assert saved is not None
        assert saved["output"] == "from_a"
        assert saved["metadata"]["visited_a"] is True

        graph.update_state(config, {"output": "updated"})
        updated = graph.get_state(config)
        assert updated["output"] == "updated"


# ── Workflow State Transition Tests ────────────────────────────────

class TestWorkflowStateTransitions:
    """Workflow-specific state transitions."""

    def test_job_processing_state_transition(self):
        updated = JobProcessingState(
            input="job url",
            raw_content="job posting content",
            job_title="Software Engineer",
            job_company="Tech Corp",
            job_num=1,
            extraction_data={"title": "Software Engineer", "company": "Tech Corp"},
            resume_text="",
            linkedin_text="",
            rules="",
        )
        assert updated["extraction_data"]["title"] == "Software Engineer"

    def test_company_processing_state_transition(self):
        updated = CompanyProcessingState(
            input="company url",
            raw_content="about page",
            company_name="Tech Corp",
            company_type="private",
            extraction_data={"name": "Tech Corp", "industry": "AI"},
            intelligence_data={},
            scores={"overall": 85},
        )
        assert updated["scores"]["overall"] == 85

    def test_insights_state_transition(self):
        updated = InsightsState(
            input="insight prompt",
            section="skills",
            section_data={"top_skills": ["Python", "ML"]},
            all_results=[{"section": "skills", "data": {"top_skills": ["Python", "ML"]}}],
            errors_list=[],
        )
        assert len(updated["all_results"]) == 1

    def test_skill_roadmap_state_transition(self):
        updated = SkillRoadmapState(
            input="skill roadmap",
            skill_name="Machine Learning",
            job_type="engineer",
            job_id=1,
            items=[
                {"skill": "Python", "level": "intermediate"},
                {"skill": "TensorFlow", "level": "beginner"},
            ],
        )
        assert len(updated["items"]) == 2

    def test_state_serialization_roundtrip(self):
        state = JobProcessingState(
            input="test",
            raw_content="raw",
            job_title="Engineer",
            job_company="Co",
            job_num=1,
            extraction_data={"key": "value"},
            resume_text="resume",
            linkedin_text="linkedin",
            rules="rules",
            output="result",
        )
        serialized = json.dumps(state, default=str)
        deserialized = json.loads(serialized)
        assert deserialized["input"] == "test"
        assert deserialized["extraction_data"]["key"] == "value"
