"""Playwright-based ContentFetcher — fallback fetching implementation.

Renders JavaScript-heavy pages in a real browser. The playwright package is
optional: when it is not installed, fetch() returns a failed FetchedContent
so the composite fetcher can fall back to the primary implementation.
"""

from __future__ import annotations

from processing.application.ports.content_fetcher import ContentFetcher
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.source import JobSource


class PlaywrightContentFetcher(ContentFetcher):
    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout

    def fetch(self, source: JobSource) -> FetchedContent:
        url = source.url or ""
        if not source.is_fetchable:
            return FetchedContent(
                source=source,
                url=url,
                success=False,
                error=f"Invalid URL: {url}",
            )

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return FetchedContent(
                source=source,
                url=url,
                success=False,
                error="Playwright is not installed",
            )

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.goto(url, timeout=int(self._timeout * 1000), wait_until="domcontentloaded")
                    content = page.content()
                    title = page.title() or ""
                finally:
                    browser.close()

            return FetchedContent(
                source=source,
                url=url,
                success=True,
                content=content,
                content_type="html",
                metadata={"title": title},
            )
        except Exception as e:
            return FetchedContent(
                source=source,
                url=url,
                success=False,
                error=f"{type(e).__name__}: {e}",
            )
