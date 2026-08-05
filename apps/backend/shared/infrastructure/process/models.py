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

class JobStatus(str, Enum):
    """Explicit deterministic job statuses — single source of truth.

    Flow:
        CREATED → PENDING → QUEUED → PROCESSING → PROCESSED
                                 └→ FAILED ←┘         │
          CANCELLED ←──────────────────────────────────┘
    """
    CREATED = 'created'
    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    FAILED = 'failed'
    PROCESSED = 'processed'
    CANCELLED = 'cancelled'

    @classmethod
    def valid_transitions(cls) -> Dict[JobStatus, set[JobStatus]]:
        return {
            cls.CREATED:    {cls.PENDING, cls.FAILED, cls.CANCELLED},
            cls.PENDING:    {cls.QUEUED, cls.FAILED, cls.CANCELLED},
            cls.QUEUED:     {cls.PROCESSING, cls.PENDING, cls.FAILED, cls.CANCELLED},
            cls.PROCESSING: {cls.PROCESSED, cls.FAILED, cls.CANCELLED},
            cls.PROCESSED:  {cls.PENDING, cls.QUEUED, cls.CANCELLED},  # reprocess
            cls.FAILED:     {cls.PENDING, cls.QUEUED, cls.CANCELLED},  # retry
            cls.CANCELLED:  {cls.PENDING},                              # un-cancel
        }

    def can_transition_to(self, target: JobStatus) -> bool:
        return target in self.valid_transitions().get(self, set())

    @property
    def is_terminal(self) -> bool:
        return self in (JobStatus.PROCESSED, JobStatus.FAILED, JobStatus.CANCELLED)

    @property
    def is_active(self) -> bool:
        return self is JobStatus.PROCESSING

    @property
    def label(self) -> str:
        return {
            'created': 'Created',
            'pending': 'Pending',
            'queued': 'Queued',
            'processing': 'Processing',
            'processed': 'Processed',
            'failed': 'Failed',
            'cancelled': 'Cancelled',
        }.get(self.value, self.value)


class ItemStatus(str, Enum):
    """Legacy status enum — kept for backward compatibility during migration.
    
    Maps to JobStatus where possible. Marked for removal after migration.
    """
    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    PAUSED = 'paused'
    DONE = 'done'
    FAILED = 'failed'

    def to_job_status(self) -> JobStatus:
        mapping = {
            'pending': JobStatus.CREATED,
            'queued': JobStatus.QUEUED,
            'processing': JobStatus.PROCESSING,
            'paused': JobStatus.PENDING,
            'done': JobStatus.PROCESSED,
            'failed': JobStatus.FAILED,
        }
        return mapping.get(self.value, JobStatus.CREATED)

    @classmethod
    def from_job_status(cls, status: JobStatus) -> ItemStatus:
        mapping = {
            JobStatus.CREATED: 'pending',
            JobStatus.PENDING: 'pending',
            JobStatus.QUEUED: 'queued',
            JobStatus.PROCESSING: 'processing',
            JobStatus.PROCESSED: 'done',
            JobStatus.FAILED: 'failed',
            JobStatus.CANCELLED: 'paused',
        }
        return mapping.get(status, 'pending')

    @classmethod
    def valid_transitions(cls) -> Dict[ItemStatus, set[ItemStatus]]:
        return {
            cls.PENDING:   {cls.QUEUED, cls.FAILED},
            cls.QUEUED:    {cls.PROCESSING, cls.PENDING, cls.FAILED},
            cls.PROCESSING: {cls.DONE, cls.FAILED, cls.PAUSED, cls.QUEUED},
            cls.PAUSED:    {cls.QUEUED, cls.FAILED, cls.PENDING},
            cls.DONE:      {cls.PENDING},
            cls.FAILED:    {cls.PENDING, cls.QUEUED},
        }

    def can_transition_to(self, target: ItemStatus) -> bool:
        return target in self.valid_transitions().get(self, set())


class WorkflowStep(str, Enum):
    """Workflow execution stages — each maps to a LangGraph node.
    
    These represent the meaningful execution stages that are
    communicated to the frontend via WebSocket events.
    """
    VALIDATE = 'validate'
    FETCH = 'fetch'
    EXTRACT = 'extract'
    ANALYZE = 'analyze'
    SCORE = 'score'
    SUMMARIZE = 'summarize'
    PERSIST = 'persist'
    COMPLETE = 'complete'

    @property
    def label(self) -> str:
        return {
            'validate': 'Validating input',
            'fetch': 'Fetching content',
            'extract': 'Extracting data',
            'analyze': 'Analyzing job',
            'score': 'Scoring',
            'summarize': 'Generating summary',
            'persist': 'Saving results',
            'complete': 'Done',
        }.get(self.value, self.value)


class PipelineStep(str, Enum):
    """Legacy pipeline steps — kept for backward compatibility."""
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
    pid: str
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
    pid: str
    step: str
    msg: str
    ts: str = field(default_factory=lambda: datetime.now().strftime('%H:%M:%S'))


@dataclass(frozen=True)
class ProcessingComplete:
    """Domain event: processing finished successfully."""
    table: str
    pid: str
    result: Dict[str, Any]
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ProcessingError:
    """Domain event: processing failed."""
    table: str
    pid: str
    msg: str
    step: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


# ── Enhanced Domain Events for New State Machine ──────────────────

@dataclass(frozen=True)
class JobCreated:
    """Emitted when a new job record is created."""
    job_id: int
    url: str
    source: str
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class JobQueued:
    """Emitted when a job is enqueued for processing."""
    job_id: int
    queue_position: int
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class JobStatusChanged:
    """Emitted when a job transitions between states."""
    job_id: int
    from_status: str
    to_status: str
    reason: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class WorkflowNodeStarted:
    """Emitted when a LangGraph node begins execution."""
    job_id: int
    node: str
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class WorkflowNodeCompleted:
    """Emitted when a LangGraph node finishes execution."""
    job_id: int
    node: str
    duration_ms: float
    success: bool
    error: Optional[str] = None
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class WorkflowProgress:
    """Emitted periodically to report workflow progress."""
    table: str
    pid: str
    current_node: str
    progress_pct: float
    message: str
    status: str = 'processing'
    completed_nodes: list = field(default_factory=list)
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class FailureDetails:
    """Detailed failure information for error tracking."""
    workflow_step: str
    provider: Optional[str] = None
    exception: str = ''
    retry_count: int = 0
    recoverable: bool = False
    ts: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class ObservabilityEvent:
    """Observability tracking data for a workflow execution."""
    execution_id: str
    workflow_id: str
    correlation_id: Optional[str] = None
    current_node: str = ''
    current_state: str = ''
    worker: str = ''
    duration_ms: Optional[float] = None
    provider: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
