"""ContentFetcher — application interface for fetching external content.

The workflow depends on this interface, never on concrete infrastructure
implementations. Implementations live in the Content Infrastructure context
(e.g. HTTPXContentFetcher, PlaywrightContentFetcher).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from processing.domain.workflow.fetched_content import FetchedContent
from processing.domain.workflow.source import JobSource


class ContentFetcher(ABC):
    @abstractmethod
    def fetch(self, source: JobSource) -> FetchedContent:
        """Fetch a source and return its raw content.

        Implementations must return a FetchedContent result — a failed fetch
        must not raise; it is represented with success=False and an error.
        """
        ...
