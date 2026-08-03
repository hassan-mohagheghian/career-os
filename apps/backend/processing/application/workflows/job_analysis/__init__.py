"""Job Analysis workflow — runs the single combined LLM analysis for a job
and persists the canonical result (fields, scores, recommendation, summary,
skills).

Runs after the Job Context Preparation workflow. The prepared context is read
from the job row (persisted by the prep phase), so the analysis input is
durable.
"""

from processing.application.workflows.job_analysis.graph import JobAnalysisGraph

__all__ = ["JobAnalysisGraph"]
