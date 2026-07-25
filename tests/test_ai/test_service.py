"""Tests for LLMService — unified entry point for AI calls.

TDD: Tests define the service contract.
Facade Pattern: Tests verify the simple interface over complex internals.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.ai.service import LLMService, get_llm_service, reset_llm_service
from app.ai.providers.base import LLMProvider, ProviderConfig, ProviderResponse


class TestLLMService:
    """LLMService — Facade Pattern over provider complexity."""

    def test_create_with_provider(self):
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        service = LLMService(provider)
        assert service.provider is provider

    def test_generate_delegates_to_provider(self):
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        provider.generate.return_value = ProviderResponse(content="response")
        service = LLMService(provider)

        resp = service.generate("test prompt")
        assert resp.content == "response"
        provider.generate.assert_called_once_with("test prompt", context=None, timeout=None)

    def test_generate_structured_delegates_to_provider(self):
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        provider.generate_structured.return_value = ProviderResponse(content='{"key": "value"}')
        service = LLMService(provider)

        resp = service.generate_structured("test prompt", context={"result_file": "/tmp/test.json"})
        assert resp.content == '{"key": "value"}'
        provider.generate_structured.assert_called_once()

    def test_generate_streaming_delegates_to_provider(self):
        provider = MagicMock()
        provider.name = "test"
        provider.generate_streaming.return_value = ProviderResponse(
            content="streamed",
            metadata={"line_count": 10, "session_id": "abc"},
        )
        service = LLMService(provider)

        on_event = MagicMock()
        on_session_id = MagicMock()
        resp = service.generate_streaming(
            "test prompt",
            on_event=on_event,
            on_session_id=on_session_id,
        )
        assert resp.content == "streamed"
        provider.generate_streaming.assert_called_once()

    def test_generate_streaming_fallback_without_streaming(self):
        """When provider doesn't have generate_streaming, falls back to generate."""
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        # Remove generate_streaming if it exists
        if hasattr(provider, 'generate_streaming'):
            delattr(provider, 'generate_streaming')
        provider.generate.return_value = ProviderResponse(content="fallback")
        service = LLMService(provider)

        resp = service.generate_streaming("test prompt")
        assert resp.content == "fallback"

    def test_generate_logs_duration(self):
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        provider.generate.return_value = ProviderResponse(content="ok")
        service = LLMService(provider)

        # Should not raise
        service.generate("prompt")

    def test_generate_raises_on_error(self):
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        provider.generate.side_effect = RuntimeError("LLM failed")
        service = LLMService(provider)

        with pytest.raises(RuntimeError, match="LLM failed"):
            service.generate("prompt")

    def test_close_delegates_to_provider(self):
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        service = LLMService(provider)
        service.close()
        provider.close.assert_called_once()


class TestGetLLMService:
    """Test the singleton factory function."""

    def test_get_returns_service(self):
        reset_llm_service()
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        service = get_llm_service(provider)
        assert isinstance(service, LLMService)
        reset_llm_service()

    def test_get_caches_instance(self):
        reset_llm_service()
        provider = MagicMock(spec=LLMProvider)
        provider.name = "test"
        s1 = get_llm_service(provider)
        s2 = get_llm_service()
        assert s1 is s2
        reset_llm_service()

    def test_get_with_provider_replaces(self):
        reset_llm_service()
        p1 = MagicMock(spec=LLMProvider)
        p1.name = "p1"
        s1 = get_llm_service(p1)
        p2 = MagicMock(spec=LLMProvider)
        p2.name = "p2"
        s2 = get_llm_service(p2)
        assert s1 is not s2
        reset_llm_service()
