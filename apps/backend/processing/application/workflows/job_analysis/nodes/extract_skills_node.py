"""ExtractSkillsNode — normalizes the job's required skills.

Tags each skill matched/missing/low relative to the user's profile and stores
the normalized list on the analysis context. The ScoreNode (which runs next
and builds the canonical analysis result) merges the list into the result.
"""

from __future__ import annotations

from typing import Any

from processing.application.services.job_analysis_scoring import normalize_skills
from processing.application.workflows import progress_ops
from processing.domain.workflow.job_processing_state import JobProcessingState

NODE_ID = "extract_skills"


class ExtractSkillsNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: JobProcessingState) -> JobProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        raw_skills = (state.analysis_context.get("raw_payload") or {}).get("skills")
        state.analysis_context["normalized_skills"] = normalize_skills(raw_skills)
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
