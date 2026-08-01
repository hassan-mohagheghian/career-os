"""WorkflowStepMapper — maps internal LangGraph node names to user-facing
WorkflowSteps.

LangGraph internals are never exposed to clients. This mapper is the only place
that knows the node_name → step title mapping for the Job Context Preparation
workflow.
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

WORKFLOW_ID = "job_context_preparation"
WORKFLOW_NAME = "Job Context Preparation"

# node_name → (step_id, step_title)
NODE_TO_STEP: dict[str, tuple[str, str]] = {
    "load_job": ("load_job", "Load Job"),
    "collect_sources": ("collect_sources", "Collect Sources"),
    "fetch_sources": ("fetch_sources", "Fetch Content"),
    "extract_content": ("extract_content", "Extract Content"),
    "build_context": ("build_context", "Build Context"),
    "validate_context": ("validate_context", "Validate Context"),
    "context_ready": ("context_ready", "Ready For Analysis"),
    "execution_failed": ("execution_failed", "Execution Failed"),
}

# Ordered user-facing step ids for the context preparation workflow.
WORKFLOW_STEP_IDS = [
    "load_job",
    "collect_sources",
    "fetch_sources",
    "extract_content",
    "build_context",
    "validate_context",
]

# Internal nodes that must never be rendered by the frontend.
HIDDEN_NODE_IDS = {"execution_failed"}


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
