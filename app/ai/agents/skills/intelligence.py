"""Skill Intelligence Agent — analyzes skill gaps and market demand.

SRP: Only handles skill analysis and comparison.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import AgentState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class SkillIntelligenceAgent:
    """Analyzes skills and generates intelligence insights.

    Compares required skills against user's current skills
    and generates market demand analysis.
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
            ("load_skills", self._load_skills),
            ("analyze_gaps", self._analyze_gaps),
        ]
        return self._executor.execute_chain(nodes, state)

    def _load_skills(self, state: AgentState) -> AgentState:
        """Load current skills from database."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from core.db import get_db

            conn = get_db()
            rows = conn.execute("SELECT name, level, category FROM tech_stack ORDER BY level DESC").fetchall()
            conn.close()

            state["metadata"]["current_skills"] = [dict(r) for r in rows] if rows else []
        except Exception as e:
            state["errors"].append(f"Failed to load skills: {e}")
        return state

    def _analyze_gaps(self, state: AgentState) -> AgentState:
        """Analyze skill gaps from input requirements."""
        current = state.get("metadata", {}).get("current_skills", [])
        current_names = {s["name"].lower() for s in current if s.get("name")}

        state["metadata"]["skill_count"] = len(current)
        state["metadata"]["unique_skills"] = len(current_names)
        state["output"] = f"Analyzed {len(current)} skills"
        return state
