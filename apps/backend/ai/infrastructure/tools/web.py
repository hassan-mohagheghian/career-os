"""Unified web fetch tool — the single entry point for all URL fetching.

Replaces all duplicated _fetch_url functions. Uses local-first philosophy:
fetch, preprocess, cache, and return structured content.

SOLID: Single responsibility — fetching and preprocessing web content.
"""

from __future__ import annotations

from typing import Any, Optional

from .base import BaseTool, ToolResult
from .cache import get_content_cache
from .fetch import fetch_page, MAX_CONTENT_LENGTH, COMPANY_MAX_LENGTH
from .models import FetchedPage, FetchStatus


class WebFetchTool(BaseTool):
    """Fetches and preprocesses web content locally.

    Priority: Local HTTP → HTML clean → content extraction → cache → return.
    Never sends raw URLs to the LLM.
    """

    def __init__(
        self,
        max_length: int = MAX_CONTENT_LENGTH,
        use_cache: bool = True,
        ttl_seconds: int = 3600 * 6,
    ):
        self._max_length = max_length
        self._use_cache = use_cache
        self._ttl_seconds = ttl_seconds

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return (
            "Fetch a URL and return cleaned, structured content. "
            "Handles redirects, retries, encoding, HTML cleaning, and caching. "
            "Returns plain text suitable for LLM consumption."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch and preprocess",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum text length to return",
                    "default": self._max_length,
                },
                "use_cache": {
                    "type": "boolean",
                    "description": "Whether to use cached results",
                    "default": self._use_cache,
                },
            },
            "required": ["url"],
        }

    def run(self, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        if not url:
            return ToolResult(success=False, error="url parameter is required")

        use_cache = kwargs.get("use_cache", self._use_cache)
        max_length = kwargs.get("max_length", self._max_length)

        if use_cache:
            cache = get_content_cache(ttl_seconds=self._ttl_seconds)
            cached = cache.get(url)
            if cached is not None:
                cached.plain_text = cached.plain_text[:max_length]
                return ToolResult(
                    success=True,
                    data=cached.model_dump(mode="json"),
                    metadata={"url": url, "cache_hit": True, "length": len(cached.plain_text)},
                )

        page = fetch_page(url, max_length=max_length)

        if use_cache and page.is_ok:
            cache = get_content_cache(ttl_seconds=self._ttl_seconds)
            cache.set(url, page)

        if page.is_ok:
            return ToolResult(
                success=True,
                data=page.model_dump(mode="json"),
                metadata={
                    "url": url,
                    "cache_hit": False,
                    "status_code": page.status_code,
                    "length": len(page.plain_text),
                },
            )
        else:
            return ToolResult(
                success=False,
                error=page.error.message if page.error else "Fetch failed",
                metadata={"url": url, "status": page.status.value},
            )

    def fetch_direct(self, url: str, **kwargs) -> FetchedPage:
        """Direct fetch returning a typed FetchedPage (for use by other tools)."""
        max_length = kwargs.get("max_length", self._max_length)
        use_cache = kwargs.get("use_cache", self._use_cache)

        if use_cache:
            cache = get_content_cache(ttl_seconds=self._ttl_seconds)
            cached = cache.get(url)
            if cached is not None:
                cached.plain_text = cached.plain_text[:max_length]
                return cached

        page = fetch_page(url, max_length=max_length)

        if use_cache and page.is_ok:
            cache = get_content_cache(ttl_seconds=self._ttl_seconds)
            cache.set(url, page)

        return page


class CompanyFetchTool(WebFetchTool):
    """Fetch tool optimized for company pages (longer content)."""

    def __init__(self, **kwargs):
        super().__init__(max_length=COMPANY_MAX_LENGTH, **kwargs)

    @property
    def name(self) -> str:
        return "company_web_fetch"

    @property
    def description(self) -> str:
        return (
            "Fetch a company page and return cleaned content. "
            "Uses longer content limits for company intelligence."
        )


class MultiSourceFetchTool(BaseTool):
    """Fetches content from multiple sources (URLs + text notes + links).

    Consolidates _fetch_multi_source from worker.py.
    """

    def __init__(self, max_total_length: int = 8000):
        self._max_total_length = max_total_length
        self._fetcher = WebFetchTool()

    @property
    def name(self) -> str:
        return "multi_source_fetch"

    @property
    def description(self) -> str:
        return (
            "Fetch content from multiple sources: URLs, text notes, and link objects. "
            "Combines all content into a single cleaned text."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Main URL to fetch"},
                "notes": {
                    "type": "array",
                    "description": "Text/URL notes to include",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["text", "url"]},
                            "content": {"type": "string"},
                        },
                    },
                },
                "links": {
                    "type": "array",
                    "description": "Link objects to fetch",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "title": {"type": "string"},
                        },
                    },
                },
            },
        }

    def run(self, **kwargs) -> ToolResult:
        url = kwargs.get("url", "")
        notes = kwargs.get("notes", [])
        links = kwargs.get("links", [])

        parts = []
        failed_urls = []

        for note in notes:
            note_type = note.get("type", "text")
            content = note.get("content", "").strip()
            if not content:
                continue
            if note_type == "url" or content.startswith("http"):
                result = self._fetcher.run(url=content, max_length=MAX_CONTENT_LENGTH)
                if result.success:
                    parts.append(f"[URL] {result.data.get('plain_text', '')}")
                else:
                    failed_urls.append(content)
            else:
                parts.append(f"[NOTE] {content}")

        if url and url.startswith("http"):
            result = self._fetcher.run(url=url, max_length=MAX_CONTENT_LENGTH)
            if result.success:
                parts.append(result.data.get("plain_text", ""))
            else:
                failed_urls.append(url)

        for link in links:
            link_url = link.get("url", "")
            if link_url and link_url.startswith("http"):
                title = link.get("title", "Link")
                result = self._fetcher.run(url=link_url, max_length=MAX_CONTENT_LENGTH)
                if result.success:
                    parts.append(f"[{title}] {result.data.get('plain_text', '')}")
                else:
                    failed_urls.append(link_url)

        combined = "\n\n".join(parts)[: self._max_total_length]

        return ToolResult(
            success=bool(combined),
            data=combined,
            metadata={
                "source_count": len(parts),
                "failed_count": len(failed_urls),
                "total_length": len(combined),
                "failed_urls": failed_urls,
            },
        )
