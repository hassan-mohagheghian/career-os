"""
Process lifecycle management — subprocess creation and cancellation.

Uses os.setsid() for process groups so cancel() can kill the entire tree.
Thread-safe: all state protected by a lock.
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from typing import Optional, Dict

from shared.infrastructure.process.logging_config import get_logger
from .interfaces import IProcessManager
from .models import ProcessHandle

logger = get_logger('process.manager')


class ProcessManager(IProcessManager):
    """Manages subprocess lifecycles with process groups.

    Each subprocess gets its own process group (via os.setsid()),
    so we can kill the entire tree (mimo + children) cleanly.
    """

    _instance: Optional[ProcessManager] = None
    _class_lock = threading.Lock()

    def __new__(cls) -> ProcessManager:
        with cls._class_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._processes: Dict[str, ProcessHandle] = {}
                inst._lock = threading.Lock()
                cls._instance = inst
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton — for testing only."""
        with cls._class_lock:
            cls._instance = None

    def start(self, cmd: list, cwd: str, env: dict, timeout: int,
              description: str = '', key: Optional[str] = None) -> ProcessHandle:
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, env=env, preexec_fn=os.setsid,
        )
        handle = ProcessHandle(proc, proc.pid, description)
        track_key = key or str(proc.pid)
        with self._lock:
            self._processes[track_key] = handle
        logger.info(f"[process] Started {description or track_key} (pid={proc.pid})")
        return handle

    def cancel(self, handle: ProcessHandle, grace_period: float = 5.0) -> bool:
        if not handle or not handle.is_alive:
            return True
        try:
            pgid = os.getpgid(handle.pid)
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        start = time.time()
        while time.time() - start < grace_period:
            if not handle.is_alive:
                return True
            time.sleep(0.2)
        try:
            pgid = os.getpgid(handle.pid)
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            handle.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        return not handle.is_alive

    def is_alive(self, key: str) -> bool:
        with self._lock:
            h = self._processes.get(key)
            return h.is_alive if h else False

    def get(self, key: str) -> Optional[ProcessHandle]:
        with self._lock:
            return self._processes.get(key)

    def remove(self, key: str) -> None:
        with self._lock:
            self._processes.pop(key, None)

    def cleanup_all(self) -> int:
        killed = 0
        with self._lock:
            handles = list(self._processes.values())
        for h in handles:
            if h.is_alive:
                self.cancel(h, grace_period=3.0)
                killed += 1
        with self._lock:
            self._processes.clear()
        if killed:
            logger.info(f"[process] Cleanup: killed {killed} orphaned process(es)")
        return killed
