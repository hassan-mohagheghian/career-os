"""Roadmaps API router — the Roadmap Workspace backend.

Owned by the Roadmaps bounded context (per-context router, rule 10). Serves
manual roadmap CRUD, milestone/task/note/resource management, skill linking and
progress. AI generation entry points are dispatched from the Applications router
(prompt 146) and persisted into this context.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status as http_status

from dependencies import (
    get_roadmap_repo,
    get_roadmap_service,
)
from roadmaps.application.services.roadmap_service import RoadmapService
from roadmaps.infrastructure import SQLAlchemyRoadmapRepository
from roadmaps.presentation.api.schemas.roadmaps import (
    CreateMilestoneRequest,
    CreateNoteRequest,
    CreateResourceRequest,
    CreateRoadmapRequest,
    CreateTaskRequest,
    DeleteResponse,
    LinkSkillRequest,
    RoadmapDetailResponse,
    RoadmapMilestoneSchema,
    RoadmapNoteSchema,
    RoadmapResourceSchema,
    RoadmapSkillLinkSchema,
    RoadmapSummarySchema,
    RoadmapTaskSchema,
    UpdateMilestoneRequest,
    UpdateResourceRequest,
    UpdateRoadmapRequest,
    UpdateTaskRequest,
    build_roadmap_detail,
    build_roadmap_summary,
)
from shared.application.exceptions import BadRequestError, NotFoundError

router = APIRouter()


def _load_roadmap(
    roadmap_repo: SQLAlchemyRoadmapRepository,
    service: RoadmapService,
    roadmap_id: str,
) -> RoadmapDetailResponse:
    roadmap = roadmap_repo.get_by_id(roadmap_id)
    if not roadmap:
        raise NotFoundError(f"Roadmap {roadmap_id} not found")
    tasks_by_milestone: dict[str, list[dict]] = {}
    for ms in roadmap_repo.list_milestones(roadmap_id):
        tasks_by_milestone[ms["id"]] = roadmap_repo.list_tasks(ms["id"])
    return build_roadmap_detail(
        roadmap,
        roadmap_repo.get_goal(roadmap_id),
        roadmap_repo.list_milestones(roadmap_id),
        tasks_by_milestone,
        roadmap_repo.list_skills(roadmap_id),
        roadmap_repo.list_notes(roadmap_id),
        roadmap_repo.list_resources(roadmap_id),
        service.compute_progress(roadmap_id),
    )


@router.get("", response_model=list[RoadmapSummarySchema])
def list_roadmaps(
    roadmap_repo=Depends(get_roadmap_repo),
    service: RoadmapService = Depends(get_roadmap_service),
):
    return [
        build_roadmap_summary(r, service.compute_progress(r["id"]))
        for r in roadmap_repo.list()
    ]


@router.get("/by-application/{application_id}", response_model=RoadmapDetailResponse)
def get_roadmap_by_application(
    application_id: str,
    roadmap_repo=Depends(get_roadmap_repo),
    service: RoadmapService = Depends(get_roadmap_service),
):
    roadmap = roadmap_repo.get_by_application_id(application_id)
    if not roadmap:
        raise NotFoundError(f"No roadmap found for application {application_id}")
    return _load_roadmap(roadmap_repo, service, roadmap["id"])


@router.post("", status_code=http_status.HTTP_201_CREATED, response_model=RoadmapDetailResponse)
def create_roadmap(
    body: CreateRoadmapRequest,
    roadmap_repo=Depends(get_roadmap_repo),
    service: RoadmapService = Depends(get_roadmap_service),
):
    stored = service.create_manual(body.title, body.description, body.goal)
    return _load_roadmap(roadmap_repo, service, stored["id"])


@router.get("/{roadmap_id}", response_model=RoadmapDetailResponse)
def get_roadmap(
    roadmap_id: str,
    roadmap_repo=Depends(get_roadmap_repo),
    service: RoadmapService = Depends(get_roadmap_service),
):
    return _load_roadmap(roadmap_repo, service, roadmap_id)


@router.patch("/{roadmap_id}", response_model=RoadmapDetailResponse)
def update_roadmap(
    roadmap_id: str,
    body: UpdateRoadmapRequest,
    roadmap_repo=Depends(get_roadmap_repo),
    service: RoadmapService = Depends(get_roadmap_service),
):
    data = body.model_dump(exclude_unset=True)
    service.update(roadmap_id, data)
    return _load_roadmap(roadmap_repo, service, roadmap_id)


@router.delete("/{roadmap_id}", response_model=DeleteResponse)
def delete_roadmap(
    roadmap_id: str,
    service: RoadmapService = Depends(get_roadmap_service),
):
    service.delete(roadmap_id)
    return DeleteResponse(status="deleted")


# ── Milestones ───────────────────────────────────────────────────────


@router.post("/{roadmap_id}/milestones", status_code=http_status.HTTP_201_CREATED, response_model=RoadmapMilestoneSchema)
def add_milestone(
    roadmap_id: str,
    body: CreateMilestoneRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.add_milestone(roadmap_id, body.title, body.description, body.priority)


@router.patch("/milestones/{milestone_id}", response_model=RoadmapMilestoneSchema)
def update_milestone(
    milestone_id: str,
    body: UpdateMilestoneRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.update_milestone(milestone_id, body.model_dump(exclude_unset=True))


@router.delete("/milestones/{milestone_id}", response_model=DeleteResponse)
def delete_milestone(
    milestone_id: str,
    service: RoadmapService = Depends(get_roadmap_service),
):
    service.delete_milestone(milestone_id)
    return DeleteResponse(status="deleted")


# ── Tasks ────────────────────────────────────────────────────────────


@router.post("/milestones/{milestone_id}/tasks", status_code=http_status.HTTP_201_CREATED, response_model=RoadmapTaskSchema)
def add_task(
    milestone_id: str,
    body: CreateTaskRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.add_task(
        milestone_id,
        body.title,
        body.description,
        body.priority,
        body.estimated_effort,
        body.success_criteria,
    )


@router.patch("/tasks/{task_id}", response_model=RoadmapTaskSchema)
def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.update_task(task_id, body.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", response_model=DeleteResponse)
def delete_task(
    task_id: str,
    service: RoadmapService = Depends(get_roadmap_service),
):
    service.delete_task(task_id)
    return DeleteResponse(status="deleted")


# ── Notes ────────────────────────────────────────────────────────────


@router.post("/{roadmap_id}/notes", status_code=http_status.HTTP_201_CREATED, response_model=RoadmapNoteSchema)
def add_note(
    roadmap_id: str,
    body: CreateNoteRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.add_note(roadmap_id, body.content, body.milestone_id, body.task_id)


@router.delete("/notes/{note_id}", response_model=DeleteResponse)
def delete_note(
    note_id: str,
    service: RoadmapService = Depends(get_roadmap_service),
):
    service.delete_note(note_id)
    return DeleteResponse(status="deleted")


# ── Resources ────────────────────────────────────────────────────────


@router.post("/{roadmap_id}/resources", status_code=http_status.HTTP_201_CREATED, response_model=RoadmapResourceSchema)
def add_resource(
    roadmap_id: str,
    body: CreateResourceRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.add_resource(
        roadmap_id,
        body.title,
        body.url,
        body.description,
        body.type,
        body.milestone_id,
        body.task_id,
    )


@router.patch("/resources/{resource_id}", response_model=RoadmapResourceSchema)
def update_resource(
    resource_id: str,
    body: UpdateResourceRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    return service.update_resource(resource_id, body.model_dump(exclude_unset=True))


@router.delete("/resources/{resource_id}", response_model=DeleteResponse)
def delete_resource(
    resource_id: str,
    service: RoadmapService = Depends(get_roadmap_service),
):
    service.delete_resource(resource_id)
    return DeleteResponse(status="deleted")


# ── Skills ───────────────────────────────────────────────────────────


@router.post("/skills", status_code=http_status.HTTP_201_CREATED, response_model=RoadmapSkillLinkSchema)
def link_skill(
    body: LinkSkillRequest,
    service: RoadmapService = Depends(get_roadmap_service),
):
    roadmap_id = _roadmap_id_for_node(service, body.milestone_id, body.task_id)
    return service.link_skill(
        roadmap_id,
        body.skill_name,
        body.milestone_id,
        body.task_id,
    )


@router.delete("/skills/{link_id}", response_model=DeleteResponse)
def unlink_skill(
    link_id: str,
    service: RoadmapService = Depends(get_roadmap_service),
):
    service.unlink_skill(link_id)
    return DeleteResponse(status="deleted")


# ── helpers ──────────────────────────────────────────────────────────


def _roadmap_id_for_node(service: RoadmapService, milestone_id: str | None, task_id: str | None) -> str:
    if task_id:
        task = service._repo.get_task(task_id)
        if task:
            milestone = service._repo.get_milestone(task["milestone_id"])
            if milestone:
                return milestone["roadmap_id"]
    if milestone_id:
        milestone = service._repo.get_milestone(milestone_id)
        if milestone:
            return milestone["roadmap_id"]
    raise BadRequestError("link_skill requires a milestone_id or task_id")