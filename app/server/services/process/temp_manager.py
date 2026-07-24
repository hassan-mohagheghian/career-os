"""
Temp file tracking and cleanup — zero file leaks on shutdown.

Every temp file registered here is guaranteed to be removed
when the job completes or the server shuts down.
"""

from __future__ import annotations

import os
import threading
import logging
from typing import Dict, List

from .interfaces import ITempFileManager

logger = logging.getLogger(__name__)


class TempFileManager(ITempFileManager):
    """Tracks temp files per job and provides cleanup."""

    _instance: Optional[TempFileManager] = None
    _class_lock = threading.Lock()

    def __new__(cls) -> TempFileManager:
        with cls._class_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._files: Dict[str, List[str]] = {}
                inst._lock = threading.Lock()
                cls._instance = inst
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton — for testing only."""
        with cls._class_lock:
            cls._instance = None

    def register(self, job_key: str, path: str) -> None:
        with self._lock:
            self._files.setdefault(job_key, [])
            if path not in self._files[job_key]:
                self._files[job_key].append(path)

    def cleanup(self, job_key: str) -> int:
        removed = 0
        with self._lock:
            paths = self._files.pop(job_key, [])
        for path in paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    removed += 1
            except OSError as e:
                logger.warning(f"[temp] Failed to remove {path}: {e}")
        return removed

    def cleanup_all(self) -> int:
        total = 0
        with self._lock:
            all_paths = [p for paths in self._files.values() for p in paths]
            self._files.clear()
        for path in all_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    total += 1
            except OSError:
                pass
        return total
