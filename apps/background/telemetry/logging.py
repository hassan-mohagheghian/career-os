"""Structured logging for the background worker application.

Reuses the structlog configuration from the server.
"""

import os
import sys

_server_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "server")
)
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)

from shared.infrastructure.process.logging_config import setup_logging, get_logger

_initialized = False


def init_logging(log_dir: str | None = None, level: str = "INFO"):
    global _initialized
    if _initialized:
        return
    _initialized = True

    log_dir = log_dir or os.environ.get("BACKGROUND_LOG_DIR")
    setup_logging(log_dir=log_dir, level=level)


__all__ = ["init_logging", "get_logger"]
