"""Tests for the unified AI Tool Layer.

TDD: Tests define the tool layer contract.
Covers: fetch, cache, models, registry, content extraction, web tools.
"""

import json
import os
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Models Tests ────────────────────────────────────────────────────

class TestFetchedPage:
    """FetchedPage is a value object — structured fetch result."""

    def test_success_page(self):
        from ai.infrastructure.tools.models import FetchedPage, FetchStatus
        page = FetchedPage(url="https://example.com", plain_text="Hello world")
        assert page.is_ok is True
        assert page.status == FetchStatus.SUCCESS
        assert page.plain_text == "Hello world"

    def test_cached_page(self):
        from ai.infrastructure.tools.models import FetchedPage, FetchStatus
        page = FetchedPage(url="https://example.com", plain_text="Hello", status=FetchStatus.CACHED)
        assert page.is_ok is True
        assert page.cache_hit is False

    def test_failed_page(self):
        from ai.infrastructure.tools.models import FetchedPage, FetchStatus, FetchError
        page = FetchedPage(
            url="https://example.com",
            status=FetchStatus.FAILED,
            error=FetchError(code="NOT_FOUND", message="Not found", url="https://example.com"),
        )
        assert page.is_ok is False
        assert page.error.code == "NOT_FOUND"

    def test_short_text_truncation(self):
        from ai.infrastructure.tools.models import FetchedPage
        page = FetchedPage(url="https://example.com", plain_text="x" * 10000)
        assert len(page.short_text) == 5000

    def test_content_length(self):
        from ai.infrastructure.tools.models import FetchedPage
        page = FetchedPage(url="https://example.com", plain_text="Hello", content_length=100)
        assert page.content_length == 100


class TestContentExtraction:
    """ContentExtraction is a value object — content extraction result."""

    def test_default_values(self):
        from ai.infrastructure.tools.models import ContentExtraction
        ext = ContentExtraction()
        assert ext.raw_html == ""
        assert ext.cleaned_text == ""
        assert ext.word_count == 0
        assert ext.extraction_method == "regex"

    def test_with_data(self):
        from ai.infrastructure.tools.models import ContentExtraction
        ext = ContentExtraction(
            cleaned_text="Hello world",
            main_content="Hello",
            word_count=2,
        )
        assert ext.word_count == 2


class TestToolExecutionLog:
    """ToolExecutionLog tracks tool execution for observability."""

    def test_log_entry(self):
        from ai.infrastructure.tools.models import ToolExecutionLog
        log = ToolExecutionLog(tool_name="web_fetch", execution_time_ms=42.5)
        assert log.tool_name == "web_fetch"
        assert log.execution_time_ms == 42.5
        assert log.success is True


# ── Fetch Tests ─────────────────────────────────────────────────────

