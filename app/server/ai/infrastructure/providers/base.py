"""Base provider interface — contracts for all LLM providers.

Uses langchain-core BaseChatModel as the foundation so that agents
can use LangChain-compatible tool calling and structured output.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str = "mimo"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 300
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Standardized response from an LLM provider."""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    usage: dict[str, Any] = field(default_factory=dict)
    provider: str = ""
    model: str = ""


class LLMProvider(abc.ABC):
    """Abstract base class for LLM providers.

    All agents communicate with LLMs through this interface.
    Providers never call subprocess directly —
    that's an implementation detail of concrete providers.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        self._config = config or ProviderConfig()

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Generate a text response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.
            context: Optional context dict (session_id, system prompt, etc.).
            timeout: Optional timeout override in seconds.

        Returns:
            ProviderResponse with the generated content.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Generate a structured (JSON) response from the LLM.

        Args:
            prompt: The prompt to send.
            schema: Optional JSON schema for output structure.
            context: Optional context dict.
            timeout: Optional timeout override.

        Returns:
            ProviderResponse with JSON-parsed content.
        """
        raise NotImplementedError

    def as_langchain_llm(self) -> BaseChatModel:
        """Return a LangChain-compatible chat model wrapper.

        Override in subclasses to provide a native LangChain integration.
        The default wraps this provider's generate() into a simple LLM.
        """
        from .langchain_wrapper import ProviderChatModel
        return ProviderChatModel(provider=self)

    def close(self):
        """Clean up provider resources. Override if needed."""
        pass
