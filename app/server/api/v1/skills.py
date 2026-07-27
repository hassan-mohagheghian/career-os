"""Tech stack CRUD, skill relationships, merge, hide/restore."""

import sqlite3

from fastapi import APIRouter, Depends, Query

from dependencies import get_db
from infrastructure.database.skill_repository import SkillRepository
from schemas.skills import (
    SkillCreate,
    SkillUpdate,
    SkillRename,
    SkillHide,
    SkillMerge,
    SkillBulkHide,
    SkillBulkCategorize,
    SkillCategoryUpdate,
)
from exceptions import NotFoundError, BadRequestError, ConflictError

router = APIRouter()


def _get_repo(db: sqlite3.Connection = Depends(get_db)) -> SkillRepository:
    return SkillRepository(db)


@router.get("")
def list_skills(
    category: str = Query(""),
    repo: SkillRepository = Depends(_get_repo),
):
    """Get visible skills with aliases and tags."""
    return repo.list_visible(category)


@router.get("/hidden")
def list_hidden_skills(repo: SkillRepository = Depends(_get_repo)):
    """List all hidden skills."""
    return repo.list_hidden()


@router.get("/categories")
def get_categories(repo: SkillRepository = Depends(_get_repo)):
    """Get all skill categories with counts."""
    return repo.get_categories()


@router.get("/stats")
def get_stats(repo: SkillRepository = Depends(_get_repo)):
    """Get overall skills statistics."""
    return repo.get_stats()


@router.post("")
def create_skill(data: SkillCreate, repo: SkillRepository = Depends(_get_repo)):
    """Create a new skill."""
    existing = repo.get_by_name(data.name)
    if existing:
        return {"id": existing["id"], "name": data.name, "message": "Skill already exists"}
    return repo.create(data.model_dump())


@router.put("/{id}")
def update_skill(id: int, data: SkillUpdate, repo: SkillRepository = Depends(_get_repo)):
    """Update a skill."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise BadRequestError("No valid fields to update")
    result = repo.update(id, updates)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.patch("/{id}/rename")
def rename_skill(id: int, data: SkillRename, repo: SkillRepository = Depends(_get_repo)):
    """Rename a skill and update all references."""
    new_name = data.name.strip()
    result = repo.rename(id, new_name)
    if not result:
        # Check if skill exists
        existing = repo.get_by_id(id)
        if not existing:
            raise NotFoundError(f"Skill {id} not found")
        raise ConflictError(f'Skill "{new_name}" already exists')
    return result


@router.delete("/{id}")
def delete_skill(id: int, repo: SkillRepository = Depends(_get_repo)):
    """Delete a skill and all its aliases."""
    skill = repo.get_by_id(id)
    if not skill:
        raise NotFoundError(f"Skill {id} not found")
    repo.delete(id)
    return {"status": "deleted", "name": skill["name"], "aliases_deleted": skill.get("aliases", [])}


@router.patch("/{id}/hide")
def hide_skill(id: int, data: SkillHide, repo: SkillRepository = Depends(_get_repo)):
    """Toggle hidden flag on a skill."""
    result = repo.set_hidden(id, data.hidden)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.patch("/{id}/restore")
def restore_skill(id: int, repo: SkillRepository = Depends(_get_repo)):
    """Restore a hidden skill."""
    result = repo.set_hidden(id, 0)
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result


@router.post("/merge")
def merge_skills(data: SkillMerge, repo: SkillRepository = Depends(_get_repo)):
    """Merge source skills into target skill."""
    result = repo.merge(data.target_id, data.source_ids)
    if "error" in result:
        raise NotFoundError(result["error"])
    return result


@router.get("/skill-relationships/{skill_name}")
def get_skill_relationships(skill_name: str, repo: SkillRepository = Depends(_get_repo)):
    """Get all relationships for a skill."""
    return repo.get_relationships(skill_name)


@router.post("/skill-relationships")
def create_skill_relationship(data: dict, repo: SkillRepository = Depends(_get_repo)):
    """Create a skill relationship."""
    success = repo.create_relationship(data)
    if not success:
        raise ConflictError("Relationship already exists")
    return {"status": "created"}


@router.delete("/skill-relationships/{id}")
def delete_skill_relationship(id: int, repo: SkillRepository = Depends(_get_repo)):
    """Delete a skill relationship."""
    repo.delete_relationship(id)
    return {"status": "deleted"}


@router.post("/bulk-hide")
def bulk_hide(data: SkillBulkHide, repo: SkillRepository = Depends(_get_repo)):
    """Hide multiple skills at once."""
    if not data.ids:
        raise BadRequestError("ids array required")
    count = repo.bulk_hide(data.ids)
    return {"status": "hidden", "count": count}


@router.post("/bulk-categorize")
def bulk_categorize(data: SkillBulkCategorize, repo: SkillRepository = Depends(_get_repo)):
    """Re-categorize multiple skills at once."""
    valid = {"technical", "engineering", "professional", "domain", "career"}
    if data.category not in valid:
        raise BadRequestError(f"Invalid category. Must be one of: {', '.join(valid)}")
    count = repo.bulk_categorize(data.ids, data.category)
    return {"status": "categorized", "category": data.category, "count": count}


@router.put("/{id}/category")
def update_category(id: int, data: SkillCategoryUpdate, repo: SkillRepository = Depends(_get_repo)):
    """Update a skill's category."""
    valid = {"technical", "engineering", "professional", "domain", "career"}
    if data.category not in valid:
        raise BadRequestError(f"Invalid category. Must be one of: {', '.join(valid)}")
    result = repo.update(id, {"category": data.category})
    if not result:
        raise NotFoundError(f"Skill {id} not found")
    return result
