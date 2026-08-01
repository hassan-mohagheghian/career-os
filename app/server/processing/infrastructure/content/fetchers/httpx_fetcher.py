"""HTTPX-based ContentFetcher — primary fetching implementation.

Uses httpx to fetch external URLs. Returns a FetchedContent result for both
success and failure; individual failures never raise.
"""

from __future__ import annotations

import httpx

from processing.application.ports.content_fetcher import ContentFetcher
from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.source import JobSource

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class HTTPXContentFetcher(ContentFetcher):
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
            with httpx.Client(
                follow_redirects=True,
                timeout=self._timeout,
                headers=DEFAULT_HEADERS,
            ) as client:
                response = client.get(url)

            content_type = (response.headers.get("content-type") or "").lower()
            is_html = "html" in content_type

            return FetchedContent(
                source=source,
                url=str(response.url),
                success=response.is_success,
                content=response.text,
                content_type="html" if is_html else "text",
                status_code=response.status_code,
                error=None if response.is_success else f"HTTP {response.status_code}",
                metadata={"content_type": content_type},
            )
        except httpx.HTTPError as e:
            return FetchedContent(
                source=source,
                url=url,
                success=False,
                error=f"{type(e).__name__}: {e}",
            )