class TestExtractContent:
    """Test the HTML content extraction pipeline."""

    def test_strip_scripts(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "<html><head><script>var x=1;</script></head><body><p>Hello world</p></body></html>"
        result = extract_content(html)
        assert "var x=1" not in result.cleaned_text
        assert "Hello world" in result.cleaned_text

    def test_strip_styles(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "<html><style>.red{color:red;}</style><body><p>Hello</p></body></html>"
        result = extract_content(html)
        assert ".red" not in result.cleaned_text

    def test_strip_html_tags(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "<p>Hello <b>world</b></p>"
        result = extract_content(html)
        assert "<p>" not in result.cleaned_text
        assert "Hello" in result.cleaned_text
        assert "world" in result.cleaned_text

    def test_normalize_whitespace(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "<p>Hello   world</p>"
        result = extract_content(html)
        assert "  " not in result.cleaned_text

    def test_main_content_extraction(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "Header stuff About The Role Real job content here"
        result = extract_content(html, content_markers=["About The Role"])
        assert "About The Role" in result.main_content
        assert "Real job content" in result.main_content

    def test_empty_html(self):
        from ai.infrastructure.tools.fetch import extract_content
        result = extract_content("")
        assert result.cleaned_text == ""
        assert result.word_count == 0

    def test_language_detection_english(self):
        from ai.infrastructure.tools.fetch import extract_content
        result = extract_content("<p>The software engineer is in the team</p>")
        assert result.language == "en"

    def test_entities_stripped(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "<p>Hello &amp; world &#169; test</p>"
        result = extract_content(html)
        assert "&amp;" not in result.cleaned_text
        assert "Hello" in result.cleaned_text

    def test_comments_stripped(self):
        from ai.infrastructure.tools.fetch import extract_content
        html = "<p>Hello</p><!-- comment --><p>World</p>"
        result = extract_content(html)
        assert "comment" not in result.cleaned_text


class TestFetchPage:
    """Test the fetch_page function with mocked HTTP."""

    @patch("ai.infrastructure.tools.fetch.urllib.request.urlopen")
    def test_successful_fetch(self, mock_urlopen):
        from ai.infrastructure.tools.fetch import fetch_page
        long_content = "We are looking for a software engineer to join our team. " * 10
        mock_resp = MagicMock()
        mock_resp.read.return_value = f"<html><body><p>About The Role {long_content}</p></body></html>".encode()
        mock_resp.status = 200
        mock_resp.url = "https://example.com/job"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        page = fetch_page("https://example.com/job")
        assert page.is_ok
        assert page.status_code == 200
        assert "software engineer" in page.plain_text.lower()

    @patch("ai.infrastructure.tools.fetch.urllib.request.urlopen")
    def test_404_returns_failed(self, mock_urlopen):
        import urllib.error
        from ai.infrastructure.tools.fetch import fetch_page
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com", 404, "Not Found", {}, None
        )
        page = fetch_page("https://example.com", max_retries=0)
        assert not page.is_ok
        assert page.error.code == "NOT_FOUND"

    @patch("ai.infrastructure.tools.fetch.urllib.request.urlopen")
    def test_403_returns_failed(self, mock_urlopen):
        import urllib.error
        from ai.infrastructure.tools.fetch import fetch_page
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com", 403, "Forbidden", {}, None
        )
        page = fetch_page("https://example.com", max_retries=0)
        assert not page.is_ok
        assert page.error.code == "ACCESS_DENIED"

    @patch("ai.infrastructure.tools.fetch.urllib.request.urlopen")
    def test_content_too_short(self, mock_urlopen):
        from ai.infrastructure.tools.fetch import fetch_page
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"<html><body>Hi</body></html>"
        mock_resp.status = 200
        mock_resp.url = "https://example.com"
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        page = fetch_page("https://example.com", max_retries=0)
        assert not page.is_ok
        assert page.error.code == "CONTENT_TOO_SHORT"

    def test_invalid_url(self):
        from ai.infrastructure.tools.fetch import fetch_page
        page = fetch_page("not-a-url")
        assert not page.is_ok
        assert page.error.code == "INVALID_URL"

    def test_empty_url(self):
        from ai.infrastructure.tools.fetch import fetch_page
        page = fetch_page("")
        assert not page.is_ok


# ── Cache Tests ─────────────────────────────────────────────────────

class TestContentCache:
    """ContentCache provides file-based caching with TTL."""

    def test_set_and_get(self):
        from ai.infrastructure.tools.cache import ContentCache
        from ai.infrastructure.tools.models import FetchedPage
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir, ttl_seconds=3600)
            page = FetchedPage(url="https://example.com", plain_text="Hello")
            cache.set("https://example.com", page)
            cached = cache.get("https://example.com")
            assert cached is not None
            assert cached.plain_text == "Hello"
            assert cached.cache_hit is True

    def test_expired_entry(self):
        from ai.infrastructure.tools.cache import ContentCache
        from ai.infrastructure.tools.models import FetchedPage
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir, ttl_seconds=0)
            page = FetchedPage(url="https://example.com", plain_text="Hello")
            cache.set("https://example.com", page)
            time.sleep(0.01)
            cached = cache.get("https://example.com")
            assert cached is None

    def test_invalidate(self):
        from ai.infrastructure.tools.cache import ContentCache
        from ai.infrastructure.tools.models import FetchedPage
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir)
            page = FetchedPage(url="https://example.com", plain_text="Hello")
            cache.set("https://example.com", page)
            assert cache.invalidate("https://example.com") is True
            assert cache.get("https://example.com") is None

    def test_clear(self):
        from ai.infrastructure.tools.cache import ContentCache
        from ai.infrastructure.tools.models import FetchedPage
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir)
            for i in range(3):
                page = FetchedPage(url=f"https://example.com/{i}", plain_text=f"Page {i}")
                cache.set(f"https://example.com/{i}", page)
            count = cache.clear()
            assert count == 3

    def test_stats(self):
        from ai.infrastructure.tools.cache import ContentCache
        from ai.infrastructure.tools.models import FetchedPage
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir)
            page = FetchedPage(url="https://example.com", plain_text="Hello")
            cache.set("https://example.com", page)
            cache.get("https://example.com")
            cache.get("https://nonexistent.com")
            stats = cache.stats
            assert stats["hits"] == 1
            assert stats["misses"] == 1

    def test_nonexistent_key(self):
        from ai.infrastructure.tools.cache import ContentCache
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir)
            assert cache.get("https://nonexistent.com") is None


