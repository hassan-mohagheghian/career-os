"""OpenAI API provider — stub for future implementation.

SRP: Only handles OpenAI API communication.
OCP: Extends LLMProvider without modifying it.
LSP: Can substitute any LLMProvider in agent code.
DIP: Depends on LLMProvider abstraction, not on OpenAI SDK directly.
"""

from __future__ import annotations

from typing import Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API (GPT-4, GPT-4o, etc.).

    Currently a stub. Full implementation requires:
    - openai or langchain-openai package
    - API key configuration
    - Model selection
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="openai"))
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self._config.api_key)
            except ImportError:
                raise RuntimeError(
                    "OpenAI provider requires the 'openai' package. "
                    "Install with: pip install openai"
                )

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        self._ensure_client()
        context = context or {}
        system_prompt = context.get("system_prompt", "You are a helpful assistant.")

        response = self._client.chat.completions.create(
            model=self._config.model or "gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            timeout=timeout or self._config.timeout,
        )

        content = response.choices[0].message.content or ""
        return ProviderResponse(
            content=content,
            metadata={"model": response.model, "finish_reason": response.choices[0].finish_reason},
            usage={"tokens": response.usage.total_tokens if response.usage else 0},
            provider="openai",
            model=response.model,
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        self._ensure_client()
        context = context or {}
        system_prompt = context.get(
            "system_prompt",
            "You are a helpful assistant. Always respond with valid JSON.",
        )

        response = self._client.chat.completions.create(
            model=self._config.model or "gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            timeout=timeout or self._config.timeout,
            response_format={"type": "json_object"} if schema else None,
        )

        content = response.choices[0].message.content or ""
        return ProviderResponse(
            content=content,
            metadata={"model": response.model, "finish_reason": response.choices[0].finish_reason},
            usage={"tokens": response.usage.total_tokens if response.usage else 0},
            provider="openai",
            model=response.model,
        )
