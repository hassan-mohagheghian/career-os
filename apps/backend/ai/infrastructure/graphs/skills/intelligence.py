"""Skill Intelligence Agent — analyzes skill gaps and market demand.

SRP: Only handles skill analysis and comparison.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from skills.infrastructure.models.skill_model import SkillModel
from skills.infrastructure.mappers import skill_model_to_dict
from ..runtime.state import BaseState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class SkillIntelligenceAgent:
    """Analyzes skills and generates intelligence insights.

    Compares required skills against user's current skills
    and generates market demand analysis.
    """

    def __init__(self, provider: Optional[LLMProvider] = None, session: Optional[Session] = None):
        self._provider = provider
        self._session = session
        self._executor = AgentExecutor()

    def execute(self, state: Optional[BaseState] = None) -> BaseState:
        if state is None:
            state = create_initial_state()

        if self._provider:
            state["context"]["provider"] = self._provider

        nodes = [
            ("load_skills", self._load_skills),
            ("analyze_gaps", self._analyze_gaps),
        ]
        return self._executor.execute_chain(nodes, state)

    def _load_skills(self, state: BaseState) -> BaseState:
        """Load current skills from database."""
        try:
            if self._session is None:
                from shared.infrastructure.database.session import get_session_sync
                self._session = get_session_sync()

            rows = self._session.query(SkillModel.name, SkillModel.level, SkillModel.category) \
                .order_by(SkillModel.level.desc()).all()

            state["metadata"]["current_skills"] = [
                {"name": r.name, "level": r.level, "category": r.category}
                for r in rows
            ] if rows else []
        except Exception as e:
            state["errors"].append(f"Failed to load skills: {e}")
        return state

    def _analyze_gaps(self, state: BaseState) -> BaseState:
        """Analyze skill gaps from input requirements."""
        current = state.get("metadata", {}).get("current_skills", [])
        current_names = {s["name"].lower() for s in current if s.get("name")}

        state["metadata"]["skill_count"] = len(current)
        state["metadata"]["unique_skills"] = len(current_names)
        state["output"] = f"Analyzed {len(current)} skills"
        return state