# ── Registry Tests ──────────────────────────────────────────────────

class TestToolRegistry:
    """ToolRegistry manages tool registration and selection."""

    def test_register_and_get(self):
        from ai.infrastructure.tools.registry import ToolRegistry, ToolCategory
        from ai.infrastructure.tools.base import BaseTool, ToolResult

        class DummyTool(BaseTool):
            name = "dummy"
            description = "A dummy tool"
            def run(self, **kwargs):
                return ToolResult(success=True, data="ok")

        registry = ToolRegistry()
        registry.register(DummyTool(), ToolCategory.FETCH)
        reg = registry.get("dummy")
        assert reg is not None
        assert reg.tool.name == "dummy"

    def test_find_by_capability(self):
        from ai.infrastructure.tools.registry import ToolRegistry, ToolCategory, ToolPriority
        from ai.infrastructure.tools.base import BaseTool, ToolResult

        class FastTool(BaseTool):
            name = "fast"
            description = "Fast tool"
            def run(self, **kwargs):
                return ToolResult(success=True)

        class SlowTool(BaseTool):
            name = "slow"
            description = "Slow tool"
            def run(self, **kwargs):
                return ToolResult(success=True)

        registry = ToolRegistry()
        registry.register(FastTool(), ToolCategory.FETCH, ToolPriority.LOCAL, capabilities=["http"])
        registry.register(SlowTool(), ToolCategory.FETCH, ToolPriority.PROVIDER_NATIVE, capabilities=["http"])

        candidates = registry.find_by_capability("http")
        assert len(candidates) == 2
        assert candidates[0].tool.name == "fast"  # LOCAL first

    def test_select_tool(self):
        from ai.infrastructure.tools.registry import ToolRegistry, ToolCategory, ToolPriority
        from ai.infrastructure.tools.base import BaseTool, ToolResult

        class MyTool(BaseTool):
            name = "my_tool"
            description = "My tool"
            def run(self, **kwargs):
                return ToolResult(success=True)

        registry = ToolRegistry()
        registry.register(MyTool(), ToolCategory.EXTRACT, capabilities=["text"])
        tool = registry.select_tool("text")
        assert tool is not None
        assert tool.name == "my_tool"

    def test_execute_tool(self):
        from ai.infrastructure.tools.registry import ToolRegistry, ToolCategory
        from ai.infrastructure.tools.base import BaseTool, ToolResult

        class ExecTool(BaseTool):
            name = "exec"
            description = "Executable tool"
            def run(self, **kwargs):
                return ToolResult(success=True, data=kwargs.get("x", 0) * 2)

        registry = ToolRegistry()
        registry.register(ExecTool(), ToolCategory.TRANSFORM)
        result = registry.execute("exec", x=5)
        assert result.success
        assert result.data == 10

    def test_execute_nonexistent_tool(self):
        from ai.infrastructure.tools.registry import ToolRegistry
        registry = ToolRegistry()
        result = registry.execute("nonexistent")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_stats(self):
        from ai.infrastructure.tools.registry import ToolRegistry, ToolCategory
        from ai.infrastructure.tools.base import BaseTool, ToolResult

        class StatTool(BaseTool):
            name = "stat"
            description = "Stat tool"
            def run(self, **kwargs):
                return ToolResult(success=True)

        registry = ToolRegistry()
        registry.register(StatTool(), ToolCategory.FETCH)
        registry.execute("stat")
        stats = registry.stats
        assert stats["total_tools"] == 1
        assert stats["total_executions"] == 1


