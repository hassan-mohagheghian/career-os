"""Shared process utilities — re-exports from the process module.

Provides backward-compatible access to process infrastructure
for workers and other components.
"""
from shared.infrastructure.process.process_manager import ProcessManager
from shared.infrastructure.process.temp_manager import TempFileManager
from shared.infrastructure.process.mimo_runner import MimoRunner, DB_PATH, PROJECT_ROOT, MIMO_BIN, TMP_DIR
from shared.infrastructure.process.broadcaster import Broadcaster as StatusBroadcaster

# Shared broadcaster instance — wired to SocketIO by app.py
broadcaster = StatusBroadcaster()
