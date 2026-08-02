"""Workflow progress operations.

Pure-ish helpers used by the workflow nodes (and the runner) to build and mutate
the user-facing WorkflowProgress tree for one execution. Every mutation also
emits a user-facing workflow.step.* event.

The tree lives inside JobProcessingState.workflow_progress so that LangGraph
nodes stay stateless over the execution; the runner persists the final tree onto
the ProcessingExecution record.
"""

from __future__ import annotations

import uuid
from datetime import datetime, UTC
from typing import Any, Iterable

from processing.application.workflows.workflow_step_mapper import WorkflowStepMapper
from processing.domain.workflow.job_processing_state import JobProcessingState
from processing.domain.workflow.workflow_progress import (
    WorkflowProgress,
    WorkflowProgressStatus,
)
from processing.domain.workflow.workflow_step import (
    WorkflowStep,
    WorkflowStepError,
    WorkflowStepStatus,
)
from shared.infrastructure.events import processing_events


def build_initial_progress(execution_id: str) -> WorkflowProgress:
    """Build a fully-pending WorkflowProgress for an execution."""
    return WorkflowStepMapper.build_initial_progress(execution_id)


def start_step(publisher: Any, state: JobProcessingState, node_id: str) -> WorkflowProgress:
    progress = _ensure_progress(state)
    step = _find(progress, node_id)
    if step is not None:
        step.status = WorkflowStepStatus.PROCESSING
        step.started_at = step.started_at or _now()
        progress.status = WorkflowProgressStatus.RUNNING
        progress.current_step = step
    _recompute(progress)
    state.workflow_progress = progress
    if step is not None:
        _emit_step_event(publisher, state, processing_events.WORKFLOW_STEP_STARTED, step)
    return progress


def complete_step(publisher: Any, state: JobProcessingState, node_id: str) -> WorkflowProgress:
    progress = _ensure_progress(state)
    step = _find(progress, node_id)
    if step is not None:
        step.status = WorkflowStepStatus.COMPLETED
        step.progress = 100.0
        step.completed_at = step.completed_at or _now()
        progress.current_step = None
    _recompute(progress)
    state.workflow_progress = progress
    if step is not None:
        _emit_step_event(publisher, state, processing_events.WORKFLOW_STEP_COMPLETED, step)
    return progress


def fail_step(
    publisher: Any,
    state: JobProcessingState,
    node_id: str,
    message: str,
    code: str = "PROCESSING_ERROR",
) -> WorkflowProgress:
    progress = _ensure_progress(state)
    step = _find(progress, node_id)
    if step is not None:
        step.status = WorkflowStepStatus.FAILED
        step.error = WorkflowStepError(code=code, message=message)
        step.completed_at = step.completed_at or _now()
        progress.status = WorkflowProgressStatus.FAILED
        progress.current_step = None
    _recompute(progress)
    state.workflow_progress = progress
    if step is not None:
        _emit_step_event(publisher, state, processing_events.WORKFLOW_STEP_FAILED, step)
    return progress


def update_step(
    publisher: Any,
    state: JobProcessingState,
    node_id: str,
    value: float,
) -> WorkflowProgress:
    progress = _ensure_progress(state)
    step = _find(progress, node_id)
    if step is not None:
        step.status = WorkflowStepStatus.PROCESSING
        step.progress = min(100.0, max(0.0, value))
        progress.status = WorkflowProgressStatus.RUNNING
        progress.current_step = step
    _recompute(progress)
    state.workflow_progress = progress
    if step is not None:
        _emit_step_event(publisher, state, processing_events.WORKFLOW_STEP_PROGRESS, step)
    return progress


def replace_children(
    publisher: Any,
    state: JobProcessingState,
    node_id: str,
    children: Iterable[dict[str, Any]],
) -> WorkflowProgress:
    """Replace the children of a step (e.g. per-source fetch steps)."""
    progress = _ensure_progress(state)
    step = _find(progress, node_id)
    if step is not None:
        step.children = [_child(c) for c in children]
        step.status = WorkflowStepStatus.PROCESSING
        progress.current_step = step
    _recompute(progress)
    state.workflow_progress = progress
    if step is not None:
        _emit_step_event(publisher, state, processing_events.WORKFLOW_STEP_PROGRESS, step)
    return progress


