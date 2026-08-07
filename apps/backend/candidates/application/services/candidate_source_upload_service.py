"""CandidateSourceUploadService — records a raw profile document as a candidate
source version.

Uploaded sources (resume / LinkedIn) are stored on the current candidate
profile with a per-type version number, PII masked (matching the legacy Resume
page privacy behavior), and left ``pending`` so the next candidate processing
run picks them up and marks them ``processed``.

Domain events are emitted through the CandidateEventPublisher port
(in-memory collector by default — EDD is incremental, no pub/sub yet).
"""

from __future__ import annotations

from typing import Any

from candidates.domain.event_publisher import CandidateEventPublisher, InMemoryEventCollector
from candidates.domain.events import CandidateSourceAdded
from shared.infrastructure.utils import mask_pii

SUPPORTED_SOURCE_TYPES = ("resume", "linkedin")


class CandidateSourceUploadService:
    """Upload raw profile text as a new candidate source version."""

    def __init__(
        self,
        profile_repo: Any,
        source_repo: Any,
        event_publisher: CandidateEventPublisher | None = None,
    ):
        self._profile_repo = profile_repo
        self._source_repo = source_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def upload(self, source_type: str, raw_text: str) -> dict[str, Any]:
        """Store ``raw_text`` as the next version of ``source_type`` for the
        current profile. Returns the stored source row."""
        if source_type not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(f"Unsupported source type: {source_type}")

        profile = self._profile_repo.get_or_create_current()
        profile_id = profile["id"]
        version = self._source_repo.get_next_version(profile_id, source_type)
        stored = self._source_repo.create(
            {
                "profile_id": profile_id,
                "source_type": source_type,
                "version": version,
                "raw_text": mask_pii(raw_text),
                "status": "pending",
            }
        )
        try:
            self.event_publisher.publish(
                CandidateSourceAdded(
                    aggregate_id=profile_id,
                    profile_id=profile_id,
                    source_type=source_type,
                    version=version,
                )
            )
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass
        return stored


__all__ = ["CandidateSourceUploadService", "SUPPORTED_SOURCE_TYPES"]
