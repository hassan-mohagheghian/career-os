"""Roadmap Generation workflow — generates a job-preparation roadmap from an
Application as a consumer of existing Career Intelligence and persists it into
the Roadmaps context.

Runs exactly one LLM call per roadmap. The grounded input is assembled from the
persisted job analysis, company intelligence and candidate profile.
"""

from processing.application.workflows.roadmap_generation.graph import (
    RoadmapGenerationGraph,
)

__all__ = ["RoadmapGenerationGraph"]