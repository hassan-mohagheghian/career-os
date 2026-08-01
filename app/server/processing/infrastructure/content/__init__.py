"""Content Infrastructure — infrastructure adapters for fetching and
extracting external content.

These adapters must not leak into domain logic. The workflow depends on the
application interfaces (ContentFetcher / ContentExtractor), never on these
concrete implementations. Possible implementations can change in the future.
"""

from processing.infrastructure.content.fetchers import (
    CompositeContentFetcher,
    HTTPXContentFetcher,
    PlaywrightContentFetcher,
)
from processing.infrastructure.content.extractors import (
    BeautifulSoupContentExtractor,
    CompositeContentExtractor,
    TrafilaturaContentExtractor,
)

__all__ = [
    "CompositeContentFetcher",
    "HTTPXContentFetcher",
    "PlaywrightContentFetcher",
    "CompositeContentExtractor",
    "TrafilaturaContentExtractor",
    "BeautifulSoupContentExtractor",
]
