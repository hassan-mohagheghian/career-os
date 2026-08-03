"""Fetchers — HTTPX primary, Playwright fallback, composite orchestration."""

from __future__ import annotations

from processing.application.ports.content_fetcher import ContentFetcher
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.source import JobSource

from processing.infrastructure.content.fetchers.httpx_fetcher import HTTPXContentFetcher
from processing.infrastructure.content.fetchers.playwright_fetcher import PlaywrightContentFetcher

__all__ = [
    "CompositeContentFetcher",
    "HTTPXContentFetcher",
    "PlaywrightContentFetcher",
]


class CompositeContentFetcher(ContentFetcher):
    def __init__(self, fetchers: list[ContentFetcher]):
        self._fetchers = fetchers

    def fetch(self, source: JobSource) -> FetchedContent:
        last_real: FetchedContent | None = None
        last_degraded: FetchedContent | None = None
        for fetcher in self._fetchers:
            try:
                result = fetcher.fetch(source)
            except Exception as e:
                result = FetchedContent(
                    source=source,
                    url=source.url or "",
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                )
            if result.success:
                result.metadata["fetcher"] = fetcher.__class__.__name__
                return result
            if result.metadata.get("degraded"):
                last_degraded = result
            else:
                last_real = result
        return last_real if last_real is not None else last_degraded if last_degraded is not None else FetchedContent(
            source=source,
            url=source.url or "",
            success=False,
            error="No fetcher available",
        )
