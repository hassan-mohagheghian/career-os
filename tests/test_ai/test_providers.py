"""Tests for the LLM Provider abstraction layer.

TDD: These tests define the contract that providers must satisfy.
Run first (red), then implement providers to make them pass (green).
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.ai.providers.base import LLMProvider, ProviderConfig, ProviderResponse


# ── Value Object Tests ──────────────────────────────────────────────

class TestProviderConfig:
    """ProviderConfig is a value object — immutable configuration."""

    def test_default_config(self):
        config = ProviderConfig()
        assert config.name == "mimo"
        assert config.timeout == 300
        assert config.temperature == 0.0
        assert config.extra == {}

    def test_custom_config(self):
        config = ProviderConfig(name="openai", model="gpt-4", api_key="sk-test")
        assert config.name == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "sk-test"

    def test_config_equality(self):
        a = ProviderConfig(name="mimo", timeout=100)
        b = ProviderConfig(name="mimo", timeout=100)
        assert a == b


class TestProviderResponse:
    """ProviderResponse is a value object — standardized LLM response."""

    def test_minimal_response(self):
        resp = ProviderResponse(content="hello")
        assert resp.content == "hello"
        assert resp.metadata == {}
        assert resp.usage == {}

    def test_full_response(self):
        resp = ProviderResponse(
            content="result",
            metadata={"duration": 1.5},
            usage={"tokens": 100},
            provider="mimo",
            model="mimo-cli",
        )
        assert resp.provider == "mimo"
        assert resp.metadata["duration"] == 1.5


# ── Interface Contract Tests ────────────────────────────────────────

class TestLLMProviderContract:
    """Test the LLMProvider abstract interface.

    SRP: Each test verifies one aspect of the provider contract.
    DIP: Tests depend on the abstraction, not concrete implementations.
    """

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_concrete_provider_must_implement_generate(self):
        class IncompleteProvider(LLMProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_concrete_provider_must_implement_generate_structured(self):
        class PartialProvider(LLMProvider):
            def generate(self, prompt, context=None, timeout=None):
                return ProviderResponse(content="ok")

        with pytest.raises(TypeError):
            PartialProvider()

    def test_concrete_provider_satisfies_interface(self):
        class ValidProvider(LLMProvider):
            def generate(self, prompt, context=None, timeout=None):
                return ProviderResponse(content="ok")

            def generate_structured(self, prompt, schema=None, context=None, timeout=None):
                return ProviderResponse(content='{"ok": true}')

        provider = ValidProvider()
        assert isinstance(provider, LLMProvider)
        resp = provider.generate("test prompt")
        assert resp.content == "ok"

    def test_provider_name_property(self):
        class MyProvider(LLMProvider):
            def generate(self, prompt, context=None, timeout=None):
                return ProviderResponse(content="ok")

            def generate_structured(self, prompt, schema=None, context=None, timeout=None):
                return ProviderResponse(content="ok")

        provider = MyProvider(ProviderConfig(name="custom"))
        assert provider.name == "custom"

    def test_provider_config_property(self):
        class MyProvider(LLMProvider):
            def generate(self, prompt, context=None, timeout=None):
                return ProviderResponse(content="ok")

            def generate_structured(self, prompt, schema=None, context=None, timeout=None):
                return ProviderResponse(content="ok")

        config = ProviderConfig(name="test", timeout=60)
        provider = MyProvider(config)
        assert provider.config is config

    def test_close_is_optional(self):
        class MinimalProvider(LLMProvider):
            def generate(self, prompt, context=None, timeout=None):
                return ProviderResponse(content="ok")

            def generate_structured(self, prompt, schema=None, context=None, timeout=None):
                return ProviderResponse(content="ok")

        provider = MinimalProvider()
        provider.close()  # Should not raise


# ── Provider Factory Tests ──────────────────────────────────────────

class TestProviderFactory:
    """Test the provider registry and factory.

    Factory Pattern: get_provider() creates providers by name.
    Singleton Pattern: same name returns cached instance.
    """

    def test_get_provider_returns_llm_provider(self):
        from app.ai.providers import get_provider, reset_providers
        reset_providers()
        provider = get_provider("mimo")
        assert isinstance(provider, LLMProvider)
        reset_providers()

    def test_get_provider_caches_instances(self):
        from app.ai.providers import get_provider, reset_providers
        reset_providers()
        p1 = get_provider("mimo")
        p2 = get_provider("mimo")
        assert p1 is p2
        reset_providers()

    def test_get_provider_default_uses_env(self):
        from app.ai.providers import get_provider, reset_providers
        reset_providers()
        with patch.dict("os.environ", {"AI_PROVIDER": "mimo"}):
            provider = get_provider()
            assert isinstance(provider, LLMProvider)
        reset_providers()

    def test_get_provider_unknown_raises(self):
        from app.ai.providers import get_provider, reset_providers
        reset_providers()
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent")
        reset_providers()

    def test_get_provider_openai_stub(self):
        from app.ai.providers import get_provider, reset_providers
        reset_providers()
        provider = get_provider("openai")
        assert isinstance(provider, LLMProvider)
        assert provider.name == "openai"
        reset_providers()

    def test_get_provider_local_stub(self):
        from app.ai.providers import get_provider, reset_providers
        reset_providers()
        provider = get_provider("local")
        assert isinstance(provider, LLMProvider)
        assert provider.name == "local"
        reset_providers()
