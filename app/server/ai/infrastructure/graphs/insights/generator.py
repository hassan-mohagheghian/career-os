"""Insights Agent — generates career intelligence insights.

SRP: Only handles insight generation orchestration.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import AgentState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class InsightsAgent:
    """Generates career intelligence insights from job and skill data.

    Orchestrates the insight generation pipeline using existing
    services. Supports partial failure — one section failing
    doesn't stop others.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[AgentState] = None) -> AgentState:
        if state is None:
            state = create_initial_state()

        if self._provider:
            state["context"]["provider"] = self._provider

        nodes = [
            ("collect_data", self._collect_data),
            ("generate", self._generate),
        ]
        return self._executor.execute_chain(nodes, state)

    def _collect_data(self, state: AgentState) -> AgentState:
        """Collect job and skill data for insight generation."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from core.db import get_db

            conn = get_db()

            # Collect job summary
            jobs = conn.execute(
                "SELECT company, role, score, match, overall_score FROM jobs WHERE deleted=0 ORDER BY overall_score DESC LIMIT 50"
            ).fetchall()
            state["metadata"]["jobs"] = [dict(r) for r in jobs] if jobs else []

            # Collect skills
            skills = conn.execute(
                "SELECT name, level, category FROM tech_stack ORDER BY level DESC"
            ).fetchall()
            state["metadata"]["skills"] = [dict(r) for r in skills] if skills else []

            conn.close()
        except Exception as e:
            state["errors"].append(f"Data collection failed: {e}")
        return state

    def _generate(self, state: AgentState) -> AgentState:
        """Generate insight summary."""
        jobs = state.get("metadata", {}).get("jobs", [])
        skills = state.get("metadata", {}).get("skills", [])
        state["output"] = f"Insights: {len(jobs)} jobs, {len(skills)} skills analyzed"
        return state
