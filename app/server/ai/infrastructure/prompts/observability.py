from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class PromptLogEntry:
    identifier: str
    version: str
    provider: str
    prompt_type: str
    execution_time: float
    token_count: int = 0
    rendered_size: int = 0
    success: bool = True
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptLogger:
    def __init__(self):
        self._logs: list[PromptLogEntry] = []
        self._render_count: int = 0

    @property
    def render_count(self) -> int:
        return self._render_count

    @property
    def logs(self) -> list[PromptLogEntry]:
        return list(self._logs)

    def log_render(self, identifier: str, version: str, rendered_size: int) -> None:
        self._render_count += 1

    def log_execution(
        self,
        identifier: str,
        version: str,
        provider: str = "unknown",
        prompt_type: str = "unknown",
        token_count: int = 0,
        rendered_size: int = 0,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> PromptLogEntry:
        entry = PromptLogEntry(
            identifier=identifier,
            version=version,
            provider=provider,
            prompt_type=prompt_type,
            execution_time=0.0,
            token_count=token_count,
            rendered_size=rendered_size,
            success=success,
            error=error,
            metadata=metadata or {},
        )
        self._logs.append(entry)
        return entry

    def clear(self) -> None:
        self._logs.clear()
        self._render_count = 0


_logger: Optional[PromptLogger] = None


def get_prompt_logger() -> PromptLogger:
    global _logger
    if _logger is None:
        _logger = PromptLogger()
    return _logger


def reset_prompt_logger() -> None:
    global _logger
    _logger = None
