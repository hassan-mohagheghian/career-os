"""Source model — a normalized input source for a job context.

The workflow collects all available job sources (primary URL, additional
URLs, notes) and normalizes them into JobSource models before fetching.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PRIMARY_URL = "primary_url"
    ADDITIONAL_URL = "additional_url"
    NOTE = "note"


class JobSource(BaseModel):
    url: str | None = None
    type: SourceType
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_fetchable(self) -> bool:
        return bool(self.url and self.url.startswith(("http://", "https://")))
