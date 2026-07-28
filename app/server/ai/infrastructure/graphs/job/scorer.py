"""Job Scorer Agent — scores job fit and success probability.

SRP: Only handles scoring logic.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import AgentState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class JobScorerAgent:
    """Scores a job for fit and success probability.

    Uses existing scoring logic from worker.py.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[AgentState] = None) -> AgentState:
        """Run the scoring pipeline."""
        if state is None:
            state = create_initial_state()

        nodes = [
            ("compute_scores", self._compute_scores),
            ("normalize", self._normalize),
        ]
        return self._executor.execute_chain(nodes, state)

    def _compute_scores(self, state: AgentState) -> AgentState:
        """Compute fit and success scores."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from services.worker import normalize_score

            extraction = state.get("metadata", {}).get("extraction", {})
            if isinstance(extraction, dict):
                score = normalize_score(extraction.get("score", "P"))
                state["metadata"]["score"] = score
                state["metadata"]["fit_score"] = extraction.get("fit_score")
                state["metadata"]["success_score"] = extraction.get("success_score")
        except Exception as e:
            state["errors"].append(f"Scoring failed: {e}")
        return state

    def _normalize(self, state: AgentState) -> AgentState:
        """Normalize scores to standard format."""
        return state
