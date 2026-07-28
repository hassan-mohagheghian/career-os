"""
Insights service — OOP wrapper for career intelligence generation.

SOLID:
- SRP: Only manages insight generation lifecycle
- OCP: New insight types added via SECTION_PROMPTS mapping
- DIP: Depends on abstractions (LLM service, broadcaster)

This module wraps the existing insights.py functionality in a proper class,
while maintaining full backward compatibility with the existing API.
"""

from __future__ import annotations

import json
import os
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List

from shared.domain.models.generation_models import GenerationSource


class InsightsService:
    """OOP service for career intelligence generation.

    Manages the lifecycle of insight generation:
    - Concurrency control (only one analysis at a time)
    - Progress tracking via broadcaster
    - Session management for LLM retry
    - Cancellation support
    """

    # Insight type -> source mapping
    INSIGHT_SOURCE_MAP = {
        'overview': GenerationSource.INSIGHT_OVERVIEW,
        'opportunities': GenerationSource.INSIGHT_OPPORTUNITIES,
        'companies': GenerationSource.INSIGHT_COMPANIES,
        'skills': GenerationSource.INSIGHT_SKILLS_INTEL,
        'skills_intel': GenerationSource.INSIGHT_SKILLS_INTEL,
        'market': GenerationSource.INSIGHT_MARKET,
        'networking': GenerationSource.INSIGHT_NETWORKING,
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._cancel_requested = False
        self._current_run: Dict[str, Any] = {
            'active': False, 'type': None, 'started_at': None,
            'run_id': None, 'process': None, 'session_id': None,
        }

    @property
    def is_running(self) -> bool:
        return self._current_run['active']

    @property
    def current_type(self) -> Optional[str]:
        return self._current_run['type']

    def get_source_for_type(self, insight_type: str) -> GenerationSource:
        """Map insight type to GenerationSource."""
        return self.INSIGHT_SOURCE_MAP.get(insight_type, GenerationSource.INSIGHT_OVERVIEW)

    def generate_all(self, pid: int = 0) -> Optional[dict]:
        """Generate all insight sections."""
        from career.application.services.insights import generate_all
        return generate_all(pid)

    def generate_section(self, section: str, pid: int = 0) -> Optional[dict]:
        """Generate a single insight section."""
        from career.application.services.insights import generate_section
        return generate_section(section, pid)

    def generate_skills_intel(self, pid: int = 0) -> Optional[dict]:
        """Generate the Skills Intelligence Report."""
        from career.application.services.insights import generate_skills_intel
        return generate_skills_intel(pid)

    def cancel(self) -> bool:
        """Cancel the current running analysis."""
        from career.application.services.insights import cancel_run
        return cancel_run()

    def get_progress(self) -> dict:
        """Get current analysis progress."""
        from career.application.services.insights import get_progress as _get_progress
        return _get_progress()

    def get_latest(self, insight_type: Optional[str] = None):
        """Get the latest career insight(s)."""
        from career.application.services.insights import get_latest
        return get_latest(insight_type)

    def get_runs(self, insight_type: Optional[str] = None, limit: int = 10, offset: int = 0):
        """Get recent generation runs."""
        from career.application.services.insights import get_runs
        return get_runs(insight_type, limit, offset)


# Module-level singleton for backward compatibility
_insights_service: Optional[InsightsService] = None


def get_insights_service() -> InsightsService:
    """Get or create the singleton InsightsService."""
    global _insights_service
    if _insights_service is None:
        _insights_service = InsightsService()
    return _insights_service
