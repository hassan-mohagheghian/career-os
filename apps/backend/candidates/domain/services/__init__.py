"""Candidate domain services (pure business logic, no infrastructure)."""

from candidates.domain.services.profile_merge_service import (
    CHILD_KINDS,
    CORE_FIELDS,
    MergeResult,
    ProfileDiff,
    ProfileMergeService,
    SectionDiff,
)

__all__ = [
    "CHILD_KINDS",
    "CORE_FIELDS",
    "MergeResult",
    "ProfileDiff",
    "ProfileMergeService",
    "SectionDiff",
]
