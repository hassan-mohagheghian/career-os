"""
Skill Roadmap service — OOP wrapper for learning roadmap generation.

SOLID:
- SRP: Only manages skill roadmap generation lifecycle
- OCP: New operations (generate, extend, finegrain) added via method delegation
- DIP: Depends on abstractions (LLM service, broadcaster)

This module wraps the existing skill_roadmap_service.py functionality in a proper class,
while maintaining full backward compatibility with the existing API.
"""

from __future__ import annotations

import json
import os
from typing import Optional, Dict, Any, List

from shared.domain.models.generation_models import GenerationSource


class SkillRoadmapService:
    """OOP service for skill roadmap generation.

    Operations: generate, extend, finegrain.
    Each creates a job, runs LLM, and saves results.
    """

    # Operation -> source mapping
    OPERATION_SOURCE_MAP = {
        'generate': GenerationSource.SKILL_ROADMAP_GENERATE,
        'extend': GenerationSource.SKILL_ROADMAP_EXTEND,
        'finegrain': GenerationSource.SKILL_ROADMAP_FINEGRAIN,
    }

    def get_source_for_operation(self, operation: str) -> GenerationSource:
        """Map operation to GenerationSource."""
        return self.OPERATION_SOURCE_MAP.get(operation, GenerationSource.SKILL_ROADMAP_GENERATE)

    def generate(self, skill_name: str):
        """Generate a new skill roadmap from scratch."""
        from skills.application.services.skill_roadmap_service import generate_roadmap
        return generate_roadmap(skill_name)

    def extend(self, skill_name: str):
        """Extend an existing roadmap with more advanced items."""
        from skills.application.services.skill_roadmap_service import extend_roadmap
        return extend_roadmap(skill_name)

    def finegrain(self, skill_name: str):
        """Fine-grain existing roadmap by splitting broad items."""
        from skills.application.services.skill_roadmap_service import finegrain_roadmap
        return finegrain_roadmap(skill_name)

    def get_roadmap(self, skill_name: str) -> list:
        """Get existing roadmap items."""
        from skills.application.services.skill_roadmap_service import _get_existing_roadmap, _build_tree, _flatten_tree
        items = _get_existing_roadmap(skill_name)
        tree = _build_tree(items)
        return _flatten_tree(tree)

    def get_jobs(self, limit: int = 50) -> list:
        """Get recent roadmap jobs."""
        from dependencies import get_session_sync
        from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
        session = get_session_sync()
        try:
            repo = SQLAlchemySkillRoadmapJobRepository(session)
            return repo.get_all(limit=limit)
        finally:
            session.close()


# Module-level singleton for backward compatibility
_skill_roadmap_service: Optional[SkillRoadmapService] = None


def get_skill_roadmap_service() -> SkillRoadmapService:
    """Get or create the singleton SkillRoadmapService."""
    global _skill_roadmap_service
    if _skill_roadmap_service is None:
        _skill_roadmap_service = SkillRoadmapService()
    return _skill_roadmap_service
