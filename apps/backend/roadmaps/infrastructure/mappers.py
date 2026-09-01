"""Mappers between SQLAlchemy models and dict representations."""

from __future__ import annotations

from typing import Any

from roadmaps.infrastructure.models.roadmap_model import (
    RoadmapGoalModel,
    RoadmapMilestoneModel,
    RoadmapModel,
    RoadmapNoteModel,
    RoadmapResourceModel,
    RoadmapSkillLinkModel,
    RoadmapTaskModel,
    _now_iso,
)


def roadmap_model_to_dict(model: RoadmapModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "title": model.title,
        "description": model.description,
        "goal_type": model.goal_type,
        "source": model.source,
        "application_id": model.application_id,
        "status": model.status,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_roadmap_model(data: dict[str, Any]) -> RoadmapModel:
    return RoadmapModel(
        id=data.get("id"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        goal_type=data.get("goal_type", "CUSTOM"),
        source=data.get("source", "MANUAL"),
        application_id=data.get("application_id"),
        status=data.get("status", "ACTIVE"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
        user_id=data.get("user_id", ""),
    )


def goal_model_to_dict(model: RoadmapGoalModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "roadmap_id": model.roadmap_id,
        "type": model.type,
        "title": model.title,
        "description": model.description,
        "target_job_id": model.target_job_id,
        "target_company_id": model.target_company_id,
        "target_skill_id": model.target_skill_id,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_goal_model(data: dict[str, Any]) -> RoadmapGoalModel:
    return RoadmapGoalModel(
        id=data.get("id"),
        roadmap_id=data.get("roadmap_id", ""),
        type=data.get("type", "CUSTOM"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        target_job_id=data.get("target_job_id"),
        target_company_id=data.get("target_company_id"),
        target_skill_id=data.get("target_skill_id"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def milestone_model_to_dict(model: RoadmapMilestoneModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "roadmap_id": model.roadmap_id,
        "position": model.position,
        "title": model.title,
        "description": model.description,
        "status": model.status,
        "priority": model.priority,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_milestone_model(data: dict[str, Any]) -> RoadmapMilestoneModel:
    return RoadmapMilestoneModel(
        id=data.get("id"),
        roadmap_id=data.get("roadmap_id", ""),
        position=data.get("position", 0),
        title=data.get("title", ""),
        description=data.get("description", ""),
        status=data.get("status", "NOT_STARTED"),
        priority=data.get("priority", "MEDIUM"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def task_model_to_dict(model: RoadmapTaskModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "milestone_id": model.milestone_id,
        "position": model.position,
        "title": model.title,
        "description": model.description,
        "status": model.status,
        "priority": model.priority,
        "estimated_effort": model.estimated_effort,
        "success_criteria": model.success_criteria,
        "completed_at": model.completed_at,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_task_model(data: dict[str, Any]) -> RoadmapTaskModel:
    return RoadmapTaskModel(
        id=data.get("id"),
        milestone_id=data.get("milestone_id", ""),
        position=data.get("position", 0),
        title=data.get("title", ""),
        description=data.get("description", ""),
        status=data.get("status", "NOT_STARTED"),
        priority=data.get("priority", "MEDIUM"),
        estimated_effort=data.get("estimated_effort"),
        success_criteria=data.get("success_criteria"),
        completed_at=data.get("completed_at"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def skill_link_model_to_dict(model: RoadmapSkillLinkModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "roadmap_id": model.roadmap_id,
        "milestone_id": model.milestone_id,
        "task_id": model.task_id,
        "skill_id": model.skill_id,
        "skill_name": model.skill_name,
        "position": model.position,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_skill_link_model(data: dict[str, Any]) -> RoadmapSkillLinkModel:
    return RoadmapSkillLinkModel(
        id=data.get("id"),
        roadmap_id=data.get("roadmap_id", ""),
        milestone_id=data.get("milestone_id"),
        task_id=data.get("task_id"),
        skill_id=data.get("skill_id", ""),
        skill_name=data.get("skill_name", ""),
        position=data.get("position", 0),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def note_model_to_dict(model: RoadmapNoteModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "roadmap_id": model.roadmap_id,
        "milestone_id": model.milestone_id,
        "task_id": model.task_id,
        "content": model.content,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_note_model(data: dict[str, Any]) -> RoadmapNoteModel:
    return RoadmapNoteModel(
        id=data.get("id"),
        roadmap_id=data.get("roadmap_id", ""),
        milestone_id=data.get("milestone_id"),
        task_id=data.get("task_id"),
        content=data.get("content", ""),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )


def resource_model_to_dict(model: RoadmapResourceModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "roadmap_id": model.roadmap_id,
        "milestone_id": model.milestone_id,
        "task_id": model.task_id,
        "title": model.title,
        "url": model.url,
        "description": model.description,
        "type": model.type,
        "status": model.status,
        "source": model.source,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
    }


def dict_to_resource_model(data: dict[str, Any]) -> RoadmapResourceModel:
    return RoadmapResourceModel(
        id=data.get("id"),
        roadmap_id=data.get("roadmap_id", ""),
        milestone_id=data.get("milestone_id"),
        task_id=data.get("task_id"),
        title=data.get("title", ""),
        url=data.get("url", ""),
        description=data.get("description", ""),
        type=data.get("type", "OTHER"),
        status=data.get("status", "PLANNED"),
        source=data.get("source", "USER"),
        created_at=data.get("created_at") or _now_iso(),
        updated_at=data.get("updated_at") or _now_iso(),
    )