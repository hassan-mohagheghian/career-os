"""ApplicationWorkflowStepMapper — maps internal application generation node
names to user-facing WorkflowSteps.

LangGraph internals are never exposed to clients. This mapper is the only place
that knows the node_name → step title mapping for the application intelligence
workflow (tailored resume / cover letter generation).
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

WORKFLOW_ID = "application_generation"
WORKFLOW_NAME = "Application Generation"

# node_name → (step_id, step_title)
NODE_TO_STEP: dict[str, tuple[str, str]] = {
    "load_context": ("load_context", "Load Context"),
    "generate": ("generate", "Generate"),
    "persist": ("persist", "Save Result"),
    "application_ready": ("application_ready", "Generation Ready"),
    "execution_failed": ("execution_failed", "Execution Failed"),
}

# Ordered user-facing step ids for the application generation workflow.
WORKFLOW_STEP_IDS = [
    "load_context",
    "generate",
    "persist",
]

# Internal nodes that must never be rendered by the frontend.
HIDDEN_NODE_IDS = {
    "execution_failed",
    "application_ready",
}


class ApplicationWorkflowStepMapper:
    @staticmethod
    def step_for_node(node_id: str) -> tuple[str, str]:
        """Return the (step_id, step_title) for an internal node name."""
        return NODE_TO_STEP.get(node_id, (node_id, node_id.replace("_", " ").title()))

    @staticmethod
    def is_displayable(node_id: str) -> bool:
        step_id, _ = ApplicationWorkflowStepMapper.step_for_node(node_id)
        return step_id not in HIDDEN_NODE_IDS

    @staticmethod
    def build_initial_progress(execution_id: str) -> WorkflowProgress:
        """Build a fully-pending WorkflowProgress tree for an application execution."""
        steps = [
            WorkflowStep(
                id=step_id,
                node_id=node_name,
                title=title,
                status=WorkflowStepStatus.PENDING,
                displayable=ApplicationWorkflowStepMapper.is_displayable(node_name),
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
