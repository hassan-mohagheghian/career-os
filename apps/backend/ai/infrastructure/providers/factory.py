"""ProviderFactory — creates and configures LLM providers.

Strategy Pattern: Different providers are created based on configuration.
Factory Pattern: Encapsulates provider creation logic.
"""

from __future__ import annotations

import os
from typing import Optional

from ...domain.value_objects.provider_config import ProviderConfig
from .base import LLMProvider


class ProviderFactory:
    """Factory for creating LLM providers based on configuration."""

    _providers: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """Register a provider class."""
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, config: Optional[ProviderConfig] = None) -> LLMProvider:
        """Create a provider based on configuration.

        Args:
            config: Provider configuration. If None, uses environment variables.

        Returns:
            Configured LLMProvider instance.
        """
        if config is None:
            config = cls._config_from_env()

        provider_class = cls._providers.get(config.name)
        if provider_class is None:
            raise ValueError(f"Unknown provider: {config.name}")

        return provider_class(config)

    @classmethod
    def _config_from_env(cls) -> ProviderConfig:
        """Create configuration from environment variables."""
        return ProviderConfig(
            name=os.getenv("AI_PROVIDER", "mimo"),
            model=os.getenv("AI_MODEL"),
            api_key=os.getenv("AI_API_KEY"),
            base_url=os.getenv("AI_BASE_URL"),
            timeout=int(os.getenv("AI_TIMEOUT", "300")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.0")),
        )

    @classmethod
    def available_providers(cls) -> list[str]:
        """List available provider names."""
        return list(cls._providers.keys())
