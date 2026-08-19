"""Placeholder entity and placeholder-key catalog.

A placeholder is a named, user-supplied value (``{{token}}``) injected into
generated documents. The Placeholders context owns these values so the job
application workspace (a different bounded context) can substitute them without
a cross-context FK (AGENTS.md rule 15).
"""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any


class PlaceholderKey:
    """Canonical placeholder tokens supported by generated documents.

    These keys are surfaced to the user on the Placeholders page; generated
    resumes / cover letters reference them with ``{{key}}`` syntax.
    """

    NAME = "name"
    TITLE = "title"
    EMAIL = "email"
    PHONE = "phone"
    LOCATION = "location"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    HEADLINE = "headline"
    SUMMARY = "summary"

    ALL: tuple[str, ...] = (
        NAME,
        TITLE,
        EMAIL,
        PHONE,
        LOCATION,
        LINKEDIN,
        GITHUB,
        HEADLINE,
        SUMMARY,
    )

    # Human labels shown on the Placeholders page.
    LABELS: dict[str, str] = {
        NAME: "Full name",
        TITLE: "Professional title",
        EMAIL: "Email",
        PHONE: "Phone",
        LOCATION: "Location",
        LINKEDIN: "LinkedIn URL",
        GITHUB: "GitHub URL",
        HEADLINE: "Headline",
        SUMMARY: "Professional summary",
    }


class Placeholder:
    """A single named placeholder value."""

    def __init__(
        self,
        key: str,
        value: str = "",
        updated_at: str | None = None,
    ):
        self.key = key
        self.value = value or ""
        self.updated_at = updated_at or datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "value": self.value, "updated_at": self.updated_at}


def fill_placeholders(content: str, values: dict[str, str]) -> str:
    """Replace every ``{{key}}`` token with its value from ``values``.

    Unknown tokens (not present in ``values``) are left untouched so a partially
    configured set never corrupts the document. Tokens are ``{{key}}`` — the key
    is case-insensitive and whitespace-trimmed.
    """
    import re

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip().lower()
        if key in values:
            return values[key]
        return match.group(0)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", _replace, content)


__all__ = ["Placeholder", "PlaceholderKey", "fill_placeholders"]