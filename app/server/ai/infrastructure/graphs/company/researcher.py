"""Company Researcher Agent — extracts and researches company data.

SRP: Only handles company data extraction and research.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import BaseState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class CompanyResearcherAgent:
    """Extracts structured company data from multiple sources.

    Workflow: fetch → extract → prepare
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[BaseState] = None) -> BaseState:
        if state is None:
            state = create_initial_state()

        if self._provider:
            state["context"]["provider"] = self._provider

        nodes = [
            ("fetch", self._fetch),
            ("extract", self._extract),
        ]
        return self._executor.execute_chain(nodes, state)

    def _fetch(self, state: BaseState) -> BaseState:
        """Fetch company content from provided sources."""
        content = state["input"]
        state["metadata"]["content_length"] = len(content)
        return state

    def _extract(self, state: BaseState) -> BaseState:
        """Extract structured company data."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from services.company_worker import _extract_company_info

            pid = state["context"].get("pid", "ai_company")
            result = _extract_company_info(state["input"], "multi_note", pid)
            if result:
                state["metadata"]["company_data"] = result
                state["output"] = str(result)
        except Exception as e:
            state["errors"].append(f"Company extraction failed: {e}")
        return state
