"""Company Evaluator Agent — generates intelligence analysis for companies.

SRP: Only handles company evaluation and scoring.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import AgentState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class CompanyEvaluatorAgent:
    """Evaluates a company and generates intelligence analysis.

    Uses existing analysis logic from company_worker.py.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[AgentState] = None) -> AgentState:
        if state is None:
            state = create_initial_state()

        nodes = [
            ("analyze", self._analyze),
            ("score", self._score),
        ]
        return self._executor.execute_chain(nodes, state)

    def _analyze(self, state: AgentState) -> AgentState:
        """Generate intelligence analysis."""
        company_data = state.get("metadata", {}).get("company_data", {})
        if not company_data:
            state["errors"].append("No company data to analyze")
            return state

        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from services.company_worker import _analyze_company, _load_rules

            pid = state["context"].get("pid", "ai_analyze")
            company_type = company_data.get("company_type", "UNKNOWN")
            rules = _load_rules(context='company', company_type=company_type)

            result = _analyze_company(company_data, pid, company_type=company_type)
            if result:
                state["metadata"]["intelligence"] = result
                state["metadata"]["rules"] = rules
        except Exception as e:
            state["errors"].append(f"Analysis failed: {e}")
        return state

    def _score(self, state: AgentState) -> AgentState:
        """Extract scores from intelligence data."""
        intelligence = state.get("metadata", {}).get("intelligence", {})
        if isinstance(intelligence, dict):
            scores = intelligence.get("scores", {})
            state["metadata"]["scores"] = scores
            state["output"] = str(intelligence)
        return state
