"""
Logging configuration — structlog setup for the processing pipeline.

Single source of truth: every pipeline event (step updates, mimo output,
errors, completions) flows through this logger. Output goes to:
1. Console (human-readable in dev)
2. JSON file (machine-readable for debugging/audit)
3. DB workflow_log (per-job audit trail via Broadcaster)

Usage:
    from .logging_config import get_logger
    log = get_logger()
    log.info("pipeline.start", pid=42, url="https://...")
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

import structlog

_initialized = False


def setup_logging(log_dir: str = None, level: str = 'INFO') -> None:
    """Configure structlog + stdlib logging. Call once at app startup.

    Args:
        log_dir: Directory for JSON log files. None = no file output.
        level: Minimum log level.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    # Ensure log directory exists
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Shared processors — run on every log entry
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # File handler for JSON logs (audit trail)
    if log_dir:
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'pipeline_{today}.jsonl')
        file_formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=shared_processors,
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

    # Quiet noisy libraries
    for name in ('werkzeug', 'engineio', 'socketio'):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str = 'process') -> structlog.stdlib.BoundLogger:
    """Get a bound logger for the processing pipeline."""
    return structlog.get_logger(name)
