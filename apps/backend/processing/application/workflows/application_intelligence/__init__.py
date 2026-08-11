"""Application Intelligence workflow — generates application artifacts
(preparation plan / tailored resume / cover letter) as a consumer of existing
Career Intelligence and persists them.

Runs exactly one LLM call per artifact. The grounded input is assembled from
the persisted job analysis, company intelligence and candidate profile.
"""

from processing.application.workflows.application_intelligence.graph import (
    ApplicationIntelligenceGraph,
)

__all__ = ["ApplicationIntelligenceGraph"]
