"""ProviderConfig — configuration value object for LLM providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for an LLM provider.

    Immutable value object — providers are configured once and replaced
    through configuration, not mutation.
    """
    name: str = "mimo"
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    timeout: int = 300
    temperature: float = 0.0
    max_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProviderConfig:
        return cls(
            name=data.get("name", "mimo"),
            model=data.get("model"),
            api_key=data.get("api_key"),
            base_url=data.get("base_url"),
            timeout=data.get("timeout", 300),
            temperature=data.get("temperature", 0.0),
            max_tokens=data.get("max_tokens"),
            extra=data.get("extra", {}),
        )
