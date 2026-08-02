"""AI Agent structured logging — extends structlog for agent events.

SRP: Only handles agent-specific logging.
Observer Pattern: Emits structured events at agent lifecycle points.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from shared.infrastructure.process.logging_config import get_logger


_log = get_logger("ai")


def agent_started(agent_name: str, provider: str = "", **kwargs):
    """Log agent execution start."""
    _log.info("agent_started", agent=agent_name, provider=provider, **kwargs)


def agent_completed(agent_name: str, duration: float, provider: str = "", **kwargs):
    """Log agent execution completion."""
    _log.info(
        "agent_completed",
        agent=agent_name,
        provider=provider,
        duration=round(duration, 3),
        status="success",
        **kwargs,
    )


def agent_failed(agent_name: str, error: str, duration: float, provider: str = "", **kwargs):
    """Log agent execution failure."""
    _log.warning(
        "agent_failed",
        agent=agent_name,
        provider=provider,
        error=error,
        duration=round(duration, 3),
        status="failed",
        **kwargs,
    )


def provider_called(provider: str, model: str, duration: float, **kwargs):
    """Log LLM provider call."""
    _log.info(
        "provider_called",
        provider=provider,
        model=model,
        duration=round(duration, 3),
        **kwargs,
    )


def workflow_finished(workflow_name: str, duration: float, nodes: int, errors: int = 0, **kwargs):
    """Log workflow graph completion."""
    _log.info(
        "workflow_finished",
        workflow=workflow_name,
        duration=round(duration, 3),
        nodes=nodes,
        errors=errors,
        status="completed" if errors == 0 else "completed_with_errors",
        **kwargs,
    )
