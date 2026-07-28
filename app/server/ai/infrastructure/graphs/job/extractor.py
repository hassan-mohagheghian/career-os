"""Job Extractor Agent — extracts and validates job posting data.

SRP: Only handles extraction and validation.
Strategy Pattern: Different extraction strategies for different input types.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import BaseState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class JobExtractorAgent:
    """Extracts structured job data from raw text.

    Workflow: validate → extract_raw → extract_struct

    Agents are thin layers — business logic stays in existing services.
    This agent orchestrates the extraction pipeline via the executor.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[BaseState] = None) -> BaseState:
        """Run the extraction pipeline."""
        if state is None:
            state = create_initial_state()

        if self._provider:
            state["context"]["provider"] = self._provider

        nodes = [
            ("validate", self._validate),
            ("extract_raw", self._extract_raw),
            ("extract_struct", self._extract_struct),
        ]
        return self._executor.execute_chain(nodes, state)

    def _validate(self, state: BaseState) -> BaseState:
        """Validate that the input contains job content."""
        content = state["input"]
        if not content or len(content) < 50:
            state["errors"].append("Content too short to be a valid job posting")
        state["metadata"]["content_length"] = len(content)
        return state

    def _extract_raw(self, state: BaseState) -> BaseState:
        """Extract raw job information using existing services."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from services.worker import _extract_all

            pid = state["context"].get("pid", "ai_extract")
            result = _extract_all(state["input"], pid)
            if result:
                state["metadata"]["extraction"] = result
                state["metadata"]["valid"] = result.get("valid", False)
        except Exception as e:
            state["errors"].append(f"Raw extraction failed: {e}")
        return state

    def _extract_struct(self, state: BaseState) -> BaseState:
        """Process structured extraction results."""
        extraction = state.get("metadata", {}).get("extraction")
        if extraction:
            state["output"] = str(extraction)
        return state
