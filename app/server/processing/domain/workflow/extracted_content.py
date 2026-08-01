"""ExtractedContent model — clean text produced by a ContentExtractor."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from processing.domain.workflow.source import JobSource


class ExtractedContent(BaseModel):
    source: JobSource
    url: str
    title: str = ""
    clean_text: str = ""
    length: int = 0
    extraction_method: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
