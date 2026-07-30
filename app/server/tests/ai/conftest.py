"""Shared test fixtures for the AI agent layer."""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv()


@pytest.fixture
def provider_config():
    from ai.infrastructure.providers.base import ProviderConfig
    return ProviderConfig(name="test", timeout=30)


@pytest.fixture
def mock_llm_provider():
    from ai.infrastructure.providers.mock import MockProvider
    return MockProvider()