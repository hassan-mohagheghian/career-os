"""Job Analyzer Agent — analyzes job fit and generates insights.

SRP: Only handles job analysis and scoring preparation.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import BaseState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class JobAnalyzerAgent:
    """Analyzes a job posting for fit, stack, and requirements.

    Orchestrates the analysis pipeline. Business rules remain
    in existing worker.py services.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[BaseState] = None) -> BaseState:
        """Run the analysis pipeline."""
        if state is None:
            state = create_initial_state()

        if self._provider:
            state["context"]["provider"] = self._provider

        nodes = [
            ("load_rules", self._load_rules),
            ("analyze_stack", self._analyze_stack),
            ("prepare_output", self._prepare_output),
        ]
        return self._executor.execute_chain(nodes, state)

    def _load_rules(self, state: BaseState) -> BaseState:
        """Load scoring rules from DB."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from services.worker import _load_rules
            state["metadata"]["rules"] = _load_rules(context='job')
        except Exception as e:
            state["errors"].append(f"Failed to load rules: {e}")
        return state

    def _analyze_stack(self, state: BaseState) -> BaseState:
        """Analyze the tech stack from extracted data."""
        extraction = state.get("metadata", {}).get("extraction", {})
        stack = extraction.get("stack", "") if isinstance(extraction, dict) else ""
        state["metadata"]["tech_stack"] = stack
        return state

    def _prepare_output(self, state: BaseState) -> BaseState:
        """Prepare analysis output."""
        extraction = state.get("metadata", {}).get("extraction", {})
        state["output"] = str(extraction) if extraction else ""
        return state
