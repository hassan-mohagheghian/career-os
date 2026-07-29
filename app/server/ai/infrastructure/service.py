"""LLM Service — unified entry point for all AI calls.

SRP: Single responsibility — coordinate LLM interactions with logging,
error handling, and context management. This is the ONLY way existing
code should use the provider abstraction going forward.

Facade Pattern: Hides provider complexity behind a simple interface.
Observer Pattern: Logs all LLM interactions.
Template Method: Subclasses can override error handling.
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Optional

from .providers import get_provider
from .providers.base import LLMProvider, ProviderConfig, ProviderResponse

from shared.infrastructure.process.logging_config import get_logger
_log = get_logger("ai.service")


class LLMService:
    """Unified LLM service — the single entry point for all AI calls.

    Replaces: direct subprocess invocation, MimoRunner
    Uses: LLMProvider abstraction underneath.

    Design Patterns:
    - Facade: Simple interface over complex provider internals
    - Observer: Logs all LLM interactions with timing
    - Template Method: Error handling can be overridden
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider

    @property
    def provider(self) -> LLMProvider:
        """Lazy-load provider on first use."""
        if self._provider is None:
            self._provider = get_provider()
        return self._provider

    def generate(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Generate a text response from the LLM.

        Args:
            prompt: The prompt to send.
            context: Optional context (session_id, system_prompt, etc.).
            timeout: Optional timeout override.

        Returns:
            ProviderResponse with the generated content.
        """
        start = time.time()
        try:
            resp = self.provider.generate(prompt, context=context, timeout=timeout)
            duration = time.time() - start
            _log.info(
                "llm.generate",
                provider=self.provider.name,
                duration=round(duration, 3),
                content_length=len(resp.content),
            )
            return resp
        except Exception as e:
            duration = time.time() - start
            _log.error(
                "llm.generate_failed",
                provider=self.provider.name,
                error=str(e),
                duration=round(duration, 3),
            )
            raise

    def generate_structured(
        self,
        prompt: str,
        schema: Optional[dict] = None,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> ProviderResponse:
        """Generate a structured (JSON) response from the LLM.

        The prompt should instruct the LLM to write results to a
        specific output file. This method runs the LLM, then reads
        that file and parses the JSON.

        Args:
            prompt: The prompt to send.
            schema: Optional JSON schema for output.
            context: Optional context (result_file, pid, session_id, etc.).
            timeout: Optional timeout override.

        Returns:
            ProviderResponse with JSON-parsed content.
        """
        start = time.time()
        try:
            resp = self.provider.generate_structured(
                prompt, schema=schema, context=context, timeout=timeout
            )
            duration = time.time() - start
            _log.info(
                "llm.generate_structured",
                provider=self.provider.name,
                duration=round(duration, 3),
                result_file=context.get("result_file") if context else None,
            )
            return resp
        except Exception as e:
            duration = time.time() - start
            _log.error(
                "llm.generate_structured_failed",
                provider=self.provider.name,
                error=str(e),
                duration=round(duration, 3),
            )
            raise

    def generate_streaming(
        self,
        prompt: str,
        context: Optional[dict] = None,
        timeout: Optional[int] = None,
        on_event: Optional[Callable] = None,
        on_session_id: Optional[Callable] = None,
    ) -> ProviderResponse:
        """Generate with streaming event callbacks.

        Supports real-time event forwarding and session ID discovery.
        Used by workers that need live progress updates.

        Args:
            prompt: The prompt to send.
            context: Optional context (session_id, pid, key, cwd).
            timeout: Optional timeout override.
            on_event: Called for each JSON event from the LLM.
            on_session_id: Called when session_id is discovered.

        Returns:
            ProviderResponse with raw output lines in metadata.
        """
        start = time.time()

        # Try provider's generate_streaming first, fall back to generate
        if hasattr(self.provider, 'generate_streaming'):
            try:
                resp = self.provider.generate_streaming(
                    prompt, context=context, timeout=timeout,
                    on_event=on_event, on_session_id=on_session_id,
                )
                duration = time.time() - start
                _log.info(
                    "llm.generate_streaming",
                    provider=self.provider.name,
                    duration=round(duration, 3),
                    line_count=resp.metadata.get("line_count", 0),
                )
                return resp
            except Exception as e:
                duration = time.time() - start
                _log.error(
                    "llm.generate_streaming_failed",
                    provider=self.provider.name,
                    error=str(e),
                    duration=round(duration, 3),
                )
                raise
        else:
            # Fallback: use non-streaming generate
            return self.generate(prompt, context=context, timeout=timeout)

    def close(self):
        """Clean up provider resources."""
        if self._provider:
            self._provider.close()


# ── Module-level convenience ────────────────────────────────────────

_default_service: Optional[LLMService] = None


def get_llm_service(provider: Optional[LLMProvider] = None) -> LLMService:
    """Get or create the default LLM service.

    Singleton Pattern: returns cached instance.
    """
    global _default_service
    if _default_service is None or provider is not None:
        _default_service = LLMService(provider)
    return _default_service


def reset_llm_service():
    """Reset the default service (for testing)."""
    global _default_service
    _default_service = None
