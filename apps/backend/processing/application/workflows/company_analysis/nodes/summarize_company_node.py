"""SummarizeCompanyNode — finalizes the company summary for the result.

Ensures the recommendation/overview text is always present, falling back to a
generated summary from the extraction fields when missing.
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.workflow.company_processing_state import CompanyProcessingState

NODE_ID = "summarize_company"


class SummarizeCompanyNode:
    def __init__(self, event_publisher: Any | None = None):
        self._events = event_publisher

    def __call__(self, state: CompanyProcessingState) -> CompanyProcessingState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.analysis_result
        if result is not None:
            recommendation = result.get("recommendation") or {}
            if not recommendation.get("observation"):
                extraction = result.get("extraction") or {}
                recommendation["observation"] = (
                    f"{extraction.get('name') or 'This company'} is "
                    f"{extraction.get('industry') or 'an industry'} player "
                    f"{extraction.get('company_size') or ''}".strip()
                )
                result["recommendation"] = recommendation
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state
