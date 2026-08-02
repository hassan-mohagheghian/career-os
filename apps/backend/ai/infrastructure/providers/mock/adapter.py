"""Mock LLM provider — deterministic provider for testing.

SRP: Only handles returning canned responses for tests.
OCP: Extends LLMProvider without modifying it.
LSP: Can substitute any LLMProvider in agent code.
DIP: Depends on LLMProvider abstraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..base import LLMProvider, ProviderConfig, ProviderResponse


@dataclass
class CallRecord:
    """Records a single call to the mock provider."""
    method: str
    prompt: str
    schema: Optional[dict] = None
    context: Optional[dict] = None
    timeout: Optional[int] = None


class MockProvider(LLMProvider):
    """Deterministic LLM provider for testing.

    Returns configurable canned responses. Tracks all calls for assertions.

    Configure via ProviderConfig.extra:
        mock_response: str          — return value for generate()
        mock_structured_response: str — return value for generate_structured()
        mock_error: Exception       — raise this on generate()
        mock_structured_error: Exception — raise this on generate_structured()
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(name="mock"))
        self._mock_response: str = self._config.extra.get("mock_response", "mock response")
        self._mock_structured_response: str = self._config.extra.get(
            "mock_structured_response", '{"result": "mock"}'
        )
        self._mock_error: Optional[Exception] = self._config.extra.get("mock_error")
        self._mock_structured_error: Optional[Exception] = self._config.extra.get("mock_structured_error")
        self._calls: list[CallRecord] = []

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        self._calls.append(CallRecord(
            method="generate", prompt=prompt, context=context, timeout=timeout,
        ))
        if self._mock_error is not None:
            raise self._mock_error
        return ProviderResponse(
            content=self._mock_response,
            metadata={"mock": True},
            provider="mock",
            model="mock-model",
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        self._calls.append(CallRecord(
            method="generate_structured", prompt=prompt,
            schema=schema, context=context, timeout=timeout,
        ))
        if self._mock_structured_error is not None:
            raise self._mock_structured_error
        return ProviderResponse(
            content=self._mock_structured_response,
            metadata={"mock": True},
            provider="mock",
            model="mock-model",
        )

    @property
    def calls(self) -> list[CallRecord]:
        """All recorded calls."""
        return list(self._calls)

    @property
    def generate_calls(self) -> list[CallRecord]:
        """Only generate() calls."""
        return [c for c in self._calls if c.method == "generate"]

    @property
    def structured_calls(self) -> list[CallRecord]:
        """Only generate_structured() calls."""
        return [c for c in self._calls if c.method == "generate_structured"]

    def reset(self):
        """Clear call history."""
        self._calls.clear()
