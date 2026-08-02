"""Structured output models for the AI Tool Layer.

DDD Value Objects: Typed results that flow between tool nodes.
SOLID: Single source of truth for all tool output schemas.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class FetchStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CACHED = "cached"


class FetchError(BaseModel):
    """Typed error from a fetch operation."""
    code: str
    message: str
    url: str
    retryable: bool = False


class FetchedPage(BaseModel):
    """Structured result from fetching and preprocessing a web page."""
    url: str
    status: FetchStatus = FetchStatus.SUCCESS
    title: str = ""
    canonical_url: Optional[str] = None
    markdown: str = ""
    plain_text: str = ""
    language: str = "en"
    metadata: dict[str, Any] = Field(default_factory=dict)
    fetched_at: datetime = Field(default_factory=datetime.now)
    status_code: int = 200
    content_length: int = 0
    error: Optional[FetchError] = None
    cache_hit: bool = False

    @property
    def is_ok(self) -> bool:
        return self.status in (FetchStatus.SUCCESS, FetchStatus.CACHED)

    @property
    def short_text(self) -> str:
        return self.plain_text[:5000] if self.plain_text else ""


class ContentExtraction(BaseModel):
    """Structured result from content extraction pipeline."""
    raw_html: str = ""
    cleaned_text: str = ""
    main_content: str = ""
    sections: list[dict[str, Any]] = Field(default_factory=list)
    language: str = "en"
    word_count: int = 0
    extraction_method: str = "regex"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolExecutionLog(BaseModel):
    """Observability record for tool execution."""
    tool_name: str
    execution_time_ms: float = 0
    cache_hit: bool = False
    tokens_saved: int = 0
    provider_calls_avoided: int = 0
    success: bool = True
    error: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
