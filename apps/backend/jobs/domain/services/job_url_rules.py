"""Job URL duplicate rules.

Each job board gets its own rule for detecting that a posting URL refers to a
job that already exists in the system, even when the URL differs (tracking
parameters, subdomains, redirects). Rules are registered in
``JOB_URL_DUPLICATE_RULES`` and evaluated in order at job creation.

A rule returns a ``duplicate_fragment`` — a stable substring that any URL for
the same posting must contain — or ``None`` when the URL does not belong to
that board. Non-matching boards are skipped, so a job board with no rule yet is
never restricted.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

from jobs.domain.repositories.job_repository import IJobRepository


class JobUrlDuplicateRule(ABC):
    """Base class for a job-board URL duplicate rule."""

    name: str

    @abstractmethod
    def duplicate_fragment(self, url: str) -> str | None:
        """Return the URL fragment identifying the posting, or None if the
        rule does not apply to ``url``."""
        ...


class LinkedInJobUrlRule(JobUrlDuplicateRule):
    """LinkedIn job postings.

    The LinkedIn job id lives in the URL path: ``/jobs/view/{job_id}``. Query
    parameters (``trackingId``, ``refId``, ...) vary per visit but the path
    fragment is stable, so it is used as the duplicate key.
    """

    name = "linkedin"

    _JOB_PATH_RE = re.compile(r"/jobs/view/(?P<job_id>\d+)")

    def duplicate_fragment(self, url: str) -> str | None:
        job_id = self._extract_job_id(url)
        if job_id is None:
            return None
        return f"linkedin.com/jobs/view/{job_id}"

    @classmethod
    def _extract_job_id(cls, url: str) -> str | None:
        if not url:
            return None
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if "linkedin.com" not in host:
            return None
        match = cls._JOB_PATH_RE.search(parsed.path or "")
        return match.group("job_id") if match else None


JOB_URL_DUPLICATE_RULES: tuple[JobUrlDuplicateRule, ...] = (LinkedInJobUrlRule(),)


def find_duplicate_job(repo: IJobRepository, url: str) -> dict[str, Any] | None:
    """Return the first existing (non-deleted) job that duplicates ``url``.

    Rules that do not apply to ``url`` are skipped; a URL with no matching rule
    has no duplicate restriction.
    """
    for rule in JOB_URL_DUPLICATE_RULES:
        fragment = rule.duplicate_fragment(url)
        if fragment is None:
            continue
        existing = repo.get_by_url_fragment(fragment)
        if existing and not existing.get("deleted"):
            return existing
    return None