def update_child(
    publisher: Any,
    state: JobProcessingState,
    parent_node_id: str,
    child_id: str,
    status: WorkflowStepStatus,
    progress_value: float | None = None,
    error: str | None = None,
) -> WorkflowProgress:
    """Update a single child step and the parent's derived progress."""
    progress = _ensure_progress(state)
    parent = _find(progress, parent_node_id)
    child = None
    if parent is not None:
        child = next((c for c in parent.children if c.id == child_id), None)
    if child is not None:
        child.status = status
        if progress_value is not None:
            child.progress = min(100.0, max(0.0, progress_value))
        if error:
            child.error = WorkflowStepError(message=error)
        child.completed_at = child.completed_at or (_now() if status in (WorkflowStepStatus.COMPLETED, WorkflowStepStatus.FAILED) else None)
    _recompute(progress)
    state.workflow_progress = progress
    return progress


def finish_progress(publisher: Any, state: JobProcessingState) -> WorkflowProgress:
    """Mark the whole workflow as completed (called by terminal nodes)."""
    progress = _ensure_progress(state)
    if all(
        s.status in (WorkflowStepStatus.COMPLETED, WorkflowStepStatus.FAILED, WorkflowStepStatus.SKIPPED)
        for s in progress.steps
    ):
        progress.status = WorkflowProgressStatus.COMPLETED
    else:
        progress.status = WorkflowProgressStatus.RUNNING
    progress.current_step = None
    _recompute(progress)
    state.workflow_progress = progress
    return progress


def mark_failed(publisher: Any, state: JobProcessingState, message: str) -> WorkflowProgress:
    """Mark the whole workflow as failed."""
    progress = _ensure_progress(state)
    progress.status = WorkflowProgressStatus.FAILED
    progress.current_step = None
    state.workflow_progress = progress
    return progress


def _ensure_progress(state: JobProcessingState) -> WorkflowProgress:
    if state.workflow_progress is None:
        state.workflow_progress = build_initial_progress(state.execution_id)
    return state.workflow_progress


def _recompute(progress: WorkflowProgress) -> None:
    displayable = [s for s in progress.steps if s.displayable]
    if not displayable:
        progress.progress = 0.0
        return
    total = 0.0
    for step in displayable:
        if step.status in (WorkflowStepStatus.COMPLETED, WorkflowStepStatus.FAILED):
            total += 100.0
        elif step.status == WorkflowStepStatus.SKIPPED:
            total += 100.0
        else:
            total += step.progress or 0.0
    progress.progress = round(total / len(displayable), 1)


def _child(c: dict[str, Any]) -> WorkflowStep:
    data = dict(c)
    data.setdefault("id", f"child_{uuid.uuid4().hex[:8]}")
    data.setdefault("status", WorkflowStepStatus.PENDING.value)
    data.setdefault("displayable", True)
    data["node_id"] = data.get("node_id")
    return WorkflowStep.model_validate(data)


def _find(progress: WorkflowProgress, node_id: str) -> WorkflowStep | None:
    for step in progress.steps:
        if step.node_id == node_id or step.id == node_id:
            return step
        found = _find_in_children(step, node_id)
        if found is not None:
            return found
    return None


def _find_in_children(step: WorkflowStep, node_id: str) -> WorkflowStep | None:
    for child in step.children:
        if child.node_id == node_id or child.id == node_id:
            return child
        found = _find_in_children(child, node_id)
        if found is not None:
            return found
    return None


def _emit_step_event(publisher: Any, state: JobProcessingState, event: str, step: WorkflowStep) -> None:
    if publisher is None:
        return
    try:
        publisher.publish(
            event,
            state.execution_id,
            state.job_id,
            step.status.value,
            step=step.to_dict(),
        )
    except Exception:
        # Best-effort publishing must never break the workflow.
        pass


def _now() -> str:
    return datetime.now(UTC).isoformat()
