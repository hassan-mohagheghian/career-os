"""Skill schemas for request/response validation."""

from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    """Schema for creating a new skill."""
    name: str = Field(..., min_length=1)
    level: int = Field(1, ge=1, le=10)
    roles: str = ""
    path: str = ""
    source: str = "user"
    source_type: str = "user_input"
    category: str = ""


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: str | None = None
    level: int | None = Field(None, ge=1, le=10)
    roles: str | None = None
    path: str | None = None
    source: str | None = None
    source_type: str | None = None
    category: str | None = None
    confidence: float | None = None
    market_relevance: float | None = None
    evidence: str | None = None
    tags: list[str] | None = None


class SkillRename(BaseModel):
    name: str = Field(..., min_length=1)


class SkillHide(BaseModel):
    hidden: int = 1


class SkillMerge(BaseModel):
    target_id: int
    source_ids: list[int]


class SkillBulkHide(BaseModel):
    ids: list[int]


class SkillBulkCategorize(BaseModel):
    ids: list[int]
    category: str


class SkillCategoryUpdate(BaseModel):
    category: str


class SkillResponse(BaseModel):
    """Schema for skill response."""
    id: int
    name: str
    level: int = 1
    roles: str = ""
    path: str = ""
    source: str = ""
    source_type: str = ""
    category: str = ""
    confidence: float | None = None
    market_relevance: float | None = None
    evidence: str | None = None
    tags: list[str] = []
    aliases: list[str] = []
    hidden: int = 0

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    items: list[SkillResponse]


class CategoryResponse(BaseModel):
    category: str
    count: int
    avg_demand: float | None = None
    avg_level: float | None = None


class SkillStatsResponse(BaseModel):
    total: int
    hidden: int
    avg_level: float
    avg_demand: float
    by_source: dict[str, int]
    total_relationships: int
    total_aliases: int
    total_roadmaps: int


class SkillRelationshipResponse(BaseModel):
    id: int
    skill_name: str
    related_name: str
    relation_type: str
    confidence: float = 0


class SkillRelationshipCreate(BaseModel):
    skill_name: str
    related_name: str
    relation_type: str
    confidence: float = 0
