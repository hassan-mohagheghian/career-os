"""Pydantic schemas for the Roadmaps API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from roadmaps.domain.entities.roadmap import GoalType, RoadmapStatus


# ── Requests ─────────────────────────────────────────────────────────


class CreateRoadmapRequest(BaseModel):
    title: str = ""
    description: str = ""
    goal: dict[str, Any] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        return str(v or "").strip() or "Untitled Roadmap"


class UpdateRoadmapRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    goal: dict[str, Any] | None = None


class CreateMilestoneRequest(BaseModel):
    title: str = ""
    description: str = ""
    priority: str = "MEDIUM"


class UpdateMilestoneRequest(BaseModel):
    position: int | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None


class CreateTaskRequest(BaseModel):
    title: str = ""
    description: str = ""
    priority: str = "MEDIUM"
    estimated_effort: str | None = None
    success_criteria: str | None = None


class UpdateTaskRequest(BaseModel):
    position: int | None = None
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    estimated_effort: str | None = None
    success_criteria: str | None = None


class CreateNoteRequest(BaseModel):
    content: str = ""
    milestone_id: str | None = None
    task_id: str | None = None


class CreateResourceRequest(BaseModel):
    title: str = ""
    url: str = ""
    description: str = ""
    type: str = "OTHER"
    milestone_id: str | None = None
    task_id: str | None = None


class UpdateResourceRequest(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    type: str | None = None
    status: str | None = None


class LinkSkillRequest(BaseModel):
    skill_name: str = ""
    milestone_id: str | None = None
    task_id: str | None = None


# ── Responses ────────────────────────────────────────────────────────


class RoadmapGoalSchema(BaseModel):
    id: str
    roadmap_id: str
    type: str = GoalType.CUSTOM
    title: str = ""
    description: str = ""
    target_job_id: str | None = None
    target_company_id: str | None = None
    target_skill_id: str | None = None


class RoadmapMilestoneSchema(BaseModel):
    id: str
    roadmap_id: str
    position: int = 0
    title: str = ""
    description: str = ""
    status: str = "NOT_STARTED"
    priority: str = "MEDIUM"
    tasks: list["RoadmapTaskSchema"] = Field(default_factory=list)
    skills: list["RoadmapSkillLinkSchema"] = Field(default_factory=list)


class RoadmapTaskSchema(BaseModel):
    id: str
    milestone_id: str
    position: int = 0
    title: str = ""
    description: str = ""
    status: str = "NOT_STARTED"
    priority: str = "MEDIUM"
    estimated_effort: str | None = None
    success_criteria: str | None = None
    completed_at: str | None = None
    skills: list["RoadmapSkillLinkSchema"] = Field(default_factory=list)


class RoadmapSkillLinkSchema(BaseModel):
    id: str
    roadmap_id: str
    milestone_id: str | None = None
    task_id: str | None = None
    skill_id: str = ""
    skill_name: str = ""


class RoadmapNoteSchema(BaseModel):
    id: str
    roadmap_id: str
    milestone_id: str | None = None
    task_id: str | None = None
    content: str = ""
    created_at: str | None = None


class RoadmapResourceSchema(BaseModel):
    id: str
    roadmap_id: str
    milestone_id: str | None = None
    task_id: str | None = None
    title: str = ""
    url: str = ""
    description: str = ""
    type: str = "OTHER"
    status: str = "PLANNED"
    source: str = "USER"
    created_at: str | None = None


class MilestoneProgressSchema(BaseModel):
    milestone_id: str
    completed: int = 0
    total: int = 0
    percent: int = 0


class RoadmapProgressSchema(BaseModel):
    completed_tasks: int = 0
    total_tasks: int = 0
    overall_percent: int = 0
    milestone_progress: list[MilestoneProgressSchema] = Field(default_factory=list)


class RoadmapSummarySchema(BaseModel):
    id: str
    title: str = ""
    description: str = ""
    goal_type: str = GoalType.CUSTOM
    source: str = "MANUAL"
    application_id: str | None = None
    status: str = RoadmapStatus.ACTIVE
    progress: RoadmapProgressSchema
    created_at: str | None = None
    updated_at: str | None = None


class RoadmapDetailResponse(RoadmapSummarySchema):
    goal: RoadmapGoalSchema | None = None
    milestones: list[RoadmapMilestoneSchema] = Field(default_factory=list)
    notes: list[RoadmapNoteSchema] = Field(default_factory=list)
    resources: list[RoadmapResourceSchema] = Field(default_factory=list)


class DeleteResponse(BaseModel):
    status: str = "deleted"


RoadmapTaskSchema.model_rebuild()
RoadmapMilestoneSchema.model_rebuild()


def build_goal_schema(goal: dict[str, Any] | None) -> RoadmapGoalSchema | None:
    if not goal:
        return None
    return RoadmapGoalSchema(**goal)


def build_progress_schema(progress: dict[str, Any]) -> RoadmapProgressSchema:
    return RoadmapProgressSchema(
        completed_tasks=progress.get("completed_tasks", 0),
        total_tasks=progress.get("total_tasks", 0),
        overall_percent=progress.get("overall_percent", 0),
        milestone_progress=[
            MilestoneProgressSchema(**m) for m in progress.get("milestone_progress") or []
        ],
    )


def build_roadmap_summary(roadmap: dict[str, Any], progress: dict[str, Any]) -> RoadmapSummarySchema:
    return RoadmapSummarySchema(
        id=roadmap["id"],
        title=roadmap.get("title", ""),
        description=roadmap.get("description", ""),
        goal_type=roadmap.get("goal_type", GoalType.CUSTOM),
        source=roadmap.get("source", "MANUAL"),
        application_id=roadmap.get("application_id"),
        status=roadmap.get("status", RoadmapStatus.ACTIVE),
        progress=build_progress_schema(progress),
        created_at=roadmap.get("created_at"),
        updated_at=roadmap.get("updated_at"),
    )


def build_roadmap_detail(
    roadmap: dict[str, Any],
    goal: dict[str, Any] | None,
    milestones: list[dict[str, Any]],
    tasks_by_milestone: dict[str, list[dict[str, Any]]],
    skills: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    progress: dict[str, Any],
) -> RoadmapDetailResponse:
    skill_by_node: dict[str, list[dict[str, Any]]] = {}
    for s in skills:
        if s.get("milestone_id"):
            skill_by_node.setdefault(f"m:{s['milestone_id']}", []).append(s)
        if s.get("task_id"):
            skill_by_node.setdefault(f"t:{s['task_id']}", []).append(s)

    milestone_schemas: list[RoadmapMilestoneSchema] = []
    for ms in milestones:
        task_schemas: list[RoadmapTaskSchema] = []
        for t in tasks_by_milestone.get(ms["id"], []):
            task_schemas.append(
                RoadmapTaskSchema(
                    **t,
                    skills=[
                        RoadmapSkillLinkSchema(**s) for s in skill_by_node.get(f"t:{t['id']}", [])
                    ],
                )
            )
        milestone_schemas.append(
            RoadmapMilestoneSchema(
                **ms,
                tasks=task_schemas,
                skills=[
                    RoadmapSkillLinkSchema(**s) for s in skill_by_node.get(f"m:{ms['id']}", [])
                ],
            )
        )

    return RoadmapDetailResponse(
        **build_roadmap_summary(roadmap, progress).model_dump(),
        goal=build_goal_schema(goal),
        milestones=milestone_schemas,
        notes=[RoadmapNoteSchema(**n) for n in notes],
        resources=[RoadmapResourceSchema(**r) for r in resources],
    )


__all__ = [
    "CreateRoadmapRequest",
    "UpdateRoadmapRequest",
    "CreateMilestoneRequest",
    "UpdateMilestoneRequest",
    "CreateTaskRequest",
    "UpdateTaskRequest",
    "CreateNoteRequest",
    "CreateResourceRequest",
    "UpdateResourceRequest",
    "LinkSkillRequest",
    "RoadmapGoalSchema",
    "RoadmapMilestoneSchema",
    "RoadmapTaskSchema",
    "RoadmapSkillLinkSchema",
    "RoadmapNoteSchema",
    "RoadmapResourceSchema",
    "RoadmapProgressSchema",
    "RoadmapSummarySchema",
    "RoadmapDetailResponse",
    "DeleteResponse",
    "build_roadmap_summary",
    "build_roadmap_detail",
]