"""Insights Agent — generates career intelligence insights.

SRP: Only handles insight generation orchestration.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from jobs.infrastructure.models.job_model import JobModel
from skills.infrastructure.models.skill_model import SkillModel
from ..runtime.state import BaseState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class InsightsAgent:
    """Generates career intelligence insights from job and skill data.

    Orchestrates the insight generation pipeline using existing
    services. Supports partial failure — one section failing
    doesn't stop others.
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
            ("collect_data", self._collect_data),
            ("generate", self._generate),
        ]
        return self._executor.execute_chain(nodes, state)

    def _collect_data(self, state: BaseState) -> BaseState:
        """Collect job and skill data for insight generation."""
        try:
            if self._session is None:
                from shared.infrastructure.database.session import get_session_sync
                self._session = get_session_sync()

            jobs = self._session.query(
                JobModel.company, JobModel.role, JobModel.score,
                JobModel.match, JobModel.overall_score
            ).filter(JobModel.deleted == 0) \
             .order_by(JobModel.overall_score.desc()) \
             .limit(50).all()

            state["metadata"]["jobs"] = [
                {"company": r.company, "role": r.role, "score": r.score,
                 "match": r.match, "overall_score": r.overall_score}
                for r in jobs
            ] if jobs else []

            skills = self._session.query(
                SkillModel.name, SkillModel.level, SkillModel.category
            ).order_by(SkillModel.level.desc()).all()

            state["metadata"]["skills"] = [
                {"name": r.name, "level": r.level, "category": r.category}
                for r in skills
            ] if skills else []
        except Exception as e:
            state["errors"].append(f"Data collection failed: {e}")
        return state

    def _generate(self, state: BaseState) -> BaseState:
        """Generate insight summary."""
        jobs = state.get("metadata", {}).get("jobs", [])
        skills = state.get("metadata", {}).get("skills", [])
        state["output"] = f"Insights: {len(jobs)} jobs, {len(skills)} skills analyzed"
        return state
