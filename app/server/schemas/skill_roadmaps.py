"""Skill roadmap schemas for request/response validation."""

from pydantic import BaseModel
from typing import Any


class RoadmapCreate(BaseModel):
    skill_name: str
    description: str | None = None


class RoadmapResponse(BaseModel):
    id: int
    skill_name: str
    tree: dict[str, Any] = {}
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class RoadmapListResponse(BaseModel):
    items: list[RoadmapResponse]


class GenerateRoadmapRequest(BaseModel):
    skill_name: str
    description: str | None = None


class ExtendRoadmapRequest(BaseModel):
    skill_name: str
    node_id: str
    depth: int = 2


class FinegrainRoadmapRequest(BaseModel):
    skill_name: str
    node_id: str


class RoadmapProgressResponse(BaseModel):
    skill_name: str
    completed_nodes: list[str] = []
    total_nodes: int = 0
    percentage: float = 0


class RoadmapProgressAllResponse(BaseModel):
    items: list[RoadmapProgressResponse]
