"""BeautifulSoup-based ContentExtractor — fallback extraction implementation.

Uses BeautifulSoup to strip markup and return clean text. The
beautifulsoup4 package is optional; when it is not installed, extract()
raises so the composite extractor can fall back to the raw passthrough.
"""

from __future__ import annotations

import re

from processing.application.ports.content_extractor import ContentExtractor
from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent


class BeautifulSoupContentExtractor(ContentExtractor):
    def extract(self, content: FetchedContent) -> ExtractedContent:
        if content.content_type == "text" or not content.content.strip():
            return self._passthrough(content)

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is not installed")

        soup = BeautifulSoup(content.content, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        text = soup.get_text(separator="\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return ExtractedContent(
            source=content.source,
            url=content.url,
            title=title,
            clean_text=text,
            length=len(text),
            extraction_method="beautifulsoup",
            metadata={"extractor": "beautifulsoup"},
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
