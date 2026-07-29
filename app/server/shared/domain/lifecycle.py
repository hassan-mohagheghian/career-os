from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class LifecycleStatus(str, Enum):
    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

    @classmethod
    def valid_transitions(cls) -> Dict[LifecycleStatus, Set[LifecycleStatus]]:
        return {
            cls.PENDING: {cls.QUEUED, cls.FAILED, cls.CANCELLED},
            cls.QUEUED: {cls.PROCESSING, cls.PENDING, cls.FAILED, cls.CANCELLED},
            cls.PROCESSING: {cls.COMPLETED, cls.FAILED, cls.CANCELLED},
            cls.COMPLETED: {cls.QUEUED},
            cls.FAILED: {cls.PENDING, cls.QUEUED},
            cls.CANCELLED: {cls.PENDING},
        }

    def can_transition_to(self, target: LifecycleStatus) -> bool:
        return target in self.valid_transitions().get(self, set())

    @property
    def is_terminal(self) -> bool:
        return self in (LifecycleStatus.COMPLETED, LifecycleStatus.FAILED, LifecycleStatus.CANCELLED)
