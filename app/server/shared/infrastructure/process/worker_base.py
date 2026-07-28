"""
Abstract worker base — Template Method pattern.

Defines the processing pipeline skeleton. Subclasses implement
the concrete steps (fetch, extract, analyze, save).
"""

from __future__ import annotations

import abc
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from .interfaces import (
    IProcessManager, ITempFileManager, IMimoRunner, IBroadcaster,
    IPendingRepository,
)
from .models import (
    ItemStatus, WorkflowLogEntry, StatusUpdate, LogEntry,
    ProcessingComplete, ProcessingError,
)
from .logging_config import get_logger

logger = get_logger('worker')


class WorkerBase(abc.ABC):
    """Abstract base worker — Template Method pattern.

    Defines the pipeline skeleton:
        start -> [fetch -> extract -> analyze -> save] -> done

    Subclasses implement the concrete steps. The base class handles:
    - Status transitions (pending -> queued -> processing -> done/failed)
    - Cancellation checks between steps
    - Logging and broadcasting
    - Temp file cleanup
    """

    def __init__(
        self,
        pending_repo: IPendingRepository,
        process_mgr: IProcessManager,
        temp_mgr: ITempFileManager,
        mimo_runner: IMimoRunner,
        broadcaster: IBroadcaster,
    ):
        self._pending_repo = pending_repo
        self._proc_mgr = process_mgr
        self._temp_mgr = temp_mgr
        self._mimo = mimo_runner
        self._broadcaster = broadcaster

    @property
    @abc.abstractmethod
    def table(self) -> str:
        """DB table name: 'pending_jobs' or 'pending_companies'."""

    @property
    @abc.abstractmethod
    def pipeline_steps(self) -> list:
        """Ordered list of pipeline step column names."""

    @abc.abstractmethod
    def _execute_pipeline(self, pid: int, item: dict) -> Dict[str, Any]:
        """Execute the processing pipeline. Returns result dict."""

    def process(self, pid: int) -> None:
        """Run the full pipeline for a pending item.

        This is the Template Method — subclasses should NOT override this.
        """
        item = self._pending_repo.get(pid)
        if not item:
            logger.warning("worker.item_not_found", pid=pid, table=self.table)
            return

        log = logger.bind(pid=pid, table=self.table, url=item.get('url', ''))
        log.info("worker.start")

        try:
            # Reset steps if partially completed (broken previous run)
            self._reset_steps(pid)

            # Execute the pipeline
            result = self._execute_pipeline(pid, item)

            # If pipeline returned None, it was cancelled between steps
            if result is None:
                current = self._pending_repo.get(pid)
                status = ItemStatus(current['status']) if current else ItemStatus.PAUSED
                log.info("worker.cancelled", status=status.value)
                return

            # Mark complete
            self._mark_step(pid, 'step_done', 1)
            self._pending_repo.update_status(pid, ItemStatus.DONE)

            self._broadcaster.complete(ProcessingComplete(
                table=self.table, pid=pid, result=result,
            ))
            log.info("worker.complete", result=result)

        except Exception as e:
            log.error("worker.failed", error=str(e))
            self._broadcaster.error(ProcessingError(
                table=self.table, pid=pid, msg=str(e),
            ))
            self._pending_repo.update_status(
                pid, ItemStatus.FAILED, error=str(e),
            )
        finally:
            self._temp_mgr.cleanup(str(pid))
            self._proc_mgr.remove(str(pid))

    def _reset_steps(self, pid: int) -> None:
        """Reset all pipeline steps to 0."""
        updates = {step: 0 for step in self.pipeline_steps}
        updates['workflow_log'] = '[]'
        current = self._pending_repo.get(pid)
        status = ItemStatus(current['status']) if current else ItemStatus.PENDING
        self._pending_repo.update_status(pid, status, **updates)

    def _is_cancelled(self, pid: int) -> bool:
        """Check if processing should stop (pause/stop/restart)."""
        item = self._pending_repo.get(pid)
        if not item:
            return True
        return item['status'] not in (ItemStatus.PROCESSING.value,)

    def _mark_step(self, pid: int, step: str, val: int = 1, **extra) -> None:
        """Mark a pipeline step as done and broadcast."""
        self._pending_repo.update_step(pid, step, val, **extra)
        self._broadcaster.step_update(StatusUpdate(
            table=self.table, pid=pid, step=step, val=val, extra=extra or None,
        ))

    def _log(self, pid: int, step: str, msg: str) -> None:
        """Append a workflow log entry and broadcast."""
        entry = WorkflowLogEntry(step=step, msg=msg)
        self._pending_repo.append_log(pid, entry)
        self._broadcaster.log(LogEntry(
            table=self.table, pid=pid, step=step, msg=msg,
        ))

    def _start_step(self, pid: int, step: str) -> None:
        """Mark a step as in-progress (val=0, status=processing)."""
        self._pending_repo.update_step(pid, step, 0)
        self._broadcaster.step_update(StatusUpdate(
            table=self.table, pid=pid, step=step, val=0,
        ))

    def _mimo_event_handler(self, pid: int, evt: dict) -> None:
        """Handle a single mimo JSON event — log it for audit trail."""
        event_type = evt.get('type', '')
        if event_type == 'text':
            text = evt.get('part', {}).get('text', '')
            if text:
                self._log(pid, 'mimo', f'text: {text[:200]}')
        elif event_type == 'tool_use':
            tool = evt.get('part', {}).get('tool', 'unknown')
            self._log(pid, 'mimo', f'tool: {tool}')
        elif event_type == 'step_finish':
            reason = evt.get('part', {}).get('reason', '')
            tokens = evt.get('part', {}).get('tokens', {})
            self._log(pid, 'mimo', f'step: {reason} ({tokens.get("total", 0)} tokens)')
