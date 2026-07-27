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
