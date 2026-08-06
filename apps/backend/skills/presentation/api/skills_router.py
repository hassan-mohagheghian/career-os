"""Tech stack CRUD, skill relationships, merge, hide/restore."""

from __future__ import annotations

import base64
from typing import Any, Callable

from fastapi import APIRouter, Depends, Query

from dependencies import get_skill_repo
from skills.infrastructure import SQLAlchemySkillRepository
from skills.presentation.api.schemas.skills import (
    SkillCreate,
    SkillUpdate,
    SkillRename,
    SkillHide,
    SkillAliasAdd,
    SkillAliasRemove,
    SkillMerge,
    SkillBulkHide,
    SkillBulkCategorize,
    SkillCategoryUpdate,
    SkillListItemSchema,
    SkillListResponseSchema,
)
from shared.application.exceptions import NotFoundError, BadRequestError, ConflictError

router = APIRouter()

DEFAULT_PAGE_SIZE = 25

SKILL_CATEGORIES = ("technical", "engineering", "professional", "domain", "career")

SORTABLE_SKILL_FIELDS = ("name", "level", "confidence", "market_relevance", "mention_count")


def _cursor_decode(cursor: str) -> int:
    """Decode an opaque base64 offset cursor; invalid cursors restart at 0."""
    if not cursor:
        return 0
    try:
        return int(base64.b64decode(cursor.encode()).decode())
    except Exception:
        return 0


def _cursor_encode(offset: int) -> str:
    return base64.b64encode(str(offset).encode()).decode()


def _skill_matches(row: dict[str, Any], query: str, category: str) -> bool:
    if category:
        if (row.get("category") or "") != category:
            return False
    if query:
        q = query.lower()
        haystacks = [row.get("name"), row.get("roles"), row.get("path")]
        haystacks += row.get("aliases") or []
        if not any(h and q in str(h).lower() for h in haystacks):
            return False
    return True


def _skill_sort_key(row: dict[str, Any], sort: str) -> Any:
    if sort in SORTABLE_SKILL_FIELDS:
        return row.get(sort)
    return row.get("created_at")


@router.get("/list")
def list_skills_v2(
    query: str = Query("", description="Substring search over name, roles, path, aliases"),
    category: str = Query("", description="Exact category filter"),
    sort: str = Query("mention_count", description="Sort field"),
    order: str = Query("desc", description="asc or desc"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=200),
    cursor: str = Query("", description="Opaque pagination cursor"),
    repo: SQLAlchemySkillRepository = Depends(get_skill_repo),
) -> SkillListResponseSchema:
    """List visible skills with server-side search, category filter, sort and cursor pagination."""
    rows = [r for r in repo.list_visible() if _skill_matches(r, query, category)]

    if rows:
        mention_counts = repo.get_mention_counts([r["id"] for r in rows])
        for r in rows:
            r["mention_count"] = mention_counts.get(r["id"], 0)

    key: Callable[[dict[str, Any]], Any] = lambda r: _skill_sort_key(r, sort)
    with_value = [r for r in rows if key(r) is not None]
    without_value = [r for r in rows if key(r) is None]
    with_value.sort(key=key, reverse=(order == "desc"))
    rows = with_value + without_value

    total = len(rows)
    offset = _cursor_decode(cursor)
    page = rows[offset:offset + page_size]
    next_offset = offset + len(page)
    has_more = next_offset < total

    return SkillListResponseSchema(
        items=[
            SkillListItemSchema(
                id=r["id"],
                name=r.get("name") or "",
                level=r.get("level") or 1,
                roles=r.get("roles") or "",
                path=r.get("path") or "",
                category=r.get("category") or "",
                confidence=r.get("confidence"),
                market_relevance=r.get("market_relevance"),
                evidence=r.get("evidence"),
                tags=r.get("tags") or [],
                aliases=r.get("aliases") or [],
                source_type=r.get("source_type") or "user_input",
                mention_count=r.get("mention_count") or 0,
                created_at=r.get("created_at"),
            )
            for r in page
        ],
        next_cursor=_cursor_encode(next_offset) if has_more else None,
        has_more=has_more,
        total_items=total,
    )


@router.get("")
def list_skills(
    category: str = Query(""),
    repo: SQLAlchemySkillRepository = Depends(get_skill_repo),
):
    """Get visible skills with aliases and tags."""
    return repo.list_visible(category)


