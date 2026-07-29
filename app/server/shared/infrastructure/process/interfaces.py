"""
Abstract interfaces — contracts for all infrastructure components.

SOLID: Dependency Inversion — workers depend on these abstractions,
not on concrete SQLite/SocketIO implementations.
"""

from __future__ import annotations

import abc
from typing import Optional, List, Dict, Any, Callable

from .models import (
    ItemStatus, PipelineStep, WorkflowLogEntry, ScoreResult,
    ProcessHandle, StatusUpdate, LogEntry, ProcessingComplete, ProcessingError,
)


# ── Repository Interfaces (DDD: Repository Pattern) ────────────────

class IPendingRepository(abc.ABC):
    """Repository for pending job/company items."""

    @abc.abstractmethod
    def get(self, pid: int) -> Optional[dict]:
        """Fetch a pending item by ID."""

    @abc.abstractmethod
    def update_status(self, pid: int, status: ItemStatus, **fields) -> None:
        """Update status and optional extra fields."""

    @abc.abstractmethod
    def update_step(self, pid: int, step: str, val: int, **fields) -> None:
        """Update a pipeline step value."""

    @abc.abstractmethod
    def append_log(self, pid: int, entry: WorkflowLogEntry) -> None:
        """Append a workflow log entry."""

    @abc.abstractmethod
    def get_logs(self, pid: int) -> List[WorkflowLogEntry]:
        """Get all workflow log entries."""

    @abc.abstractmethod
    def claim_next(self) -> Optional[dict]:
        """Atomically claim the next queued item for processing."""

    @abc.abstractmethod
    def count_by_status(self) -> Dict[ItemStatus, int]:
        """Count items in each status."""


class IJobRepository(abc.ABC):
    """Repository for processed job results."""

    @abc.abstractmethod
    def get_next_num(self) -> int:
        """Get the next available job number."""

    @abc.abstractmethod
    def get_by_url(self, url: str) -> Optional[dict]:
        """Find a job by URL."""

    @abc.abstractmethod
    def insert(self, job_data: dict) -> int:
        """Insert or replace a job. Returns the job num."""

    @abc.abstractmethod
    def insert_summary(self, summary_data: dict) -> None:
        """Insert or replace a summary."""

    @abc.abstractmethod
    def insert_resume(self, resume_data: dict) -> None:
        """Insert or replace a resume."""

    @abc.abstractmethod
    def save_workflow_log(self, num: int, log_json: str) -> None:
        """Save workflow log to the jobs table."""


# ── Process Manager Interface (Strategy Pattern) ──────────────────

class IProcessManager(abc.ABC):
    """Manages subprocess lifecycles."""

    @abc.abstractmethod
    def start(self, cmd: list, cwd: str, env: dict, timeout: int,
              description: str = '', key: Optional[str] = None) -> ProcessHandle:
        """Start a subprocess in its own process group."""

    @abc.abstractmethod
    def cancel(self, handle: ProcessHandle, grace_period: float = 5.0) -> bool:
        """Cancel a process and its entire group. Returns True if terminated."""

    @abc.abstractmethod
    def is_alive(self, key: str) -> bool:
        """Check if a tracked process is still running."""

    @abc.abstractmethod
    def get(self, key: str) -> Optional[ProcessHandle]:
        """Get a tracked process handle."""

    @abc.abstractmethod
    def remove(self, key: str) -> None:
        """Remove a process from tracking."""

    @abc.abstractmethod
    def cleanup_all(self) -> int:
        """Kill all tracked processes. Returns count killed."""


# ── Temp File Manager Interface ───────────────────────────────────

class ITempFileManager(abc.ABC):
    """Tracks and cleans temporary files."""

    @abc.abstractmethod
    def register(self, job_key: str, path: str) -> None:
        """Register a temp file for tracking."""

    @abc.abstractmethod
    def cleanup(self, job_key: str) -> int:
        """Remove all temp files for a job. Returns count removed."""

    @abc.abstractmethod
    def cleanup_all(self) -> int:
        """Remove ALL tracked temp files. Returns total removed."""


# ── Mimo Runner Interface (Strategy Pattern) ─────────────────────

class IMimoRunner(abc.ABC):
    """Runs mimo CLI commands."""

    @abc.abstractmethod
    def run(self, prompt: str, timeout: int = 300,
            session_id: Optional[str] = None,
            key: Optional[str] = None,
            on_event: Optional[Callable] = None,
            on_session_id: Optional[Callable] = None,
            cwd: Optional[str] = None) -> tuple:
        """Run mimo. Returns (returncode, output_lines, session_id).
        on_session_id(session_id) is called the instant it's discovered."""


# ── Broadcaster Interface (Observer Pattern) ──────────────────────

class IBroadcaster(abc.ABC):
    """Delivers processing status to clients."""

    @abc.abstractmethod
    def step_update(self, event: StatusUpdate) -> None:
        """Broadcast a step status change."""

    @abc.abstractmethod
    def log(self, event: LogEntry) -> None:
        """Broadcast a log entry."""

    @abc.abstractmethod
    def complete(self, event: ProcessingComplete) -> None:
        """Broadcast processing completion."""

    @abc.abstractmethod
    def error(self, event: ProcessingError) -> None:
        """Broadcast a processing error."""

    @abc.abstractmethod
    def queue_status(self, processing: int, queued: int, pending: int, concurrency: int) -> None:
        """Broadcast global queue status."""

    @abc.abstractmethod
    def progress(self, event) -> None:
        """Broadcast workflow progress update."""
