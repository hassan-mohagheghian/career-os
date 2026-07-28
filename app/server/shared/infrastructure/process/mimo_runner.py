"""
mimo CLI invocation — runs mimo as a subprocess with streaming output.

Handles session awareness (--session / --continue), JSON event parsing,
and cancellation via ProcessManager.
"""

from __future__ import annotations

import os
import json
import logging
import threading
import uuid
from typing import Optional, Callable

from .interfaces import IMimoRunner, IProcessManager

logger = logging.getLogger(__name__)

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..', '..', '..')
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..', '..', '..', '..'))
MIMO_BIN = os.path.expanduser('~/.mimocode/bin/mimo')

_db_path = os.environ.get('DB_PATH', os.path.join(_server_dir, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.normpath(os.path.join(_server_dir, _db_path))

TMP_DIR = os.path.join(PROJECT_ROOT, 'tmp')
os.makedirs(TMP_DIR, exist_ok=True)


class MimoRunner(IMimoRunner):
    """Runs mimo CLI commands with streaming JSON output."""

    def __init__(self, process_manager: IProcessManager):
        self._proc_mgr = process_manager

    def run(self, prompt: str, timeout: int = 300,
            session_id: Optional[str] = None,
            key: Optional[str] = None,
            on_event: Optional[Callable] = None,
            on_session_id: Optional[Callable] = None,
            cwd: Optional[str] = None) -> tuple:
        cmd = [MIMO_BIN, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions']
        if session_id:
            cmd.extend(['--session', session_id])

        env = {**os.environ, 'NO_COLOR': '1'}
        actual_cwd = cwd or PROJECT_ROOT

        handle = self._proc_mgr.start(
            cmd, cwd=actual_cwd, env=env, timeout=timeout,
            description=f'mimo ({key or "unknown"})', key=key,
        )

        all_lines = []
        discovered_session_id = session_id  # None until discovered from stream or passed in
        timed_out = threading.Event()

        def _watchdog():
            timed_out.wait(timeout)
            if not timed_out.is_set():
                logger.warning(f"[mimo] Timeout after {timeout}s, killing pid={handle.pid}")
                self._proc_mgr.cancel(handle, grace_period=3.0)

        timer = threading.Thread(target=_watchdog, daemon=True)
        timer.start()

        try:
            for raw_line in handle.proc.stdout:
                line = raw_line.rstrip('\n')
                if not line:
                    continue
                all_lines.append(line)
                try:
                    evt = json.loads(line)
                    if on_event:
                        on_event(evt)
                    if not discovered_session_id:
                        sid = (evt.get('sessionID') or evt.get('sessionId')
                               or evt.get('session_id'))
                        if sid:
                            discovered_session_id = sid
                            logger.info(f"[mimo] Discovered session_id={sid}")
                            if on_session_id:
                                try:
                                    on_session_id(sid)
                                except Exception:
                                    pass
                except json.JSONDecodeError:
                    pass

            handle.proc.wait()
            timed_out.set()

            returncode = handle.proc.returncode
            if returncode == -9:
                raise RuntimeError(f"mimo timed out after {timeout}s")
            if returncode == -15:
                # SIGTERM — may have been killed by our watchdog or externally
                logger.warning(f"[mimo] Process killed by SIGTERM (pid={handle.pid})")
                if not discovered_session_id:
                    raise RuntimeError(f"mimo was killed (SIGTERM) after {timeout}s")

            return returncode, all_lines, discovered_session_id

        except Exception:
            # Only cancel if process is still alive
            if handle.is_alive:
                self._proc_mgr.cancel(handle)
            raise
        finally:
            timed_out.set()  # stop watchdog
            if key:
                self._proc_mgr.remove(key)
