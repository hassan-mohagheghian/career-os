"""Skill tools — wrap existing skill management services.

SRP: Each tool handles one skill-related operation.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from skills.infrastructure.models.skill_model import SkillModel
from skills.infrastructure.mappers import skill_model_to_dict
from .base import BaseTool, ToolResult


class FindSkillTool(BaseTool):
    """Finds a skill in the database by name."""

    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def name(self) -> str:
        return "find_skill"

    @property
    def description(self) -> str:
        return "Find a skill by name in the skills database"

    def run(self, **kwargs) -> ToolResult:
        name = kwargs.get("name")
        if not name:
            return ToolResult(success=False, error="name parameter is required")

        try:
            if self._session is None:
                from shared.infrastructure.database.session import get_session_sync
                self._session = get_session_sync()

            model = self._session.query(SkillModel).filter(
                func.lower(SkillModel.name) == func.lower(name)
            ).first()

            if model:
                return ToolResult(success=True, data=skill_model_to_dict(model))
            return ToolResult(success=False, error=f"Skill not found: {name}")
        except Exception as e:
            return ToolResult(success=False, error=f"Search failed: {e}")


class CalculateSkillGapTool(BaseTool):
    """Calculates skill gap between job requirements and user skills."""

    @property
    def name(self) -> str:
        return "calculate_skill_gap"

    @property
    def description(self) -> str:
        return "Compare required skills against user's current skills"

    def run(self, **kwargs) -> ToolResult:
        required = kwargs.get("required_skills", [])
        user_skills = kwargs.get("user_skills", [])

        if not required:
            return ToolResult(success=False, error="required_skills parameter is required")

        required_lower = {s.lower().strip() for s in required}
        user_lower = {s.lower().strip() for s in user_skills}

        matched = required_lower & user_lower
        missing = required_lower - user_lower

        return ToolResult(
            success=True,
            data={
                "matched": list(matched),
                "missing": list(missing),
                "coverage": len(matched) / len(required_lower) if required_lower else 0,
            },
        )
