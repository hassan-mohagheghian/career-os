"""Scoring rules endpoints."""

from fastapi import APIRouter, Depends

from dependencies import get_rule_repo
from rules.infrastructure import SQLAlchemyRuleRepository

router = APIRouter()


@router.get("")
def get_rules(repo: SQLAlchemyRuleRepository = Depends(get_rule_repo)):
    """Get all scoring rules grouped by scope."""
    rows = repo.get_all()
    grouped = {}
    for r in rows:
        scope = r.get("scope", "SHARED")
        grouped.setdefault(scope, []).append(r)
    return grouped


@router.put("/{id}")
def update_rule(id: int, data: dict, repo: SQLAlchemyRuleRepository = Depends(get_rule_repo)):
    """Update a single rule."""
    repo.update(id, data)
    return {"status": "updated"}


@router.post("")
def create_rule(data: dict, repo: SQLAlchemyRuleRepository = Depends(get_rule_repo)):
    """Create a new rule."""
    rules = data.get("rules", [data])
    for rule in rules:
        repo.create(rule)
    return {"status": "created"}


@router.delete("/{id}")
def delete_rule(id: int, repo: SQLAlchemyRuleRepository = Depends(get_rule_repo)):
    """Delete a rule."""
    repo.delete(id)
    return {"status": "deleted"}


@router.put("")
def bulk_update_rules(data: dict, repo: SQLAlchemyRuleRepository = Depends(get_rule_repo)):
    """Bulk update rules (e.g. reordering priorities)."""
    rules = data.get("rules", [])
    repo.bulk_update(rules)
    return {"status": "updated"}
