"""ContentExtractor — application interface for converting fetched content
into clean text.

The workflow depends on this interface, never on concrete infrastructure
implementations. Implementations live in the Content Infrastructure context
(e.g. TrafilaturaContentExtractor, BeautifulSoupContentExtractor).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from processing.domain.workflow.extracted_content import ExtractedContent
from processing.domain.workflow.fetched_content import FetchedContent


class ContentExtractor(ABC):
    @abstractmethod
    def extract(self, content: FetchedContent) -> ExtractedContent:
        """Convert fetched content into clean, structured text."""
        ...
