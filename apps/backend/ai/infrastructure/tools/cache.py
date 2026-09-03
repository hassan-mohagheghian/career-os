"""Caching layer for the AI Tool Layer.

Provides URL and content caching to avoid redundant network requests.
Supports file-based caching (default) with optional Redis backend.

Design: Strategy Pattern — swap cache backends without changing callers.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.config.app_config import CACHE_TTL_SECONDS, CACHE_DIR
from .models import FetchedPage, FetchStatus
log = get_logger("ai.tools.cache")

DEFAULT_TTL_SECONDS = CACHE_TTL_SECONDS
DEFAULT_CACHE_DIR = CACHE_DIR


class ContentCache:
    """File-based content cache with configurable TTL.

    Cache key = SHA256 of URL.
    Stored as JSON files in cache_dir.
    """

    def __init__(
        self,
        cache_dir: str = DEFAULT_CACHE_DIR,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, url: str) -> Optional[FetchedPage]:
        """Retrieve a cached page if it exists and is not expired."""
        key = self._key(url)
        path = self.cache_dir / f"{key}.json"

        if not path.exists():
            self._stats["misses"] += 1
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = data.get("cached_at", 0)
            if time.time() - cached_at > self.ttl_seconds:
                self._stats["evictions"] += 1
                try:
                    path.unlink()
                except OSError:
                    pass
                return None

            page = FetchedPage(**data.get("page", {}))
            page.status = FetchStatus.CACHED
            page.cache_hit = True
            self._stats["hits"] += 1
            log.debug("cache.hit", url=url[:80])
            return page
        except Exception as e:
            log.warning("cache.read_error", url=url[:80], error=str(e))
            self._stats["misses"] += 1
            return None

    def set(self, url: str, page: FetchedPage) -> None:
        """Store a page in the cache."""
        key = self._key(url)
        path = self.cache_dir / f"{key}.json"

        try:
            data = {
                "url": url,
                "cached_at": time.time(),
                "page": page.model_dump(mode="json"),
            }
            path.write_text(json.dumps(data, default=str), encoding="utf-8")
            log.debug("cache.set", url=url[:80])
        except Exception as e:
            log.warning("cache.write_error", url=url[:80], error=str(e))

    def invalidate(self, url: str) -> bool:
        """Remove a cached entry for the given URL."""
        key = self._key(url)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                path.unlink()
                return True
            except OSError:
                pass
        return False

    def clear(self) -> int:
        """Remove all cached entries. Returns count of removed files."""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        return count

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    def _key(self, url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:32]


_global_cache: Optional[ContentCache] = None


def get_content_cache(
    cache_dir: str = DEFAULT_CACHE_DIR,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> ContentCache:
    """Get or create the global content cache singleton."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ContentCache(cache_dir=cache_dir, ttl_seconds=ttl_seconds)
    return _global_cache


def reset_content_cache() -> None:
    """Reset the global cache (for testing)."""
    global _global_cache
    _global_cache = None