@router.get("/hidden")
def list_hidden_skills(repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """List all hidden skills."""
    return repo.list_hidden()


@router.get("/categories")
def get_categories(repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Get all skill categories with counts."""
    return repo.get_categories()


@router.get("/stats")
def get_stats(repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Get overall skills statistics."""
    return repo.get_stats()


@router.get("/{id}")
def get_skill(id: int, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Get a single skill with aliases and tags."""
    skill = repo.get_by_id(id)
    if not skill:
        raise NotFoundError(f"Skill {id} not found")
    return skill


@router.post("")
def create_skill(data: SkillCreate, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Create a new skill."""
    existing = repo.get_by_name(data.name)
    if existing:
        return {"id": existing["id"], "name": data.name, "message": "Skill already exists"}
    return repo.create(data.model_dump())


@router.put("/{id}")
def update_skill(id: int, data: SkillUpdate, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Update a skill."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise BadRequestError("No valid fields to update")
    result = repo.update(id, updates)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.patch("/{id}/rename")
def rename_skill(id: int, data: SkillRename, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Rename a skill and update all references."""
    new_name = data.name.strip()
    result = repo.rename(id, new_name)
    if not result:
        existing = repo.get_by_id(id)
        if not existing:
            raise NotFoundError(f"Skill {id} not found")
        raise ConflictError(f'Skill "{new_name}" already exists')
    return result


@router.delete("/{id}")
def delete_skill(id: int, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Delete a skill and all its aliases."""
    skill = repo.get_by_id(id)
    if not skill:
        raise NotFoundError(f"Skill {id} not found")
    repo.delete(id)
    return {"status": "deleted", "name": skill["name"], "aliases_deleted": skill.get("aliases", [])}


@router.patch("/{id}/hide")
def hide_skill(id: int, data: SkillHide, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Toggle hidden flag on a skill."""
    result = repo.set_hidden(id, data.hidden)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.patch("/{id}/restore")
def restore_skill(id: int, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Restore a hidden skill."""
    result = repo.set_hidden(id, 0)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.post("/{id}/aliases")
def add_skill_alias(id: int, data: SkillAliasAdd, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Add an alias to a skill."""
    result = repo.add_alias(id, data.alias_name)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.delete("/{id}/aliases/{alias_name}")
def remove_skill_alias(id: int, alias_name: str, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Remove an alias from a skill."""
    result = repo.remove_alias(id, alias_name)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.post("/merge")
def merge_skills(data: SkillMerge, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Merge source skills into target skill."""
    result = repo.merge(data.target_id, data.source_ids)
    if "error" in result:
        raise NotFoundError(result["error"])
    return result


@router.get("/skill-relationships/{skill_name}")
def get_skill_relationships(skill_name: str, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Get all relationships for a skill."""
    return repo.get_relationships(skill_name)


@router.post("/skill-relationships")
def create_skill_relationship(data: dict, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Create a skill relationship."""
    success = repo.create_relationship(data)
    if not success:
        raise ConflictError("Relationship already exists")
    return {"status": "created"}


@router.delete("/skill-relationships/{id}")
def delete_skill_relationship(id: int, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Delete a skill relationship."""
    repo.delete_relationship(id)
    return {"status": "deleted"}


@router.post("/bulk-hide")
def bulk_hide(data: SkillBulkHide, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Hide multiple skills at once."""
    if not data.ids:
        raise BadRequestError("ids array required")
    count = repo.bulk_hide(data.ids)
    return {"status": "hidden", "count": count}


@router.post("/bulk-categorize")
def bulk_categorize(data: SkillBulkCategorize, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Re-categorize multiple skills at once."""
    valid = {"technical", "engineering", "professional", "domain", "career"}
    if data.category not in valid:
        raise BadRequestError(f"Invalid category. Must be one of: {', '.join(valid)}")
    count = repo.bulk_categorize(data.ids, data.category)
    return {"status": "categorized", "category": data.category, "count": count}


@router.put("/{id}/category")
def update_category(id: int, data: SkillCategoryUpdate, repo: SQLAlchemySkillRepository = Depends(get_skill_repo)):
    """Update a skill's category."""
    valid = {"technical", "engineering", "professional", "domain", "career"}
    if data.category not in valid:
        raise BadRequestError(f"Invalid category. Must be one of: {', '.join(valid)}")
    result = repo.update(id, {"category": data.category})
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result
