"""
Generation domain models — unified representation for ALL generation types.

DDD: Pure domain objects with no infrastructure logic.
Carries data and behavior (state transitions, progress calculation).

SOLID:
- SRP: Each enum/dataclass has one reason to change
- OCP: New generation types added via new enum values + step configs
- LSP: All GenerationRun instances interchangeable
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


# ── Enums ──────────────────────────────────────────────────────────

class GenerationSource(str, Enum):
    """All generation source types across the system."""

    # Processing pipeline sources
    JOB_PROCESS = 'job_process'
    COMPANY_PROCESS = 'company_process'

    # Skill roadmap sources
    SKILL_ROADMAP_GENERATE = 'skill_roadmap_generate'
    SKILL_ROADMAP_EXTEND = 'skill_roadmap_extend'
    SKILL_ROADMAP_FINEGRAIN = 'skill_roadmap_finegrain'

    @property
    def group(self) -> str:
        """Logical group for filtering/display."""
        if self.value.startswith('job_'):
            return 'processing'
        if self.value.startswith('company_'):
            return 'processing'
        if self.value.startswith('skill_roadmap_'):
            return 'roadmap'
        return 'other'

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        _DISPLAY = {
            'job_process': 'Job Processing',
            'company_process': 'Company Processing',

            'skill_roadmap_generate': 'Skill Roadmap: Generate',
            'skill_roadmap_extend': 'Skill Roadmap: Extend',
            'skill_roadmap_finegrain': 'Skill Roadmap: Fine-grain',
        }
        return _DISPLAY.get(self.value, self.value.replace('_', ' ').title())


class GenerationStatus(str, Enum):
    """Status flow for generation runs."""

    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

    @classmethod
    def valid_transitions(cls) -> Dict[GenerationStatus, set[GenerationStatus]]:
        return {
            cls.PENDING: {cls.QUEUED, cls.FAILED},
            cls.QUEUED: {cls.PROCESSING, cls.PENDING, cls.FAILED},
            cls.PROCESSING: {cls.COMPLETED, cls.FAILED, cls.CANCELLED, cls.QUEUED},
            cls.COMPLETED: set(),
            cls.FAILED: {cls.PENDING, cls.QUEUED},
            cls.CANCELLED: {cls.PENDING, cls.QUEUED},
        }

    def can_transition_to(self, target: GenerationStatus) -> bool:
        return target in self.valid_transitions().get(self, set())

    @property
    def is_terminal(self) -> bool:
        return self in (GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED)


# ── Step Configuration ─────────────────────────────────────────────

SOURCE_STEP_CONFIG: Dict[GenerationSource, Dict[str, Any]] = {
    # Job Processing: 8 steps
    GenerationSource.JOB_PROCESS: {
        'label': 'Job Processing',
        'total_steps': 8,
        'steps': [
            {'key': 'step_fetch', 'label': 'Fetching'},
            {'key': 'step_validate', 'label': 'Validating'},
            {'key': 'step_extract_raw', 'label': 'Extracting'},
            {'key': 'step_extract_struct', 'label': 'Structuring'},
            {'key': 'step_summary', 'label': 'Summarizing'},
            {'key': 'step_analyze', 'label': 'Analyzing'},
            {'key': 'step_db', 'label': 'Saving'},
            {'key': 'step_done', 'label': 'Done'},
        ],
    },
    # Company Processing: 5 steps
    GenerationSource.COMPANY_PROCESS: {
        'label': 'Company Processing',
        'total_steps': 5,
        'steps': [
            {'key': 'step_fetch', 'label': 'Fetching'},
            {'key': 'step_extract', 'label': 'Extracting'},
            {'key': 'step_analyze', 'label': 'Analyzing'},
            {'key': 'step_save', 'label': 'Saving'},
            {'key': 'step_done', 'label': 'Done'},
        ],
    },
    # Skill Roadmap: 4 steps each
    GenerationSource.SKILL_ROADMAP_GENERATE: {
        'label': 'Skill Roadmap: Generate',
        'total_steps': 4,
        'steps': [
            {'key': 'step_prepare', 'label': 'Preparing'},
            {'key': 'step_generate', 'label': 'Generating'},
            {'key': 'step_save', 'label': 'Saving'},
            {'key': 'step_done', 'label': 'Done'},
        ],
    },
    GenerationSource.SKILL_ROADMAP_EXTEND: {
        'label': 'Skill Roadmap: Extend',
        'total_steps': 4,
        'steps': [
            {'key': 'step_prepare', 'label': 'Preparing'},
            {'key': 'step_generate', 'label': 'Generating'},
            {'key': 'step_save', 'label': 'Saving'},
            {'key': 'step_done', 'label': 'Done'},
        ],
    },
    GenerationSource.SKILL_ROADMAP_FINEGRAIN: {
        'label': 'Skill Roadmap: Fine-grain',
        'total_steps': 4,
        'steps': [
            {'key': 'step_prepare', 'label': 'Preparing'},
            {'key': 'step_generate', 'label': 'Generating'},
            {'key': 'step_save', 'label': 'Saving'},
            {'key': 'step_done', 'label': 'Done'},
        ],
    },
}


# ── Value Objects ──────────────────────────────────────────────────

@dataclass
class GenerationRun:
    """Unified representation of a generation run across all systems.

    DDD: Aggregate root for generation tracking.
    """

    id: int
    source: GenerationSource
    status: GenerationStatus = GenerationStatus.PENDING
    step: int = 0
    total_steps: int = 0
    title: str = ''
    error: Optional[str] = None
    session_id: Optional[str] = None
    provider: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.total_steps == 0:
            config = SOURCE_STEP_CONFIG.get(self.source)
            if config:
                self.total_steps = config['total_steps']

    @property
    def progress_pct(self) -> float:
        """Calculate progress percentage."""
        if self.total_steps <= 0:
            return 0.0
        return round((self.step / self.total_steps) * 100, 1)

    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Calculate elapsed time in seconds from started_at."""
        if not self.started_at:
            return None
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at) if self.completed_at else datetime.now()
            return (end - start).total_seconds()
        except (ValueError, TypeError):
            return None

    def to_history_item(self) -> 'GenerationHistoryItem':
        """Convert to a normalized history item for the API/frontend."""
        source_group = self.source.group
        source_label_map = {
            'processing': 'job-processing' if 'job' in self.source.value else 'company-processing',
            'roadmap': 'roadmap',
        }
        normalized_source = source_label_map.get(source_group, source_group)

        return GenerationHistoryItem(
            id=self.id,
            source=normalized_source,
            title=self.title or self.source.display_name,
            status=self.status.value,
            started_at=self.started_at,
            completed_at=self.completed_at,
            error=self.error,
            session_id=self.session_id,
            provider=self.provider,
        )


@dataclass
class GenerationHistoryItem:
    """Normalized history item for the unified generation history API.

    DDD: Read model for the generation history projection.
    """

    id: int
    source: str  # 'job-processing', 'company-processing', 'generation', 'roadmap'
    title: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    provider: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate duration in seconds."""
        if not self.started_at or not self.completed_at:
            return None
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return int((end - start).total_seconds())
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            'id': self.id,
            'source': self.source,
            'title': self.title,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'session_id': self.session_id,
            'provider': self.provider,
            'duration_seconds': self.duration_seconds,
        }
