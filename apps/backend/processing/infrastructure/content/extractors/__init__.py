"""Extractors — Trafilatura primary, BeautifulSoup fallback, composite orchestration.

If no extractor produces clean text, it falls back to a best-effort
markup-stripped passthrough so that a valid but unusual source never blocks
context preparation on its own. The fallback removes non-content element
bodies (script/style/head/nav/iframe/template) so inline JS and RSC payloads
never leak into the LLM context, and it caps the resulting text length so a
single broken page cannot bloat the prompt.
"""

from __future__ import annotations

import re

from processing.application.ports.content_extractor import ContentExtractor
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent

from processing.infrastructure.content.extractors.bs4_extractor import BeautifulSoupContentExtractor
from processing.infrastructure.content.extractors.trafilatura_extractor import TrafilaturaContentExtractor

MAX_FALLBACK_CHARS = 40_000

_NON_CONTENT_ELEMENTS = re.compile(
    r"<\s*(script|style|noscript|head|iframe|template|svg|math)\b[^>]*>.*?<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_SELF_CLOSING_NON_CONTENT = re.compile(
    r"<\s*(script|style|head|iframe|template)\b[^>]*/>",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")

__all__ = [
    "CompositeContentExtractor",
    "TrafilaturaContentExtractor",
    "BeautifulSoupContentExtractor",
]


class CompositeContentExtractor(ContentExtractor):
    def __init__(self, extractors: list[ContentExtractor]):
        self._extractors = extractors

    def extract(self, content: FetchedContent) -> ExtractedContent:
        last: ExtractedContent | None = None
        for extractor in self._extractors:
            try:
                result = extractor.extract(content)
            except Exception:
                continue
            if result.clean_text.strip():
                return result
            last = result
        if last is not None and last.clean_text:
            return last
        return self._fallback(content)

    @staticmethod
    def _fallback(content: FetchedContent) -> ExtractedContent:
        if content.content_type == "text":
            text = content.content.strip()
        else:
            text = content.content
            text = _NON_CONTENT_ELEMENTS.sub(" ", text)
            text = _SELF_CLOSING_NON_CONTENT.sub(" ", text)
            text = _TAG_RE.sub(" ", text)
            text = re.sub(r"\s+", " ", text).strip()
            text = text[:MAX_FALLBACK_CHARS]
        return ExtractedContent(
            source=content.source,
            url=content.url,
            title=content.metadata.get("title", ""),
            clean_text=text,
            length=len(text),
            extraction_method="fallback",
            metadata={"extractor": "fallback"},
        )
