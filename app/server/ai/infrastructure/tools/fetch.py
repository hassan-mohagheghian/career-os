"""Unified web fetcher with local-first preprocessing pipeline.

Replaces all duplicated _fetch_url functions across the codebase.
Every URL goes through: HTTP → redirect → retry → encoding → HTML clean → extract → normalize.

Design: Single Responsibility — one place for all URL fetching.
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Optional

from shared.infrastructure.process.logging_config import get_logger
from .models import ContentExtraction, FetchError, FetchStatus, FetchedPage
log = get_logger("ai.tools.fetch")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

JOB_CONTENT_MARKERS = [
    "About The Role",
    "Job Description",
    "Description",
    "What you'll do",
    "What You'll Do",
    "The Role",
    "Responsibilities",
    "Requirements",
    "Qualifications",
]

MIN_CONTENT_LENGTH = 100
MAX_CONTENT_LENGTH = 5000
COMPANY_MAX_LENGTH = 8000


def fetch_page(
    url: str,
    *,
    timeout: int = 30,
    max_retries: int = 2,
    max_length: int = MAX_CONTENT_LENGTH,
    content_markers: Optional[list[str]] = None,
    strip_scripts: bool = True,
    extract_main: bool = True,
) -> FetchedPage:
    """Fetch a URL and return a structured, cleaned page.

    Pipeline: HTTP request → redirect handling → retry → encoding →
    HTML cleaning → main content extraction → text normalization.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        max_retries: Number of retry attempts on transient errors.
        max_length: Maximum text length to return.
        content_markers: Markers to find main content section.
        strip_scripts: Whether to remove script/style tags.
        extract_main: Whether to attempt main content extraction.

    Returns:
        FetchedPage with cleaned content and metadata.
    """
    if not url or not url.startswith(("http://", "https://")):
        return FetchedPage(
            url=url,
            status=FetchStatus.FAILED,
            error=FetchError(code="INVALID_URL", message="Invalid URL", url=url),
        )

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return _do_fetch(
                url,
                timeout=timeout,
                max_length=max_length,
                content_markers=content_markers or JOB_CONTENT_MARKERS,
                strip_scripts=strip_scripts,
                extract_main=extract_main,
            )
        except urllib.error.HTTPError as e:
            last_error = e
            code = e.code
            if code == 404:
                return FetchedPage(
                    url=url,
                    status=FetchStatus.FAILED,
                    status_code=404,
                    error=FetchError(
                        code="NOT_FOUND",
                        message=f"Page not found (404): {url}",
                        url=url,
                        retryable=False,
                    ),
                )
            if code == 403:
                return FetchedPage(
                    url=url,
                    status=FetchStatus.FAILED,
                    status_code=403,
                    error=FetchError(
                        code="ACCESS_DENIED",
                        message=f"Access denied (403): {url}",
                        url=url,
                        retryable=False,
                    ),
                )
            if code == 429:
                if attempt < max_retries:
                    time.sleep(2 ** attempt * 2)
                    continue
                return FetchedPage(
                    url=url,
                    status=FetchStatus.FAILED,
                    status_code=429,
                    error=FetchError(
                        code="RATE_LIMITED",
                        message=f"Rate limited (429): {url}",
                        url=url,
                        retryable=True,
                    ),
                )
            if code == 503:
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return FetchedPage(
                    url=url,
                    status=FetchStatus.FAILED,
                    status_code=503,
                    error=FetchError(
                        code="SERVICE_UNAVAILABLE",
                        message=f"Service unavailable (503): {url}",
                        url=url,
                        retryable=True,
                    ),
                )
            if 500 <= code < 600 and attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return FetchedPage(
                url=url,
                status=FetchStatus.FAILED,
                status_code=code,
                error=FetchError(
                    code=f"HTTP_{code}",
                    message=f"HTTP error {code}: {e.reason} — {url}",
                    url=url,
                    retryable=500 <= code < 600,
                ),
            )
        except urllib.error.URLError as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return FetchedPage(
                url=url,
                status=FetchStatus.FAILED,
                error=FetchError(
                    code="NETWORK_ERROR",
                    message=f"Network error: {e.reason} — {url}",
                    url=url,
                    retryable=True,
                ),
            )
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(1)
                continue
            return FetchedPage(
                url=url,
                status=FetchStatus.FAILED,
                error=FetchError(
                    code="FETCH_ERROR",
                    message=f"Failed to fetch: {e}",
                    url=url,
                    retryable=True,
                ),
            )

    return FetchedPage(
        url=url,
        status=FetchStatus.FAILED,
        error=FetchError(
            code="MAX_RETRIES",
            message=f"Max retries exceeded: {last_error}",
            url=url,
            retryable=False,
        ),
    )


def _do_fetch(
    url: str,
    *,
    timeout: int,
    max_length: int,
    content_markers: list[str],
    strip_scripts: bool,
    extract_main: bool,
) -> FetchedPage:
    """Internal fetch implementation — no retry logic."""
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status_code = resp.status
        final_url = resp.url
        raw_bytes = resp.read()

    html = raw_bytes.decode("utf-8", errors="replace")

    extraction = extract_content(
        html,
        strip_scripts=strip_scripts,
        extract_main=extract_main,
        content_markers=content_markers,
    )

    plain_text = extraction.main_content or extraction.cleaned_text

    if len(plain_text) < MIN_CONTENT_LENGTH:
        return FetchedPage(
            url=url,
            canonical_url=final_url if final_url != url else None,
            status=FetchStatus.FAILED,
            status_code=status_code,
            content_length=len(plain_text),
            error=FetchError(
                code="CONTENT_TOO_SHORT",
                message=f"Page content too short ({len(plain_text)} chars): {url}",
                url=url,
                retryable=False,
            ),
            plain_text=plain_text,
            metadata={"raw_html_length": len(html)},
        )

    truncated = plain_text[:max_length]

    return FetchedPage(
        url=url,
        canonical_url=final_url if final_url != url else None,
        status=FetchStatus.SUCCESS,
        status_code=status_code,
        plain_text=truncated,
        content_length=len(plain_text),
        language=extraction.language,
        metadata={
            "raw_html_length": len(html),
            "cleaned_length": len(extraction.cleaned_text),
            "extraction_method": extraction.extraction_method,
            "sections_count": len(extraction.sections),
        },
        fetched_at=datetime.now(),
    )


def extract_content(
    html: str,
    *,
    strip_scripts: bool = True,
    extract_main: bool = True,
    content_markers: Optional[list[str]] = None,
) -> ContentExtraction:
    """Extract and clean content from raw HTML.

    Pipeline: strip tags → normalize whitespace → find main section →
    return structured result.
    """
    cleaned = html

    if strip_scripts:
        cleaned = re.sub(r"<script[^>]*>.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)

    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"&[a-zA-Z]+;", " ", cleaned)
    cleaned = re.sub(r"&#\d+;", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    main_content = cleaned
    if extract_main and content_markers:
        for marker in content_markers:
            idx = cleaned.find(marker)
            if idx != -1:
                main_content = cleaned[idx:]
                break

    words = main_content.split()
    word_count = len(words)

    return ContentExtraction(
        raw_html=html[:1000],
        cleaned_text=cleaned,
        main_content=main_content,
        word_count=word_count,
        extraction_method="regex",
        language=_detect_language(main_content),
    )


def _detect_language(text: str) -> str:
    """Simple language detection based on common words."""
    if not text:
        return "en"
    lower = text.lower()
    english_words = ["the", "and", "is", "in", "to", "of", "for", "with", "on", "at"]
    german_words = ["der", "die", "und", "ist", "in", "den", "von", "zu", "das", "mit"]
    en_count = sum(1 for w in english_words if f" {w} " in f" {lower} ")
    de_count = sum(1 for w in german_words if f" {w} " in f" {lower} ")
    return "de" if de_count > en_count else "en"
