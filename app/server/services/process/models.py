"""
Domain models — value objects and entities for the processing pipeline.

DDD: These are the core domain types. They carry no infrastructure logic.
All persistence and side effects live in repository/broadcaster layers.
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any


# ── Enums ──────────────────────────────────────────────────────────

class ItemStatus(str, Enum):
    """Status flow for pending items (jobs and companies)."""
    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    PAUSED = 'paused'
    DONE = 'done'
    FAILED = 'failed'

    @classmethod
    def valid_transitions(cls) -> Dict[ItemStatus, set[ItemStatus]]:
        """Valid state transitions — enforced by repository."""
        return {
            cls.PENDING:   {cls.QUEUED, cls.FAILED},
            cls.QUEUED:    {cls.PROCESSING, cls.PENDING, cls.FAILED},
            cls.PROCESSING: {cls.DONE, cls.FAILED, cls.PAUSED, cls.QUEUED},
            cls.PAUSED:    {cls.QUEUED, cls.FAILED, cls.PENDING},
            cls.DONE:      {cls.PENDING},  # only via reprocess
            cls.FAILED:    {cls.PENDING, cls.QUEUED},  # only via retry
        }

    def can_transition_to(self, target: ItemStatus) -> bool:
        return target in self.valid_transitions().get(self, set())


class PipelineStep(str, Enum):
    """Pipeline steps for job processing."""
    FETCH = 'step_fetch'
    VALIDATE = 'step_validate'
    EXTRACT_RAW = 'step_extract_raw'
    EXTRACT_STRUCT = 'step_extract_struct'
    ANALYZE = 'step_analyze'
    SUMMARY = 'step_summary'
    DB = 'step_db'
    DONE = 'step_done'

    @property
    def label(self) -> str:
        return {
            'step_fetch': 'Fetching',
            'step_validate': 'Validating',
            'step_extract_raw': 'Extracting',
            'step_extract_struct': 'Structuring',
            'step_analyze': 'Analyzing',
            'step_summary': 'Summarizing',
            'step_db': 'Saving',
            'step_done': 'Done',
        }.get(self.value, self.value)


class CompanyPipelineStep(str, Enum):
    """Pipeline steps for company processing."""
    FETCH = 'step_fetch'
    EXTRACT = 'step_extract'
    ANALYZE = 'step_analyze'
    SAVE = 'step_save'
    DONE = 'step_done'

    @property
    def label(self) -> str:
        return {
            'step_fetch': 'Fetching',
            'step_extract': 'Extracting',
            'step_analyze': 'Analyzing',
            'step_save': 'Saving',
            'step_done': 'Done',
        }.get(self.value, self.value)


# ── Value Objects ──────────────────────────────────────────────────

@dataclass(frozen=True)
class WorkflowLogEntry:
    """A single log entry in the processing workflow."""
    step: str
    msg: str
    ts: str = field(default_factory=lambda: datetime.now().strftime('%H:%M:%S'))

    def to_dict(self) -> dict:
        return {'step': self.step, 'msg': self.msg, 'ts': self.ts}

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowLogEntry:
        return cls(step=d['step'], msg=d['msg'], ts=d.get('ts', ''))


@dataclass
class ScoreResult:
    """Numeric scoring result from mimo analysis."""
    fit_score: Optional[int] = None
    success_score: Optional[int] = None
    overall_score: Optional[int] = None
    grade: str = 'P'
    match: str = 'Medium'

    def compute_overall(self, fit_weight: float = 0.6, success_weight: float = 0.4):
        """Compute overall score from fit and success."""
        if self.fit_score is not None and self.success_score is not None:
            self.overall_score = int(round(
                self.fit_score * fit_weight + self.success_score * success_weight
            ))
        return self


@dataclass
class ProcessHandle:
    """Tracks a subprocess and its process group."""
    proc: Any  # subprocess.Popen
    pid: int
    description: str = ''
    created_at: float = field(default_factory=lambda: __import__('time').time())

    @property
    def is_alive(self) -> bool:
        return self.proc.poll() is None

    @property
    def returncode(self) -> Optional[int]:
        return self.proc.returncode


# ── Domain Events ──────────────────────────────────────────────────

@dataclass(frozen=True)
class StatusUpdate:
    """Domain event: a pipeline step changed status."""
    table: str
    pid: int
    step: str
    val: int
    status: Optional[str] = None
    error: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class LogEntry:
    """Domain event: a workflow log was appended."""
    table: str
    pid: int
    step: str
    msg: str
    ts: str = field(default_factory=lambda: datetime.now().strftime('%H:%M:%S'))


@dataclass(frozen=True)
class ProcessingComplete:
    """Domain event: processing finished successfully."""
    table: str
    pid: int
    result: Dict[str, Any]
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ProcessingError:
    """Domain event: processing failed."""
    table: str
    pid: int
    msg: str
    step: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now().isoformat())
