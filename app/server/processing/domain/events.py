from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class ExecutionQueued(DomainEvent):
    execution_id: str = ""
    execution_type: str = ""
    target_type: str = ""
    target_id: str = ""
    queued_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ExecutionStarted(DomainEvent):
    execution_id: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ExecutionStepChanged(DomainEvent):
    execution_id: str = ""
    current_step: str = ""
    current_step_index: int = 0
    total_steps: int = 0
    progress: float = 0.0
    message: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class ExecutionCompleted(DomainEvent):
    execution_id: str = ""
    completed_at: datetime = field(default_factory=datetime.utcnow)
    duration: float = 0.0


@dataclass(frozen=True)
class ExecutionFailed(DomainEvent):
    execution_id: str = ""
    failed_at: datetime = field(default_factory=datetime.utcnow)
    error_code: str = ""
    error_message: str = ""
