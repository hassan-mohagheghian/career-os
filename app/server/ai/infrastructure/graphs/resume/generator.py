"""Resume Agent — generates tailored resume content for job applications.

SRP: Only handles resume generation and tailoring.
"""

from __future__ import annotations

from typing import Optional

from ..runtime.state import AgentState, create_initial_state
from ..runtime.executor import AgentExecutor
from ...providers.base import LLMProvider


class ResumeAgent:
    """Generates tailored resume content for specific job postings.

    Uses existing resume data and job analysis to produce
    customized resume suggestions.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._executor = AgentExecutor()

    def execute(self, state: Optional[AgentState] = None) -> AgentState:
        if state is None:
            state = create_initial_state()

        nodes = [
            ("load_resume", self._load_resume),
            ("tailor", self._tailor),
        ]
        return self._executor.execute_chain(nodes, state)

    def _load_resume(self, state: AgentState) -> AgentState:
        """Load the user's base resume from DB."""
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server'))
            from core.db import get_db

            conn = get_db()
            row = conn.execute(
                "SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1"
            ).fetchone()
            conn.close()

            if row and row[0]:
                state["metadata"]["resume_text"] = row[0]
            else:
                state["errors"].append("No base resume found in database")
        except Exception as e:
            state["errors"].append(f"Failed to load resume: {e}")
        return state

    def _tailor(self, state: AgentState) -> AgentState:
        """Tailor resume content for the target job."""
        resume = state.get("metadata", {}).get("resume_text", "")
        if resume:
            state["output"] = resume
        return state
