"""Skill tools — wrap existing skill management services.

SRP: Each tool handles one skill-related operation.
"""

from __future__ import annotations

import sqlite3
from .base import BaseTool, ToolResult


class FindSkillTool(BaseTool):
    """Finds a skill in the database by name."""

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
            from core.db import get_db
            conn = get_db()
            row = conn.execute(
                "SELECT * FROM tech_stack WHERE LOWER(name)=LOWER(?)",
                (name,),
            ).fetchone()
            conn.close()

            if row:
                return ToolResult(success=True, data=dict(row))
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

        # Normalize for comparison
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
