"""Trafilatura-based ContentExtractor — primary extraction implementation.

Extracts clean article text from HTML. The trafilatura package is optional;
when it is not installed, extract() raises so the composite extractor can
fall back to the BeautifulSoup implementation.
"""

from __future__ import annotations

from processing.application.ports.content_extractor import ContentExtractor
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent


class TrafilaturaContentExtractor(ContentExtractor):
    def extract(self, content: FetchedContent) -> ExtractedContent:
        if content.content_type == "text" or not content.content.strip():
            return self._passthrough(content)

        try:
            import trafilatura
        except ImportError:
            raise ImportError("trafilatura is not installed")

        text = trafilatura.extract(
            content.content,
            include_comments=False,
            include_tables=True,
            include_links=False,
        )
        text = (text or "").strip()

        return ExtractedContent(
            source=content.source,
            url=content.url,
            title=content.metadata.get("title", ""),
            clean_text=text,
            length=len(text),
            extraction_method="trafilatura",
            metadata={"extractor": "trafilatura"},
        )

    @staticmethod
    def _passthrough(content: FetchedContent) -> ExtractedContent:
        text = content.content.strip()
        return ExtractedContent(
            source=content.source,
            url=content.url,
            title=content.metadata.get("title", ""),
            clean_text=text,
            length=len(text),
            extraction_method="passthrough",
            metadata={"extractor": "passthrough"},
        )
