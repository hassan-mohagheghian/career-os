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


class SkillPinRequest(BaseModel):
    """Schema for pinning/unpinning a skill."""
    pinned: bool = True


class SkillRename(BaseModel):
    name: str = Field(..., min_length=1)


class SkillHide(BaseModel):
    hidden: int = 1


class SkillAliasAdd(BaseModel):
    alias_name: str = Field(..., min_length=1)


class SkillAliasRemove(BaseModel):
    alias_name: str = Field(..., min_length=1)


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
    pinned: bool = False

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    items: list[SkillResponse]


class SkillListItemSchema(BaseModel):
    """A single skill in the v2 list."""

    id: int
    name: str
    level: int = 1
    roles: str = ""
    path: str = ""
    category: str = ""
    confidence: float | None = None
    market_relevance: float | None = None
    evidence: str | None = None
    tags: list[str] = []
    aliases: list[str] = []
    source_type: str = "user_input"
    mention_count: int = 0
    pinned: bool = False
    created_at: str | None = None


class SkillListResponseSchema(BaseModel):
    """Cursor-paginated skill list response."""

    items: list[SkillListItemSchema] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    total_items: int = 0


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
