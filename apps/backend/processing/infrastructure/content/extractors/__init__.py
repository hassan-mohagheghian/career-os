"""Extractors — Trafilatura primary, BeautifulSoup fallback, composite orchestration.

If no extractor produces clean text, it falls back to a best-effort
markup-stripped passthrough so that a valid but unusual source never blocks
context preparation on its own.
"""

from __future__ import annotations

import re

from processing.application.ports.content_extractor import ContentExtractor
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent

from processing.infrastructure.content.extractors.bs4_extractor import BeautifulSoupContentExtractor
from processing.infrastructure.content.extractors.trafilatura_extractor import TrafilaturaContentExtractor

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
            text = re.sub(r"<[^>]+>", " ", content.content)
            text = re.sub(r"\s+", " ", text).strip()
        return ExtractedContent(
            source=content.source,
            url=content.url,
            title=content.metadata.get("title", ""),
            clean_text=text,
            length=len(text),
            extraction_method="fallback",
            metadata={"extractor": "fallback"},
        )
