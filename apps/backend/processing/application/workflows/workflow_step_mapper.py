"""WorkflowStepMapper — maps internal LangGraph node names to user-facing
WorkflowSteps.

LangGraph internals are never exposed to clients. This mapper is the only place
that knows the node_name → step title mapping for the combined Job Processing
workflow (context preparation + analysis).
"""

from __future__ import annotations

from processing.domain.workflow.workflow_progress import (
    WorkflowProgress,
    WorkflowProgressStatus,
)
from processing.domain.workflow.workflow_step import (
    WorkflowStep,
    WorkflowStepStatus,
)

WORKFLOW_ID = "job_processing"
WORKFLOW_NAME = "Job Processing"

# node_name → (step_id, step_title)
NODE_TO_STEP: dict[str, tuple[str, str]] = {
    "load_job": ("load_job", "Load Job"),
    "collect_sources": ("collect_sources", "Collect Sources"),
    "fetch_sources": ("fetch_sources", "Fetch Content"),
    "extract_content": ("extract_content", "Extract Content"),
    "build_context": ("build_context", "Build Context"),
    "validate_context": ("validate_context", "Validate Context"),
    "persist_context": ("persist_context", "Save Context"),
    "context_ready": ("context_ready", "Ready For Analysis"),
    "load_context": ("load_context", "Load Context"),
    "prepare_profile": ("prepare_profile", "Prepare Profile"),
    "analyze": ("analyze", "Analyze Job"),
    "extract_skills": ("extract_skills", "Extract Skills"),
    "score": ("score", "Score Job"),
    "recommend": ("recommend", "Recommendation"),
    "summarize": ("summarize", "Summarize"),
    "persist": ("persist", "Save Results"),
    "analysis_ready": ("analysis_ready", "Analysis Ready"),
    "execution_failed": ("execution_failed", "Execution Failed"),
}

# Ordered user-facing step ids for the combined workflow.
WORKFLOW_STEP_IDS = [
    "load_job",
    "collect_sources",
    "fetch_sources",
    "extract_content",
    "build_context",
    "validate_context",
    "persist_context",
    "analyze",
    "extract_skills",
    "score",
    "recommend",
    "summarize",
    "persist",
]

# Internal nodes that must never be rendered by the frontend.
HIDDEN_NODE_IDS = {
    "execution_failed",
    "context_ready",
    "analysis_ready",
    "load_context",
    "prepare_profile",
}


class WorkflowStepMapper:
    @staticmethod
    def step_for_node(node_id: str) -> tuple[str, str]:
        """Return the (step_id, step_title) for an internal node name."""
        return NODE_TO_STEP.get(node_id, (node_id, node_id.replace("_", " ").title()))

    @staticmethod
    def is_displayable(node_id: str) -> bool:
        step_id, _ = WorkflowStepMapper.step_for_node(node_id)
        return step_id not in HIDDEN_NODE_IDS

    @staticmethod
    def build_initial_progress(execution_id: str) -> WorkflowProgress:
        """Build a fully-pending WorkflowProgress tree for a new execution."""
        steps = [
            WorkflowStep(
                id=step_id,
                node_id=node_name,
                title=title,
                status=WorkflowStepStatus.PENDING,
                displayable=WorkflowStepMapper.is_displayable(node_name),
            )
            for node_name, (step_id, title) in NODE_TO_STEP.items()
            if step_id in WORKFLOW_STEP_IDS
        ]
        return WorkflowProgress(
            id=WORKFLOW_ID,
            name=WORKFLOW_NAME,
            status=WorkflowProgressStatus.PENDING,
            current_step=None,
            progress=0.0,
            steps=steps,
        )
