"""ProviderResponse — standardized response from LLM providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderResponse:
    """Standardized response from an LLM provider.

    All providers return this type regardless of their internal implementation.
    Business code consumes only this type.
    """
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    model: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.content

    @property
    def content_length(self) -> int:
        return len(self.content)