# ── Web Tool Tests ──────────────────────────────────────────────────

class TestWebFetchTool:
    """WebFetchTool is the unified entry point for URL fetching."""

    def test_tool_name(self):
        from ai.infrastructure.tools.web import WebFetchTool
        tool = WebFetchTool()
        assert tool.name == "web_fetch"

    def test_requires_url(self):
        from ai.infrastructure.tools.web import WebFetchTool
        tool = WebFetchTool()
        result = tool.run()
        assert not result.success
        assert "url" in result.error.lower()

    @patch("ai.infrastructure.tools.web.fetch_page")
    def test_run_with_mock(self, mock_fetch):
        from ai.infrastructure.tools.web import WebFetchTool
        from ai.infrastructure.tools.models import FetchedPage
        mock_fetch.return_value = FetchedPage(
            url="https://example.com",
            plain_text="Job content here",
        )
        tool = WebFetchTool(use_cache=False)
        result = tool.run(url="https://example.com")
        assert result.success
        assert "Job content" in result.data.get("plain_text", "")

    def test_schema(self):
        from ai.infrastructure.tools.web import WebFetchTool
        tool = WebFetchTool()
        schema = tool.input_schema
        assert schema["type"] == "object"
        assert "url" in schema["properties"]


class TestCompanyFetchTool:
    def test_tool_name(self):
        from ai.infrastructure.tools.web import CompanyFetchTool
        tool = CompanyFetchTool()
        assert tool.name == "company_web_fetch"

    def test_longer_max_length(self):
        from ai.infrastructure.tools.web import CompanyFetchTool
        tool = CompanyFetchTool()
        assert tool._max_length == 8000


class TestMultiSourceFetchTool:
    def test_tool_name(self):
        from ai.infrastructure.tools.web import MultiSourceFetchTool
        tool = MultiSourceFetchTool()
        assert tool.name == "multi_source_fetch"

    def test_empty_sources(self):
        from ai.infrastructure.tools.web import MultiSourceFetchTool
        tool = MultiSourceFetchTool()
        result = tool.run()
        assert not result.success

    @patch("ai.infrastructure.tools.web.WebFetchTool.fetch_direct")
    def test_with_notes(self, mock_fetch):
        from ai.infrastructure.tools.web import MultiSourceFetchTool
        from ai.infrastructure.tools.models import FetchedPage
        mock_fetch.return_value = FetchedPage(
            url="https://example.com",
            plain_text="Fetched content",
        )
        tool = MultiSourceFetchTool()
        result = tool.run(notes=[{"type": "text", "content": "My note"}])
        assert result.success
        assert "My note" in result.data


# ── Integration Tests ───────────────────────────────────────────────

class TestToolLayerIntegration:
    """Integration tests for the complete tool layer."""

    def test_fetch_page_returns_structured_result(self):
        from ai.infrastructure.tools.models import FetchedPage
        page = FetchedPage(
            url="https://example.com",
            plain_text="Test content",
            status_code=200,
            content_length=12,
        )
        dump = page.model_dump(mode="json")
        assert isinstance(dump, dict)
        assert dump["url"] == "https://example.com"

    def test_cache_roundtrip_with_fetch(self):
        from ai.infrastructure.tools.cache import ContentCache
        from ai.infrastructure.tools.models import FetchedPage
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ContentCache(cache_dir=tmpdir)
            original = FetchedPage(url="https://test.com", plain_text="Content")
            cache.set("https://test.com", original)
            restored = cache.get("https://test.com")
            assert restored.plain_text == "Content"
            assert restored.cache_hit is True
