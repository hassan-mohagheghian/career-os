"""Backward-compatible re-exports from the new process module.

This file exists so the existing worker.py and company_worker.py continue
to work while we migrate them to use the new services.process package directly.
"""
from services.process.process_manager import ProcessManager
from services.process.temp_manager import TempFileManager
from services.process.mimo_runner import MimoRunner, DB_PATH, PROJECT_ROOT, MIMO_BIN, TMP_DIR
from services.process.broadcaster import Broadcaster as StatusBroadcaster

# Shared broadcaster instance — wired to SocketIO by app.py
broadcaster = StatusBroadcaster()


def _db():
    """Zero-arg DB connection — matches the old worker.py interface."""
    import sqlite3, time as _time
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            return conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 4:
                _time.sleep(0.5 * (attempt + 1))
            else:
                raise
