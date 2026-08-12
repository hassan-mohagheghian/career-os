"""RoadmapWorkflowStepMapper — maps internal roadmap generation node names to
user-facing WorkflowSteps.

LangGraph internals are never exposed to clients. This mapper is the only place
that knows the node_name → step title mapping for the roadmap generation
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

WORKFLOW_ID = "roadmap_generation"
WORKFLOW_NAME = "Roadmap Generation"

# node_name → (step_id, step_title)
NODE_TO_STEP: dict[str, tuple[str, str]] = {
    "load_context": ("load_context", "Load Context"),
    "generate": ("generate", "Generate"),
    "persist": ("persist", "Save Result"),
    "roadmap_ready": ("roadmap_ready", "Roadmap Ready"),
    "execution_failed": ("execution_failed", "Execution Failed"),
}

# Ordered user-facing step ids for the roadmap generation workflow.
WORKFLOW_STEP_IDS = [
    "load_context",
    "generate",
    "persist",
]

# Internal nodes that must never be rendered by the frontend.
HIDDEN_NODE_IDS = {
    "execution_failed",
    "roadmap_ready",
}


class RoadmapWorkflowStepMapper:
    @staticmethod
    def step_for_node(node_id: str) -> tuple[str, str]:
        """Return the (step_id, step_title) for an internal node name."""
        return NODE_TO_STEP.get(node_id, (node_id, node_id.replace("_", " ").title()))

    @staticmethod
    def is_displayable(node_id: str) -> bool:
        step_id, _ = RoadmapWorkflowStepMapper.step_for_node(node_id)
        return step_id not in HIDDEN_NODE_IDS

    @staticmethod
    def build_initial_progress(execution_id: str) -> WorkflowProgress:
        """Build a fully-pending WorkflowProgress tree for a roadmap execution."""
        steps = [
            WorkflowStep(
                id=step_id,
                node_id=node_name,
                title=title,
                status=WorkflowStepStatus.PENDING,
                displayable=RoadmapWorkflowStepMapper.is_displayable(node_name),
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