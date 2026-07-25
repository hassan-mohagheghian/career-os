"""Local LLM provider — stub for Ollama and local model support.

SRP: Only handles local LLM communication.
OCP: Extends LLMProvider without modifying it.
LSP: Can substitute any LLMProvider in agent code.
DIP: Depends on LLMProvider abstraction.
"""

from __future__ import annotations

import json
from typing import Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse


class LocalLLMProvider(LLMProvider):
    """Provider for local LLMs (Ollama, llama.cpp, vLLM, etc.).

    Currently a stub. Full implementation requires:
    - ollama package or HTTP client for local API
    - Model name configuration
    - Base URL for local server
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="local"))
        self._base_url = self._config.base_url or "http://localhost:11434"

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        raise NotImplementedError(
            "Local LLM provider requires setup. "
            "Configure base_url and model in ProviderConfig. "
            "Supports Ollama API format at {self._base_url}"
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        raise NotImplementedError(
            "Local LLM provider requires setup. "
            "Configure base_url and model in ProviderConfig."
        )
