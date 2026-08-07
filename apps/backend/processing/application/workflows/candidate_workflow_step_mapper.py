"""CandidateWorkflowStepMapper — maps internal candidate processing node names
to user-facing WorkflowSteps.

LangGraph internals are never exposed to clients. This mapper is the only place
that knows the node_name → step title mapping for the combined Candidate
Processing workflow (source preparation + extraction/merge).
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

WORKFLOW_ID = "candidate_processing"
WORKFLOW_NAME = "Candidate Processing"

# node_name → (step_id, step_title)
NODE_TO_STEP: dict[str, tuple[str, str]] = {
    "load_profile": ("load_profile", "Load Profile"),
    "prepare_sources": ("prepare_sources", "Prepare Sources"),
    "sources_ready": ("sources_ready", "Sources Ready"),
    "extract": ("extract", "Extract Sources"),
    "merge": ("merge", "Merge Profile"),
    "candidate_ready": ("candidate_ready", "Profile Ready"),
    "execution_failed": ("execution_failed", "Execution Failed"),
}

# Ordered user-facing step ids for the combined candidate workflow.
WORKFLOW_STEP_IDS = [
    "load_profile",
    "prepare_sources",
    "extract",
    "merge",
]

# Internal nodes that must never be rendered by the frontend.
HIDDEN_NODE_IDS = {
    "execution_failed",
    "sources_ready",
    "candidate_ready",
}


class CandidateWorkflowStepMapper:
    @staticmethod
    def step_for_node(node_id: str) -> tuple[str, str]:
        """Return the (step_id, step_title) for an internal node name."""
        return NODE_TO_STEP.get(node_id, (node_id, node_id.replace("_", " ").title()))

    @staticmethod
    def is_displayable(node_id: str) -> bool:
        step_id, _ = CandidateWorkflowStepMapper.step_for_node(node_id)
        return step_id not in HIDDEN_NODE_IDS

    @staticmethod
    def build_initial_progress(execution_id: str) -> WorkflowProgress:
        """Build a fully-pending WorkflowProgress tree for a candidate execution."""
        steps = [
            WorkflowStep(
                id=step_id,
                node_id=node_name,
                title=title,
                status=WorkflowStepStatus.PENDING,
                displayable=CandidateWorkflowStepMapper.is_displayable(node_name),
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
