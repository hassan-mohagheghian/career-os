"""Skill schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator


class SkillCreate(BaseModel):
    """Schema for creating a new skill."""
    name: str = Field(..., min_length=1)
    level: int = Field(1, ge=1, le=10)
    roles: str = ""
    path: str = ""
    source: str = "user"
    source_type: str = "user_input"
    category: str = ""
    categories: list[str] = []


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: str | None = None
    level: int | None = Field(None, ge=1, le=10)
    roles: str | None = None
    path: str | None = None
    source: str | None = None
    source_type: str | None = None
    category: str | None = None
    categories: list[str] | None = None
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


class SkillBreakdown(BaseModel):
    """Break a composite skill into atomic child skills."""
    child_names: list[str] = Field(..., min_length=2)


class SkillCanonicalChange(BaseModel):
    """Promote an alias to be the canonical name of a skill."""
    alias_name: str = Field(..., min_length=1)


class SkillBulkHide(BaseModel):
    ids: list[int]


class SkillBulkCategorize(BaseModel):
    ids: list[int]
    category: str


class SkillCategoryUpdate(BaseModel):
    category: str


class SkillCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)


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
    categories: list[str] = []
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
    categories: list[str] = []
    confidence: float | None = None
    market_relevance: float | None = None
    evidence: str | None = None
    tags: list[str] = []
    aliases: list[str] = []
    source_type: str = "user_input"
    mention_count: int = 0
    pinned: bool = False
    notes: list[SkillNoteSchema] = []
    links: list[SkillLinkSchema] = []
    created_at: str | None = None


class SkillListResponseSchema(BaseModel):
    """Cursor-paginated skill list response."""

    items: list[SkillListItemSchema] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    total_items: int = 0


class SkillJobRefSchema(BaseModel):
    """A job that mentions a skill (used by the skill detail drawer)."""

    id: str
    title: str = ""
    company: str | None = None
    location: str | None = None
    fit_score: int | None = None
    success_score: int | None = None
    overall_score: int | None = None
    pinned: bool = False
    status: str = ""
    created_at: str | None = None


class SkillJobsResponseSchema(BaseModel):
    """Jobs that mention a skill."""

    jobs: list[SkillJobRefSchema] = Field(default_factory=list)
    total: int = 0


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


class CreateSkillNoteRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("content must not be empty")
        return v.strip()


class SkillNoteSchema(BaseModel):
    id: int
    skill_id: int
    content: str = ""
    created_at: str | None = None
    updated_at: str | None = None


class CreateSkillLinkRequest(BaseModel):
    title: str
    url: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("url must not be empty")
        return v.strip()


class SkillLinkSchema(BaseModel):
    id: int
    skill_id: int
    title: str
    url: str
    created_at: str | None = None
