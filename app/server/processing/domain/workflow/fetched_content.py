"""FetchedContent model — raw content returned by a ContentFetcher."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field

from processing.domain.workflow.source import JobSource


class FetchedContent(BaseModel):
    source: JobSource
    url: str
    success: bool
    content: str = ""
    content_type: str = "html"
    status_code: int | None = None
    error: str | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
