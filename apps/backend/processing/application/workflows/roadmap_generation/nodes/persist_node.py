"""PersistNode — writes the AI-generated roadmap into the Roadmaps context.

Builds the Roadmap aggregate through RoadmapService (the single owner of the
Roadmap business operations):

    Roadmap (source=APPLICATION, application_id, goal_type=JOB, status ACTIVE)
        ├── RoadmapGoal (type=JOB, target_job_id, target_company_id)
        └── Milestones (position 0..n)
            ├── RoadmapTask (position 0..n, status NOT_STARTED)
            └── RoadmapSkillLink (skill resolved via skill_repo.resolve_skill)

Domain events (RoadmapCreated, RoadmapMilestoneAdded, RoadmapTaskAdded,
RoadmapSkillLinked) are emitted by the service through the RoadmapEventPublisher
(best-effort, in-memory collector).
"""

from __future__ import annotations

from typing import Any

from processing.application.workflows import progress_ops
from processing.domain.enums import ExecutionStatus
from processing.domain.workflow.roadmap_generation_state import (
    RoadmapGenerationState,
)

NODE_ID = "persist"

_PRIORITY_UPPER = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}


class PersistNode:
    def __init__(
        self,
        roadmap_service: Any,
        job_service: Any,
        event_publisher: Any | None = None,
    ):
        self._roadmaps = roadmap_service
        self._jobs = job_service
        self._events = event_publisher

    def __call__(self, state: RoadmapGenerationState) -> RoadmapGenerationState:
        progress_ops.start_step(self._events, state, NODE_ID)
        result = state.result or {}
        if not result or not result.get("milestones"):
            state.errors.append(f"[{NODE_ID}] No generation result to persist")
            state.status = ExecutionStatus.FAILED
            progress_ops.complete_step(self._events, state, NODE_ID)
            return state

        try:
            state.persisted_roadmap_id = self._persist(state, result)
        except Exception as e:
            state.errors.append(f"[{NODE_ID}] Failed to persist roadmap: {e}")
            state.status = ExecutionStatus.FAILED
        progress_ops.complete_step(self._events, state, NODE_ID)
        return state

    def _persist(self, state: RoadmapGenerationState, result: dict[str, Any]) -> str:
        goal = result.get("goal") or {}
        job = self._jobs.get_job(state.job_id) if state.job_id else None
        company_id = (job or {}).get("company_id") if job else None

        roadmap = self._roadmaps.create_from_application(
            title=result.get("title") or "Job Preparation Roadmap",
            description=goal.get("description") or "",
            application_id=state.application_id,
            goal={
                "type": "JOB",
                "title": goal.get("title") or result.get("title") or "Get the job",
                "description": goal.get("description") or "",
                "target_job_id": state.job_id or None,
                "target_company_id": company_id,
            },
        )
        roadmap_id = roadmap["id"]

        for ms in result.get("milestones") or []:
            milestone = self._roadmaps.add_milestone(
                roadmap_id,
                title=ms.get("title") or "Milestone",
                description=ms.get("description") or "",
                priority=_PRIORITY_UPPER.get(str(ms.get("priority") or "medium").lower(), "MEDIUM"),
            )
            for skill_name in ms.get("skills") or []:
                self._roadmaps.link_skill(
                    roadmap_id,
                    skill_name,
                    milestone_id=milestone["id"],
                )
            for task in ms.get("tasks") or []:
                self._roadmaps.add_task(
                    milestone["id"],
                    title=task.get("title") or "Task",
                    description=task.get("description") or "",
                    priority=_PRIORITY_UPPER.get(str(task.get("priority") or "medium").lower(), "MEDIUM"),
                    estimated_effort=task.get("estimated_effort"),
                    success_criteria=task.get("success_criteria"),
                )
        return roadmap_id