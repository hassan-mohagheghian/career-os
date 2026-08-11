"""DocumentService — edits and deletes versioned application documents.

Documents are created by the application intelligence workflow (see the
processing context); this service handles the user's post-generation actions:
editing the content of a version and deleting a version.
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from applications.domain.event_publisher import ApplicationEventPublisher, InMemoryEventCollector
from applications.domain.events import ApplicationDocumentDeleted, ApplicationDocumentUpdated
from shared.application.exceptions import NotFoundError, ValidationError


class DocumentService:
    """Business operations for application documents."""

    def __init__(
        self,
        document_repo: Any,
        event_publisher: ApplicationEventPublisher | None = None,
    ):
        self._repo = document_repo
        self.event_publisher = event_publisher or InMemoryEventCollector()

    def update_content(self, document_id: str, content: str) -> dict[str, Any]:
        if not str(content).strip():
            raise ValidationError("Document content must not be empty")
        current = self._repo.get_by_id(document_id)
        if not current:
            raise NotFoundError(f"Document {document_id} not found")
        stored = self._repo.update(
            document_id,
            {
                "content": content,
                "updated_at": datetime.now(UTC).isoformat(),
            },
        ) or current
        self._emit(
            ApplicationDocumentUpdated(
                aggregate_id=current.get("application_id"),
                application_id=current.get("application_id") or "",
                document_id=document_id,
                document_type=current.get("document_type") or "",
                version=int(current.get("version") or 1),
            )
        )
        return stored

    def delete(self, document_id: str) -> None:
        current = self._repo.get_by_id(document_id)
        if not current:
            raise NotFoundError(f"Document {document_id} not found")
        self._repo.delete(document_id)
        self._emit(
            ApplicationDocumentDeleted(
                aggregate_id=current.get("application_id"),
                application_id=current.get("application_id") or "",
                document_id=document_id,
                document_type=current.get("document_type") or "",
            )
        )

    def _emit(self, event: Any) -> None:
        try:
            self.event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — best-effort publishing
            pass


__all__ = ["DocumentService"]
